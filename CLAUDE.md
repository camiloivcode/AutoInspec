# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this actually is

AutoInspec's live product is a **vehicle inspection photo → PDF report generator**: a user uploads a batch of photos, a CLIP-embedding classifier auto-assigns each photo to one of 11 fixed inspection positions (frontal, side views, driver, spare tire kit, SOAT/documents, etc.), OCR suggests the license plate, the user reviews/corrects the assignment, and the backend renders a PDF report. The corrections are persisted as training data (see the feedback loop below).

The repo used to also contain a full Clean Architecture CRUD scaffold (vehicles/inspections/templates/users/documents, Postgres, a Redis-backed bot) from an earlier, broader "inspection management system" iteration. Nothing in the frontend ever called it — the frontend only ever routed two pages (`GenerarPDF` at `/` and `History` at `/history` — see `frontend/src/App.tsx`) — so that scaffold was removed entirely (domain/application/infrastructure-database/infrastructure-storage layers, the five CRUD routes, `dependencies.py`, `word_generator.py`/`pdf_generator.py`, and the whole `bot/` service). The backend is now just `generate.py` + `history.py` + `health.py` on top of the classifier pipeline below; `docker-compose.yml` runs only `backend` and `frontend`, no Postgres/Redis.

## Commands

**Docker (all services):**
```bash
cp .env.example .env
docker compose up --build
```
Frontend → http://localhost, backend → http://localhost:8000 (`/docs` for Swagger, `/health` for healthcheck).

**Backend, local dev:**
```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```
Native deps required for the analysis/OCR/PDF pipeline outside Docker: `tesseract-ocr` (+ `tesseract-ocr-spa` language pack) and LibreOffice (`libreoffice-writer`) for doc conversion — see `backend/Dockerfile` for the exact apt packages.

**Frontend:**
```bash
cd frontend
npm install
npm run dev      # vite dev server :5173, proxies /api -> http://backend:8000
npm run build     # tsc -b && vite build
npm run lint       # eslint . (flat config in eslint.config.js)
```

**Tests:** There is no configured test runner. `backend/tests/` is empty. `backend/eval/evaluate.py` is the classifier accuracy tool (not pytest) — it groups `fotos_prueba/` images into approximate photo sessions by filename timestamp (`eval/grouping.py`) before evaluating, so near-duplicate consecutive shots can't leak across a train/holdout boundary, and writes a dated JSON report + confusion matrix to `backend/eval/results/`. It needs `cv2`/`pytesseract` (native Tesseract binary) plus the ONNX model, so run it inside the **`backend/Dockerfile.eval`** image (same base as production plus scikit-learn, which `eval/train_head.py` needs and `requirements.txt` deliberately omits since runtime inference is numpy-only):

```bash
docker build -t autoinspec-backend-eval-ml -f backend/Dockerfile.eval backend/
cd backend && docker run --rm -v "$(pwd):/app" autoinspec-backend-eval-ml \
    python -u -m eval.evaluate --dataset /app/fotos_prueba --mode both --classifier heuristic
```

Same image runs `python -m eval.train_head --dataset /app/fotos_prueba` to regenerate `position_head.json`. **From Git Bash on Windows, prefix with `MSYS_NO_PATHCONV=1`** or `/app/...` gets rewritten to a Windows path and the container sees nothing.

Pass `--no-ocr` (or `-e SKIP_OCR_DETECTION=1`) to skip the Tesseract text-density pass. Runs take substantially longer with OCR on, and under `--mode batch` most OCR calls hit their 10s timeout — see the concurrency note under Conventions. Accuracy is *better* with OCR enabled, so the numbers below quote both.

There's no lint/typecheck configured for Python; frontend type-checks via `tsc -b` as part of `npm run build` and lints via ESLint 9 flat config (`frontend/eslint.config.js`).

## Architecture

### The classifier pipeline (the part that matters)

- `backend/src/infrastructure/analysis/reference_matcher.py` — `extract_features()`: returns three normalized-image features (`brightness`, `brightness_median`, `white_ratio`) consumed only by the OCR override's brightness/white-ratio gate in `_detect_document_override`. Used to compute 19 hand-engineered features (HSV saturation/hue, blue/green ratios, Laplacian variance, sky-blue ratio, etc.) for the old threshold cascade; trimmed to what's actually read once the CLIP embedding classifier (see below) replaced that cascade. `photo_classifier.classify()` only calls it once the OCR text-density gate already passed (`_DOC_TEXT_REGIONS_MIN`/`_DOC_TEXT_LENGTH_MIN`), since `_detect_document_override` rejects anything below that same floor anyway — running the white-balance/CLAHE pass for the ~90% of photos that never clear the gate would be wasted work.
- `backend/src/infrastructure/analysis/embedding_classifier.py` — `EmbeddingPositionClassifier`, the primary classifier as of 2026-08-06. Embeds a photo with a CLIP ViT-B/32 vision encoder (ONNX, dynamic-quantized, ~85MB, downloaded at Docker build time from HuggingFace — see `Dockerfile`, not committed to the repo) and scores it against an 11x512 logistic regression head (`position_head.json`, **committed**, trained offline by `eval/train_head.py` on the 81 tuning photos + on-the-fly augmentation — brightness/contrast/saturation jitter, ±5° rotation, 90-100% crop, JPEG noise; **never horizontal flip**, since positions 4/5 and 3/7 are mirror-image pairs and a flipped photo would carry the wrong label). Inference is numpy-only (`softmax(W @ embedding + b)`); scikit-learn is a training-only dependency, not in `requirements.txt`. Also exports `confidence_from_prob()`, the shared probability→`"high"/"medium"/"low"` bucketing used by both this module and `photo_classifier.py`.
- `backend/src/infrastructure/analysis/photo_classifier.py` — `PhotoClassifier.classify()` calls the embedding classifier above for the general case, with one independent-signal override that wins when it fires: strong OCR text density (Tesseract, `_detect_document_override`, position 1). Everything the old cascade used to do — Hough circles for wheels, HSV red-mask for kit items, sky-blue ratio, headlight/taillight color detection, horizontal symmetry, Hough lines for side profiles — is gone; those hand-tuned absolute thresholds measured at **4.94% accuracy** on a session-held-out split (`backend/eval/results/`, see also `backend/eval/evaluate.py` under Tests) before being replaced. A Haar cascade face-detection override for position 8 (Conductor) was tried and removed (2026-08-12): a caching bug (`_detect_text_density` populated the shared image cache but never the `shape` the face override read from it, so `h, w` silently defaulted to `(0, 0)` and the size gate always failed) meant it never actually fired in production. Measured for real after fixing that bug, it was net-negative — position 8 was already 100% accurate from the embedding alone, and the cascade's false positives on non-driver photos cost 2 correct classifications elsewhere for zero gain — so it was deleted rather than shipped as a broken-but-measured feature.
- `classify_batch()` parallelizes per-image classification with a `ThreadPoolExecutor`, then resolves position collisions with a **deterministic global assignment**: every (photo, position, probability) pair from the embedding's full 11-class distribution becomes a candidate (the OCR override contributes its single winning position at probability 1.0), all candidates are sorted descending, and slots are claimed greedily respecting `MAX_PER_POSITION` (position 10 allows 2, matching `generate.py`'s manual-assignment cap — both import the same constant). This replaced a hardcoded `COLLISION_ALLOW_LIST` adjacency map plus feature-centroid similarity scoring, which measured 66.67% with 16% of photos unassigned. Batch coverage sits around 86%, and the gap is structural rather than algorithmic: `MAX_PER_POSITION` offers 12 slots per session while the eval dataset averages 13.5 photos per session, so surplus photos have nowhere to go by design — don't chase it as an assignment bug.
- `INSPECTION_POSITIONS` (dict of 11 fixed positions, defined in `photo_classifier.py`) is the canonical position list. It's duplicated as the `POSITIONS` array in `frontend/src/pages/GenerarPDF/positions.ts` — **keep both in sync** if positions ever change. That file also holds frontend-only presentation data derived from the same 11 positions: `SHORT_LABELS` (compact labels for the select trigger and the map legend), `SPATIAL_NODES` (x/y percentages for the six angular positions on the vehicle diagram) and `NON_SPATIAL` (the five positions — documents, driver, road kit, jack — that have no meaningful place on a vehicle outline).
- `backend/src/infrastructure/ocr/plate_detector.py` — plate OCR/regex extraction, run in parallel with classification via `asyncio.gather` in the `/api/auto-analyze` route.
- `backend/fotos_prueba/` (81 images across the 11 position folders) is the only tuning/eval dataset — a source labeled by subfolder name, not a runtime asset. `backend/.dockerignore` keeps it out of the production image; mount it as a volume for `eval/evaluate.py` or `eval/train_head.py`.

### Accuracy

Measured on the 81-photo tuning set (`eval/evaluate.py`, session-held-out grouping):

| | classify | batch |
|---|---|---|
| Old hand-tuned cascade | 4.94% | — |
| Embeddings, OCR disabled | 88.89% | ~80% |
| Embeddings, OCR enabled | **91.36%** | **82.72%** |

These are **in-sample** — the logistic head was trained on these same 81 photos. The honest generalization number is the **75.31%** leave-one-session-out CV reported by `eval/train_head.py`; quote that one when the question is "how well does this work on new photos". Batch results move ~1 point between identical runs (float32 reductions in concurrent ONNX inference aren't bit-reproducible), so treat small deltas as noise rather than regression. Every run's full report lands in `backend/eval/results/` and those JSONs are committed as the historical record.

### The feedback loop

`backend/src/infrastructure/feedback/feedback_store.py` — every generation session produces 11 human-verified labels (the user reviews and corrects each auto-suggested position), so `record_batch()` copies the images to `/data/feedback/<session_id>/` and appends one JSONL line per photo to `/data/feedback/labels.jsonl` with `(suggested_position, corrected_position, confidence, method)`. This happens **before** `generate.py`'s `finally` block deletes the request's temp dir — order matters, the photos are gone after it.

JSONL append-only is deliberate: unlike `history.json` (which rewrites the whole file, see below), a single-line append is safe under concurrent writers.

This is the only accuracy signal not contaminated by the 81 tuning photos the head was trained on. Once enough corrections accumulate, they're the retraining set for `eval/train_head.py`. `/data/feedback/` holds real vehicle photos — it's gitignored and must stay that way.

### API surface actually in use

`backend/src/api/routes/generate.py` (prefix `/api`):
- `POST /generate-pdf` — manual position assignment, images + positions arrays must match 1:1.
- `POST /auto-analyze` — runs classifier + plate detector over uploaded images, returns per-image suggested position/confidence for the frontend's review step.
- `POST /generate-pdf/auto` — same generation path as `/generate-pdf` (kept as a separate endpoint for the auto-assisted flow).

`/generate-pdf` and `/generate-pdf/auto` share three module-level helpers rather than duplicating the same ~85 lines: `_validate_generation_request()` (required fields, 1:1 image/position count, `MAX_PER_POSITION` caps), `_save_uploads()` (writes to `work_dir` with the `{pos}_{n}{ext}` naming), and `_render_and_respond()` (calls `InspectionPDFGenerator`, saves the history record, returns the `FileResponse`). In the `/auto` path, `record_batch()` (the feedback loop) runs between `_save_uploads()` and `_render_and_respond()` — it must stay there, since it needs the saved photo paths and must complete **before** the route's `finally` block deletes `work_dir`.

All three write uploads to a per-request `work_dir` under `/data/uploads/temp/<session_id>` and delete it in a `finally` block. Generated files land in `/data/output` (`OUTPUT_DIR`), rendered by `infrastructure/document_generation/inspection_generator.py`.

`backend/src/api/routes/history.py` — a flat JSON file (`/data/output/history.json`) tracking generated reports (driver, plate, filename, size, timestamp). No database involved; list/download/delete endpoints read/write the same file directly (not safe under concurrent writers, but the frontend doesn't currently write concurrently).

### Frontend

Vite + React 18 + TypeScript + TailwindCSS. Two pages (`GenerarPDF`, `History`) lazy-loaded in `App.tsx`, inside a `Layout` shell (fixed rail ≥`md`, `BottomNav` below it). Nothing under `src/` talks to a CRUD backend — the deleted CRUD-era pages, `services/api.ts` and `types/index.ts`, were removed from the frontend in `6aa69d2`, and the backend routes they would have called are gone too.

- **`src/components/ui/`** is a design-system primitive layer (`Button`, `Card`, `Field`, `Select`, `Badge`, `Modal`, `Skeleton`, `EmptyState`, `Spinner`). **Build new UI on these rather than raw Tailwind**; if a variant is missing, add it to the primitive. Sizes are props with their own class maps, never `className` overrides — `clsx` doesn't dedupe conflicting Tailwind utilities, so a passed `px-2.5` loses to the component's own `px-4` (this was a real bug in `PhotoCard`'s select). The visual rules behind all of this are in **`frontend/DESIGN.md`** — read it before changing colors, radii or type.
- **`src/pages/GenerarPDF/`** is a directory, not a file: `index.tsx` orchestrates, `steps/` holds one component per wizard step (`StepUpload`, `StepAnalyzing`, `StepReview`, `StepDone`), `components/` holds `DropZone`/`PhotoCard`/`PositionMap`/`StepIndicator`, and the state lives in two hooks — `useGenerationFlow.ts` (step machine, `/auto-analyze` fetch, the `/generate-pdf/auto` XHR with real upload progress) and `useImageQueue.ts` (add/remove/compress, object-URL lifecycle). Images are compressed client-side before upload via `utils/imageCompressor.ts`.
- **`PositionMap.tsx`** renders a top-down vehicle diagram and is a second way to assign positions: the six angular positions are number dots on the body, and every position gets a labelled chip below that opens a popover to attach an unassigned photo. The per-photo `Select` in `PhotoCard` remains the equivalent keyboard path — the map adds a way to work, it doesn't replace one.
- **Folder upload uses a `webkitdirectory` file input**, not `showDirectoryPicker`. The latter is Chromium-only *and* requires a secure context, so it silently failed over plain HTTP on a LAN — the actual field scenario. The button is hidden entirely where `webkitdirectory` is unsupported (iOS Safari).
- There is **no drag-to-reorder**. It existed once but `handleGenerate` sorts by `assignedPosition` before submitting, so the manual order was always discarded; it was removed rather than made meaningful.

### Docker / infra

`docker-compose.yml` runs two services on a shared `vehicular-network`: `backend` and `frontend` (nginx serving the Vite build, proxying `/api` to `backend:8000`), both with memory/CPU limits and healthchecks. No database, no queue — state lives on the filesystem under `/data/` (uploads, output, feedback), backed by the `uploads_data`/`output_data` named volumes.

Each of `backend/` and `frontend/` has its own `.dockerignore` (Docker doesn't read a root-level one when the build context is a subdirectory). `backend/.dockerignore` keeps `fotos_prueba/` and `eval/results/` out of the production image; `frontend/.dockerignore` keeps `node_modules/` out of the build context so the image's own `npm install` output isn't clobbered by `COPY . .`.

## Conventions

- Code (identifiers, comments) in English; user-facing strings and API error messages in Spanish (`HTTPException(detail=...)` messages are Spanish throughout `generate.py`).
- IDs are UUID strings (`str(uuid4())`); timestamps are ISO 8601 UTC.
- Async throughout: FastAPI async/await on the backend. CPU-bound work (OpenCV classification, OCR) is pushed into `ThreadPoolExecutor`s rather than blocking the event loop — follow that pattern for new CPU-heavy analysis code.
- **Tesseract does not survive high concurrency.** `classify_batch` fans out to 8 threads, and Tesseract subprocesses starve each other badly under that load — on the 81-photo eval set, essentially every OCR call hits its timeout, versus 1 of 81 when run sequentially. Mitigations in place: `timeout=10` on `pytesseract.image_to_data` (a hung Tesseract can no longer block a whole request — the photo just loses its OCR override and falls back to the embedding, which covers those positions well on its own) and a module-level `threading.Semaphore(2)` capping concurrent Tesseract processes. Neither fully fixes throughput; the root cause is CPU capacity, not application logic (capping ONNX to single-threaded inference was tried and reverted — 2.8x slower with no fewer timeouts). Real batches are 11-13 photos, not 81, so practical impact is smaller than the stress test suggests. **Don't add more per-photo subprocess work to this path without measuring.**
- No authentication implemented anywhere; every endpoint is open.
