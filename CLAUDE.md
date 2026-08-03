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

**Tests:** There is no configured test runner. `backend/tests/` is empty. The `test_*.py` and `analyze.py`/`centroids.py`/`count.py`/`per_pos.py` files at `backend/` root are **manual tuning scripts for the photo classifier**, not a pytest suite — they hardcode `/app/fotos_prueba` (a container path) and are meant to be run inside the backend container/image against the bundled sample datasets (`fotos_prueba/`, `ref_train/`, `ref_test/`, `fotos_prueba_holdout/`) while hand-tuning thresholds. There's no lint/typecheck configured for Python; frontend type-checks via `tsc -b` as part of `npm run build`.

## Architecture

### The classifier pipeline (the part that matters)

- `backend/src/infrastructure/analysis/reference_matcher.py` — `extract_features()`: pulls a fixed set of hand-engineered features out of one image (brightness, edge %, HSV saturation/hue, blue/green ratios, Laplacian variance for sharpness, sky-blue ratio in top third, Sobel edge-orientation histogram, 3x3 quadrant brightness/std). No ML model and no embedding/similarity search against reference photos despite the filename — it's pure feature extraction consumed by hand-written thresholds.
- `backend/src/infrastructure/analysis/photo_classifier.py` — `PhotoClassifier.classify()` runs the extracted features through a cascade of hand-tuned detector groups, in order: document/text (Tesseract OCR text density) → driver (Haar cascade face detection, `cv2.data.haarcascades`) → car-parts close-ups (Hough circles for wheels, HSV red-mask for kit items) → exterior (sky-blue ratio, headlight/taillight color detection, horizontal symmetry, Hough lines/circles for side profiles). `classify_batch()` parallelizes per-image classification with a `ThreadPoolExecutor`, then resolves position collisions via `_find_alternative_position`'s hardcoded group map (e.g. position 2 collides → try 3 or 6) so each of the 11 slots gets at most one photo (position 10 is the exception, capped at 2 — see `MAX_PER_POSITION` in `generate.py`).
- `INSPECTION_POSITIONS` (dict of 11 fixed positions, defined in `photo_classifier.py`) is the canonical position list. It's duplicated as the `POSITIONS` array in `frontend/src/pages/GenerarPDF.tsx` — **keep both in sync** if positions ever change.
- `backend/src/infrastructure/ocr/plate_detector.py` — plate OCR/regex extraction, run in parallel with classification via `asyncio.gather` in the `/api/auto-analyze` route.
- The sample photo directories (`fotos_prueba/`, `ref_train/`, `ref_test/`, `fotos_prueba_holdout/`, both at repo root and under `backend/`) are tuning/eval datasets for the scripts above, not runtime assets — except `backend/fotos_prueba/` which the Dockerfile bakes into the image (`COPY fotos_prueba /app/fotos_prueba`) purely so the tuning scripts can be run inside a shipped container.

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
