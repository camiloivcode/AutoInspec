# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this actually is

AutoInspec's live product is a **vehicle inspection photo → PDF report generator**: a user uploads a batch of photos, a heuristic computer-vision classifier auto-assigns each photo to one of 11 fixed inspection positions (frontal, side views, driver, spare tire kit, SOAT/documents, etc.), OCR suggests the license plate, the user reviews/corrects the assignment, and the backend renders a PDF report.

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

**Tests:** There is no configured test runner. `backend/tests/` is empty. `backend/eval/evaluate.py` is the classifier accuracy tool (not pytest) — it groups `fotos_prueba/` images into approximate photo sessions by filename timestamp (`eval/grouping.py`) before evaluating, so near-duplicate consecutive shots can't leak across a train/holdout boundary, and writes a dated JSON report + confusion matrix to `backend/eval/results/`. It needs `cv2`/`pytesseract` (native Tesseract binary), so run it inside the backend image, e.g. `docker compose run --rm -v "$(pwd)/backend/fotos_prueba:/app/fotos_prueba" backend python -m eval.evaluate --dataset /app/fotos_prueba`. Pass `--no-ocr` (or set `SKIP_OCR_DETECTION=1`) to skip the Tesseract text-density pass: it is **known to hang indefinitely** in the eval container, and every accuracy number currently recorded was measured with OCR disabled — so positions 1/11 in those results rest entirely on the embedding, not on the document override that does run in production. `backend/eval/train_head.py` retrains the classification head; it needs scikit-learn, which is deliberately absent from `requirements.txt` (runtime inference is numpy-only), so it needs an image with that dependency added. There's no lint/typecheck configured for Python; frontend type-checks via `tsc -b` as part of `npm run build`.

## Architecture

### The classifier pipeline (the part that matters)

- `backend/src/infrastructure/analysis/reference_matcher.py` — `extract_features()`: returns three normalized-image features (`brightness`, `brightness_median`, `white_ratio`) consumed only by the OCR override's brightness/white-ratio gate in `_detect_document_override`. Used to compute 19 hand-engineered features (HSV saturation/hue, blue/green ratios, Laplacian variance, sky-blue ratio, etc.) for the old threshold cascade; trimmed to what's actually read once the CLIP embedding classifier (see below) replaced that cascade.
- `backend/src/infrastructure/analysis/embedding_classifier.py` — `EmbeddingPositionClassifier`, the primary classifier as of 2026-08-06. Embeds a photo with a CLIP ViT-B/32 vision encoder (ONNX, dynamic-quantized, ~85MB, downloaded at Docker build time from HuggingFace — see `Dockerfile`, not committed to the repo) and scores it against an 11x512 logistic regression head (`position_head.json`, **committed**, trained offline by `eval/train_head.py` on the 81 tuning photos + on-the-fly augmentation — brightness/contrast/saturation jitter, ±5° rotation, 90-100% crop, JPEG noise; **never horizontal flip**, since positions 4/5 and 3/7 are mirror-image pairs and a flipped photo would carry the wrong label). Inference is numpy-only (`softmax(W @ embedding + b)`); scikit-learn is a training-only dependency, not in `requirements.txt`.
- `backend/src/infrastructure/analysis/photo_classifier.py` — `PhotoClassifier.classify()` calls the embedding classifier above for the general case, with two independent-signal overrides that win when they fire: strong OCR text density (Tesseract, `_detect_document_override`, positions 1/11) and Haar cascade face detection (`cv2.data.haarcascades`, position 8/Conductor). Everything the old cascade used to do — Hough circles for wheels, HSV red-mask for kit items, sky-blue ratio, headlight/taillight color detection, horizontal symmetry, Hough lines for side profiles — is gone; those hand-tuned absolute thresholds measured at **4.94% accuracy** on a session-held-out split (`backend/eval/results/`, see also `backend/eval/evaluate.py` under Tests) before being replaced. The face override is deliberately strict (`minNeighbors=9`, `min_size` proportional to the image rather than absolute pixels, single attempt): at OpenCV's defaults the cascade fired on 36 of 81 photos when only 7 are drivers — "faces" in wheels and seat texture — dragging accuracy down to 59%. Measured accuracy of the integrated classifier: **91.36%** per-photo in-sample with OCR enabled (88.89% with OCR disabled, since Tesseract subprocesses under `classify_batch`'s concurrent `ThreadPoolExecutor` can hit contention and time out -- see `_detect_text_density`'s `timeout=10`); the honest generalization number is the **75.31%** leave-one-session-out CV from `eval/train_head.py`.
- `classify_batch()` parallelizes per-image classification with a `ThreadPoolExecutor`, then resolves position collisions with a **deterministic global assignment**: every (photo, position, probability) pair from the embedding's full 11-class distribution becomes a candidate (OCR/face overrides contribute their single winning position at probability 1.0), all candidates are sorted descending, and slots are claimed greedily respecting `MAX_PER_POSITION` (position 10 allows 2, matching `generate.py`'s manual-assignment cap — both import the same constant). This replaced a hardcoded `COLLISION_ALLOW_LIST` adjacency map plus feature-centroid similarity scoring, which measured 66.67% with 16% of photos unassigned; the global assignment scores **80.25%**. The residual coverage gap is structural, not algorithmic: `MAX_PER_POSITION` offers 12 slots per session while the dataset averages 13.5 photos per session, so surplus photos have nowhere to go by design.
- `INSPECTION_POSITIONS` (dict of 11 fixed positions, defined in `photo_classifier.py`) is the canonical position list. It's duplicated as the `POSITIONS` array in `frontend/src/pages/GenerarPDF.tsx` — **keep both in sync** if positions ever change.
- `backend/src/infrastructure/ocr/plate_detector.py` — plate OCR/regex extraction, run in parallel with classification via `asyncio.gather` in the `/api/auto-analyze` route.
- `backend/fotos_prueba/` (repo root and under `backend/`, 81 images across the 11 position folders) is the only tuning/eval dataset — it is a source labeled by subfolder name, not a runtime asset, and is **not** baked into the backend image (mount it as a volume for `eval/evaluate.py` or `eval/train_head.py`).

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
- No authentication implemented anywhere; `BOT_API_KEY` is sent as a Bearer token by the bot but never validated by the backend.
