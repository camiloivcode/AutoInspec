# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this actually is

AutoInspec's live product is a **vehicle inspection photo → PDF report generator**: a user uploads a batch of photos, a CLIP-embedding classifier auto-assigns each photo to one of 11 fixed inspection positions (frontal, side views, driver, spare tire kit, SOAT/documents, etc.), OCR suggests the license plate, the user reviews/corrects the assignment, and the backend renders a PDF report. The corrections are persisted as training data (see the feedback loop below).

The repo also contains a full Clean Architecture CRUD scaffold (vehicles/inspections/templates/users/documents, Postgres, a Redis-backed bot) from an earlier, broader "inspection management system" iteration. That scaffold still runs (routes are registered, docker-compose still starts postgres/redis/bot) but **the current frontend only routes two pages** (`GenerarPDF` at `/` and `History` at `/history` — see `frontend/src/App.tsx`), so the CRUD stack is effectively dead weight from the UI's perspective. Don't assume features described by the CRUD layer are reachable from the app; check `App.tsx` and `backend/src/api/routes/generate.py` / `history.py` for what's actually wired up.

## Commands

**Docker (all services):**
```bash
cp .env.example .env
docker compose up --build
```
Frontend → http://localhost, backend → http://localhost:8000 (`/docs` for Swagger, `/health` for healthcheck).

**Backend, local dev** (needs Postgres reachable, though DB failures at startup are only logged as a warning — `create_tables()` failure doesn't crash the app, see `backend/src/main.py`):
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
npm run lint       # eslint .
```

**Bot:**
```bash
cd bot
pip install -r requirements.txt
python -m src.main
```
Needs `BOT_API_BASE_URL` (backend) and `BOT_REDIS_URL` (redis) reachable.

**Tests:** There is no configured test runner. `backend/tests/` is empty. `backend/eval/evaluate.py` is the classifier accuracy tool (not pytest) — it groups `fotos_prueba/` images into approximate photo sessions by filename timestamp (`eval/grouping.py`) before evaluating, so near-duplicate consecutive shots can't leak across a train/holdout boundary, and writes a dated JSON report + confusion matrix to `backend/eval/results/`. It needs `cv2`/`pytesseract` (native Tesseract binary) plus the ONNX model, so run it inside the **`backend/Dockerfile.eval`** image (same base as production plus scikit-learn, which `eval/train_head.py` needs and `requirements.txt` deliberately omits since runtime inference is numpy-only):

```bash
docker build -t autoinspec-backend-eval-ml -f backend/Dockerfile.eval backend/
cd backend && docker run --rm -v "$(pwd):/app" autoinspec-backend-eval-ml \
    python -u -m eval.evaluate --dataset /app/fotos_prueba --mode both --classifier heuristic
```

Same image runs `python -m eval.train_head --dataset /app/fotos_prueba` to regenerate `position_head.json`. **From Git Bash on Windows, prefix with `MSYS_NO_PATHCONV=1`** or `/app/...` gets rewritten to a Windows path and the container sees nothing.

Pass `--no-ocr` (or `-e SKIP_OCR_DETECTION=1`) to skip the Tesseract text-density pass. Runs take substantially longer with OCR on, and under `--mode batch` most OCR calls hit their 10s timeout — see the concurrency note under Conventions. Accuracy is *better* with OCR enabled, so the numbers below quote both.

There's no lint/typecheck configured for Python; frontend type-checks via `tsc -b` as part of `npm run build`.

## Architecture

### The classifier pipeline (the part that matters)

- `backend/src/infrastructure/analysis/reference_matcher.py` — `extract_features()`: returns three normalized-image features (`brightness`, `brightness_median`, `white_ratio`) consumed only by the OCR override's brightness/white-ratio gate in `_detect_document_override`. Used to compute 19 hand-engineered features (HSV saturation/hue, blue/green ratios, Laplacian variance, sky-blue ratio, etc.) for the old threshold cascade; trimmed to what's actually read once the CLIP embedding classifier (see below) replaced that cascade.
- `backend/src/infrastructure/analysis/embedding_classifier.py` — `EmbeddingPositionClassifier`, the primary classifier as of 2026-08-06. Embeds a photo with a CLIP ViT-B/32 vision encoder (ONNX, dynamic-quantized, ~85MB, downloaded at Docker build time from HuggingFace — see `Dockerfile`, not committed to the repo) and scores it against an 11x512 logistic regression head (`position_head.json`, **committed**, trained offline by `eval/train_head.py` on the 81 tuning photos + on-the-fly augmentation — brightness/contrast/saturation jitter, ±5° rotation, 90-100% crop, JPEG noise; **never horizontal flip**, since positions 4/5 and 3/7 are mirror-image pairs and a flipped photo would carry the wrong label). Inference is numpy-only (`softmax(W @ embedding + b)`); scikit-learn is a training-only dependency, not in `requirements.txt`.
- `backend/src/infrastructure/analysis/photo_classifier.py` — `PhotoClassifier.classify()` calls the embedding classifier above for the general case, with two independent-signal overrides that win when they fire: strong OCR text density (Tesseract, `_detect_document_override`, positions 1/11) and Haar cascade face detection (`cv2.data.haarcascades`, position 8/Conductor). Everything the old cascade used to do — Hough circles for wheels, HSV red-mask for kit items, sky-blue ratio, headlight/taillight color detection, horizontal symmetry, Hough lines for side profiles — is gone; those hand-tuned absolute thresholds measured at **4.94% accuracy** on a session-held-out split (`backend/eval/results/`, see also `backend/eval/evaluate.py` under Tests) before being replaced. The face override is deliberately strict (`minNeighbors=9`, `min_size` proportional to the image rather than absolute pixels, single attempt): at OpenCV's defaults the cascade fired on 36 of 81 photos when only 7 are drivers — "faces" in wheels and seat texture — dragging accuracy down to 59%.
- `classify_batch()` parallelizes per-image classification with a `ThreadPoolExecutor`, then resolves position collisions with a **deterministic global assignment**: every (photo, position, probability) pair from the embedding's full 11-class distribution becomes a candidate (OCR/face overrides contribute their single winning position at probability 1.0), all candidates are sorted descending, and slots are claimed greedily respecting `MAX_PER_POSITION` (position 10 allows 2, matching `generate.py`'s manual-assignment cap — both import the same constant). This replaced a hardcoded `COLLISION_ALLOW_LIST` adjacency map plus feature-centroid similarity scoring, which measured 66.67% with 16% of photos unassigned. Batch coverage sits around 86%, and the gap is structural rather than algorithmic: `MAX_PER_POSITION` offers 12 slots per session while the eval dataset averages 13.5 photos per session, so surplus photos have nowhere to go by design — don't chase it as an assignment bug.
- `INSPECTION_POSITIONS` (dict of 11 fixed positions, defined in `photo_classifier.py`) is the canonical position list. It's duplicated as the `POSITIONS` array in `frontend/src/pages/GenerarPDF.tsx` — **keep both in sync** if positions ever change.
- `backend/src/infrastructure/ocr/plate_detector.py` — plate OCR/regex extraction, run in parallel with classification via `asyncio.gather` in the `/api/auto-analyze` route.
- `backend/fotos_prueba/` (repo root and under `backend/`, 81 images across the 11 position folders) is the only tuning/eval dataset — it is a source labeled by subfolder name, not a runtime asset, and is **not** baked into the backend image (mount it as a volume for `eval/evaluate.py` or `eval/train_head.py`).

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

All three write uploads to a per-request `work_dir` under `/data/uploads/temp/<session_id>` and delete it in a `finally` block. Generated files land in `/data/output` (`OUTPUT_DIR`), rendered by `infrastructure/document_generation/inspection_generator.py`.

`backend/src/api/routes/history.py` — a flat JSON file (`/data/output/history.json`) tracking generated reports (driver, plate, filename, size, timestamp). No database involved; list/download/delete endpoints read/write the same file directly (not safe under concurrent writers, but the bot/frontend don't currently write concurrently).

### The legacy CRUD stack

`domain/` → `application/` → `infrastructure/` → `api/` is a textbook Clean Architecture layering for `vehicles`, `inspections`, `templates`, `users`, `documents` (Postgres via SQLAlchemy async, repositories translating between ORM models and domain entities). It's fully wired into `main.py`'s router list and the DB does get created on startup, but nothing in the current frontend calls these endpoints. Treat it as available infrastructure to build on if a task asks for it, not as something already exercised end-to-end.

### Bot

`bot/src/main.py`'s `InspectionBot` runs two concurrent loops: a polling loop (`_polling_loop`, exponential backoff up to 60s when idle) that calls `DocumentGenerationHandler.process_pending()` and `InspectionHandler.process_pending()` against the legacy CRUD endpoints, and a Redis pub/sub subscriber (`task:generate` channel) for on-demand `generate_document` / `notify_whatsapp` tasks, with a Redis-based lock (`try_lock`/`release_lock`) to dedupe in-flight tasks. Since the CRUD endpoints it polls aren't populated by the current frontend, the polling side is effectively idle in practice — the pub/sub side is the more likely integration point for new work.

### Frontend

Vite + React 18 + TypeScript + TailwindCSS, both real pages (`GenerarPDF`, `History`) lazy-loaded in `App.tsx`. `GenerarPDF.tsx` is a 4-step wizard (idle → analyzing → review → done) driving the `/auto-analyze` + `/generate-pdf/auto` flow, with drag-and-drop upload, folder upload (`FolderUploadModal`), client-side image compression before upload (`utils/imageCompressor.ts`), and a manual drag-to-reorder review step. Other page files under `src/pages/` (Dashboard, Documents, Inspections, Templates, Users, Vehicles) exist from the CRUD-era UI but are not routed — check `App.tsx` before assuming any of them are reachable.

### Docker / infra

`docker-compose.yml` runs `postgres:16`, `redis:7`, `backend`, `frontend` (nginx serving the Vite build, proxying `/api` to `backend:8000`), and `bot`, all with memory/CPU limits and healthchecks, on a shared `vehicular-network`. `backend` depends on `postgres` being healthy; `bot` depends on `backend` + `redis`.

## Conventions

- Code (identifiers, comments) in English; user-facing strings and API error messages in Spanish (`HTTPException(detail=...)` messages are Spanish throughout `generate.py`).
- IDs are UUID strings (`str(uuid4())`); timestamps are ISO 8601 UTC.
- Async throughout: FastAPI + SQLAlchemy async on the backend, `asyncio`/`httpx.AsyncClient` in the bot. CPU-bound work (OpenCV classification, OCR) is pushed into `ThreadPoolExecutor`s rather than blocking the event loop — follow that pattern for new CPU-heavy analysis code.
- **Tesseract does not survive high concurrency.** `classify_batch` fans out to 8 threads, and Tesseract subprocesses starve each other badly under that load — on the 81-photo eval set, essentially every OCR call hits its timeout, versus 1 of 81 when run sequentially. Mitigations in place: `timeout=10` on `pytesseract.image_to_data` (a hung Tesseract can no longer block a whole request — the photo just loses its OCR override and falls back to the embedding, which covers those positions well on its own) and a module-level `threading.Semaphore(2)` capping concurrent Tesseract processes. Neither fully fixes throughput; the root cause is CPU capacity, not application logic (capping ONNX to single-threaded inference was tried and reverted — 2.8x slower with no fewer timeouts). Real batches are 11-13 photos, not 81, so practical impact is smaller than the stress test suggests. **Don't add more per-photo subprocess work to this path without measuring.**
- No authentication implemented anywhere; `BOT_API_KEY` is sent as a Bearer token by the bot but never validated by the backend.
