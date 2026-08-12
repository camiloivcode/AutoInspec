# AutoInspec

Generador de reportes de inspección vehicular: el usuario sube un lote de fotos, un clasificador las asigna automáticamente a las 11 posiciones de inspección, y el backend genera el PDF.

```
AutoInspec/
├── docker-compose.yml
│   ├── backend         :8000   (FastAPI async)
│   └── frontend        :80     (React + Nginx)
```

---

## Flujo principal: fotos → PDF

1. El usuario sube un lote de fotos de la inspección.
2. `POST /api/auto-analyze` clasifica cada foto en una de las 11 posiciones y extrae la placa por OCR.
3. El usuario revisa y corrige las asignaciones en la interfaz.
4. `POST /api/generate-pdf/auto` genera el reporte.
5. Las correcciones se guardan en `/data/feedback/labels.jsonl` como datos de entrenamiento.

### El clasificador

Encoder de visión **CLIP ViT-B/32** (ONNX cuantizado, ~85 MB, se descarga en tiempo de build) más una cabeza de regresión logística de 11×512 entrenada sobre las fotos de ajuste. La inferencia es solo numpy (`softmax(W @ embedding + b)`), sin dependencias de ML en runtime. Dos señales independientes pueden sobrescribir el resultado del embedding: densidad de texto por OCR (posiciones 1 y 11, documentos) y detección de rostro con Haar cascade (posición 8, conductor).

Reemplazó a una cascada de umbrales absolutos ajustados a mano que medía **4.94%** de acierto. Detalle de arquitectura, números de precisión, comandos de evaluación y reentrenamiento: ver `CLAUDE.md`.

---

## Documentación por servicio

- [Backend](#backend) — API REST, puerto `:8000`
- [Frontend](#frontend) — SPA React, puerto `:80` (producción) / `:5173` (desarrollo)

---

## Backend

API REST con FastAPI. Sin base de datos: el estado (fotos en curso, reportes generados) vive en el filesystem bajo `/data/`.

### Puertos

| Entorno | Puerto |
|---------|--------|
| Docker  | `http://localhost:8000` |
| Desarrollo | `http://localhost:8000` |

### Endpoints principales

| URL | Descripción |
|-----|-------------|
| `http://localhost:8000/docs` | Documentación Swagger UI |
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/api/health` | Health check API |

### Cómo ejecutar

**Docker:**
```bash
docker compose up --build backend
```

**Desarrollo (local):**
```bash
cd backend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

Requiere `tesseract-ocr` (+ paquete de idioma `spa`) y LibreOffice (`libreoffice-writer`) instalados localmente — ver `backend/Dockerfile` para los paquetes exactos.

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Host backend |
| `API_PORT` | `8000` | Puerto backend |

### Estructura

```
backend/
├── Dockerfile
├── Dockerfile.eval          # imagen dev: + scikit-learn, para eval/ y reentrenamiento
├── .dockerignore
├── requirements.txt
├── fotos_prueba/            # 81 fotos etiquetadas por subcarpeta (dataset de ajuste)
├── eval/                    # evaluate.py, grouping.py, train_head.py, results/
├── tests/
└── src/
    ├── main.py              # create_app()
    ├── api/
    │   ├── routes/          # generate, history, health
    │   └── middleware/      # CORS, error handler
    └── infrastructure/
        ├── analysis/        # clasificador: embedding_classifier, photo_classifier
        ├── ocr/             # detección de placa
        ├── feedback/        # persistencia de correcciones del usuario
        └── document_generation/  # generación del PDF (python-docx + LibreOffice)
```

---

## Frontend

SPA con React 18 + TypeScript + Vite + TailwindCSS.

### Puertos

| Entorno | Puerto | Proxy `/api` → |
|---------|--------|----------------|
| **Docker (producción)** | **`http://localhost:80`** | `backend:8000` (Nginx) |
| Desarrollo (vite dev) | `http://localhost:5173` | `backend:8000` (Vite proxy) |

> En producción con Docker, el frontend se sirve en **`http://localhost`** (puerto 80).

### Cómo ejecutar

**Docker:**
```bash
docker compose up --build frontend
# Abrir en http://localhost
```

**Desarrollo (local):**
```bash
cd frontend
npm install
npm run dev
# Abrir en http://localhost:5173
```

El proxy de Vite redirige `/api/*` a `http://localhost:8000` automáticamente.

### Stack

React 18, React Router v6, TanStack Query, Zustand, TailwindCSS, Radix UI (dialog, select, popover), react-dropzone, clsx, Lucide icons, y la tipografía Overpass autohospedada vía `@fontsource`.

### Patrones

- **API calls:** `fetch` directo contra `/api` (el proxy resuelve el host). No hay capa de servicios: son cuatro endpoints y viven junto a quien los usa.
- **Estado servidor:** TanStack Query en `History` (listado, borrado, invalidación tras generar un PDF).
- **Estado del wizard:** dos hooks propios en `pages/GenerarPDF/` — `useGenerationFlow` (máquina de pasos + subida) y `useImageQueue` (cola de imágenes y ciclo de vida de los object URLs).
- **Estado global mínimo:** Zustand solo para UI local (sidebar, tema).
- **UI:** primitivos en `components/ui/`. La UI nueva se construye sobre ellos, no con Tailwind suelto.

### Diseño

La identidad visual (paleta de señalización vial, tipografía Overpass, escala de formas, reglas de aplicación del color) está documentada en **[`frontend/DESIGN.md`](frontend/DESIGN.md)**. Léelo antes de tocar colores, radios o tipografía.

### Flujo de `GenerarPDF`

```
Fotos ──→ Análisis ──→ Revisión ──→ PDF
  │           │            │          │
  │           │            │          └── descarga + queda en Historial
  │           │            └── corregir posiciones: por mapa del vehículo
  │           │                o por desplegable en cada foto
  │           └── POST /api/auto-analyze (posiciones + placa por OCR)
  └── arrastrar, elegir archivos, o subir una carpeta completa
```

Las fotos se comprimen en el navegador antes de subirlas (`utils/imageCompressor.ts`). La subida de carpetas usa un input con `webkitdirectory`, que funciona sobre HTTP plano (no exige contexto seguro) en todos los navegadores de escritorio y en Chrome de Android; donde no hay soporte, el botón no se muestra.

### Estructura

```
frontend/
├── Dockerfile
├── .dockerignore
├── nginx.conf              # proxy_pass /api → backend:8000
├── eslint.config.js        # ESLint 9 flat config
├── DESIGN.md               # sistema de diseño
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── index.html              # aplica el tema oscuro antes de hidratar
└── src/
    ├── main.tsx            # entrypoint: providers + fuentes
    ├── App.tsx             # rutas (/, /history, 404)
    ├── components/
    │   ├── ui/             # primitivos: Button, Card, Field, Select,
    │   │                   # Badge, Modal, Skeleton, EmptyState, Spinner
    │   ├── Layout.tsx      # shell: Sidebar + Header + BottomNav
    │   ├── Sidebar.tsx     # rail fijo ≥md
    │   ├── BottomNav.tsx   # navegación inferior <md
    │   ├── Header.tsx
    │   └── ImagePreview.tsx
    ├── context/
    │   └── ToastContext.tsx
    ├── pages/
    │   ├── GenerarPDF/
    │   │   ├── index.tsx           # orquestador
    │   │   ├── positions.ts        # las 11 posiciones (espejo del backend)
    │   │   ├── useGenerationFlow.ts
    │   │   ├── useImageQueue.ts
    │   │   ├── steps/              # StepUpload/Analyzing/Review/Done
    │   │   └── components/         # DropZone, PhotoCard,
    │   │                           # PositionMap, StepIndicator
    │   ├── History.tsx
    │   └── NotFound.tsx
    ├── hooks/
    │   └── useSystemStatus.ts      # sondea /api/health
    ├── store/                      # Zustand
    ├── utils/                      # imageCompressor
    └── index.css                   # tokens + Tailwind
```

---

## Ejecución general

### Docker (todo junto)

```bash
cp .env.example .env
docker compose up --build
```

Servicios levantados:

| Servicio | URL |
|----------|-----|
| Frontend | **http://localhost** |
| Backend (API) | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

### Comandos útiles

```bash
docker compose logs -f              # Logs de todos
docker compose logs -f backend     # Logs de un servicio
docker compose down                 # Detener
docker compose down -v              # Detener + borrar volúmenes
```

---

## API REST

Documentación interactiva: `http://localhost:8000/docs`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/health` | Health check API |
| POST | `/api/auto-analyze` | Clasifica las fotos y detecta la placa |
| POST | `/api/generate-pdf/auto` | Genera el PDF desde el flujo asistido |
| POST | `/api/generate-pdf` | Genera el PDF con asignación manual |
| GET | `/api/history` | Reportes generados |
| GET | `/api/history/download/{filename}` | Descarga un reporte |
| DELETE | `/api/history/{id}` | Borra un registro del historial |

---

## Convenciones del proyecto

- **Idioma:** Código en inglés. UI y mensajes al usuario en español.
- **IDs:** UUIDs como strings (`str(uuid4())`).
- **Fechas:** ISO 8601 UTC.
- **Async toda la pila:** Backend async/await. Trabajo CPU-bound (OpenCV, OCR) se despacha a `ThreadPoolExecutor`.
- **Sin autenticación:** todos los endpoints están abiertos.
- **Testing:** `backend/tests/` está vacío, sin framework configurado. La precisión del clasificador se mide con `backend/eval/evaluate.py` (no es pytest); ver `CLAUDE.md` para los comandos.
- **Linter:** El frontend tiene ESLint 9 (`frontend/eslint.config.js`) y typecheck vía `tsc -b` dentro de `npm run build`. En Python no hay ruff ni mypy.

### Documentos

- **Generación:** `python-docx` arma un `.docx` por posición, y LibreOffice headless lo convierte a PDF (fallback: se entrega el `.docx` si LibreOffice no está disponible).
- **Uploads:** `/data/uploads` (volumen Docker `uploads_data`), se borra al terminar cada request.
- **Salida:** `/data/output` (volumen Docker `output_data`), incluye `history.json`.

---

## Cómo contribuir

### Agregar un nuevo endpoint

1. Crear ruta en `backend/src/api/routes/`
2. Registrar el router en `backend/src/api/routes/__init__.py`
3. Consumirlo desde el frontend con `fetch` (y TanStack Query si necesita cacheo)
4. Crear página/componente en `frontend/src/pages/`, construyéndolo sobre los primitivos de `frontend/src/components/ui/`

---

## Estructura general del proyecto

```
AutoInspec/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── CLAUDE.md         # Guía de arquitectura para trabajar en el repo
├── README.md
├── backend/          → Documentación arriba
└── frontend/         → Documentación arriba
    └── DESIGN.md     # Sistema de diseño de la interfaz
```
