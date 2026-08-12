# AutoInspec

Generador de reportes de inspección vehicular: el usuario sube un lote de fotos, un clasificador las asigna automáticamente a las 11 posiciones de inspección, y el backend genera el PDF.

```
AutoInspec/
├── docker-compose.yml
│   ├── postgres:16     :5432   (persistencia)
│   ├── redis:7         :6379   (cola/estado bot)
│   ├── backend         :8000   (FastAPI async)
│   ├── frontend        :80     (React + Nginx)
│   └── bot             —       (polling, sin puerto expuesto)
```

> **Nota sobre el alcance de este README.** La mayor parte de lo documentado abajo (CRUD de vehículos, inspecciones, plantillas, usuarios) corresponde a una iteración anterior más amplia. Esa capa sigue montada y sus endpoints responden, pero **el frontend actual solo enruta dos páginas**: generación de PDF (`/`) e historial (`/history`). El flujo vivo es el del clasificador de fotos descrito justo abajo.

---

## Flujo principal: fotos → PDF

1. El usuario sube un lote de fotos de la inspección.
2. `POST /api/auto-analyze` clasifica cada foto en una de las 11 posiciones y extrae la placa por OCR.
3. El usuario revisa y corrige las asignaciones en la interfaz.
4. `POST /api/generate-pdf/auto` genera el reporte.
5. Las correcciones se guardan en `/data/feedback/labels.jsonl` como datos de entrenamiento.

### El clasificador

Encoder de visión **CLIP ViT-B/32** (ONNX cuantizado, ~85 MB, se descarga en tiempo de build) más una cabeza de regresión logística de 11×512 entrenada sobre las fotos de ajuste. La inferencia es solo numpy (`softmax(W @ embedding + b)`), sin dependencias de ML en runtime. Dos señales independientes pueden sobrescribir el resultado del embedding: densidad de texto por OCR (posiciones 1 y 11, documentos) y detección de rostro con Haar cascade (posición 8, conductor).

Reemplazó a una cascada de umbrales absolutos ajustados a mano que medía **4.94%** de acierto. Precisión actual: **91.36%** en el set de ajuste (in-sample) y **75.31%** en validación cruzada dejando una sesión fuera — este último es el número honesto de generalización.

Detalle de arquitectura, comandos de evaluación y reentrenamiento: ver `CLAUDE.md`.

---

## Documentación por servicio

- [Backend](#backend) — API REST, puerto `:8000`
- [Frontend](#frontend) — SPA React, puerto `:80` (producción) / `:5173` (desarrollo)
- [Bot](#bot) — Servicio de polling en segundo plano

---

## Backend

API REST con FastAPI + SQLAlchemy async + Clean Architecture.

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
set DB_HOST=localhost DB_USER=postgres DB_PASSWORD=postgres DB_NAME=vehicular_inspections
uvicorn src.main:app --reload --port 8000
```

Requiere PostgreSQL en `localhost:5432`.

### Arquitectura

```
api/  →  application/  →  domain/  →  infrastructure/
  │            │              │              │
  │        (casos uso)   (reglas negocio)    │
  └─────────── depende de ───────────────────┘
```

- **`domain/`** — Entidades, value objects, interfaces. Sin dependencias externas.
- **`application/`** — Casos de uso, DTOs de entrada/salida.
- **`infrastructure/`** — SQLAlchemy async models, repositorios, generación Word/PDF, file storage.
- **`api/`** — Rutas FastAPI, middleware CORS/errores, factoría de dependencias.

### Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DB_HOST` | `postgres` | Host PostgreSQL |
| `DB_PORT` | `5432` | Puerto PostgreSQL |
| `DB_USER` | `postgres` | Usuario BD |
| `DB_PASSWORD` | `postgres` | Contraseña BD |
| `DB_NAME` | `vehicular_inspections` | Nombre BD |
| `API_HOST` | `0.0.0.0` | Host backend |
| `API_PORT` | `8000` | Puerto backend |

### Estructura

```
backend/
├── Dockerfile
├── Dockerfile.eval          # imagen dev: + scikit-learn, para eval/ y reentrenamiento
├── requirements.txt
├── fotos_prueba/            # 81 fotos etiquetadas por subcarpeta (dataset de ajuste)
├── eval/                    # evaluate.py, grouping.py, train_head.py, results/
├── tests/
└── src/
    ├── main.py              # create_app(), lifespan, auto-migración
    ├── api/
    │   ├── routes/          # generate, history + CRUD legacy
    │   ├── middleware/      # CORS, error handler
    │   └── dependencies.py
    ├── application/
    │   ├── use_cases/
    │   ├── dtos/
    │   └── interfaces/
    ├── domain/
    │   ├── entities/
    │   ├── value_objects/
    │   ├── repositories/
    │   └── services/
    └── infrastructure/
        ├── analysis/        # clasificador: embedding_classifier, photo_classifier
        ├── ocr/             # detección de placa
        ├── feedback/        # persistencia de correcciones del usuario
        ├── database/        # SQLAlchemy models, repositorios, settings
        ├── document_generation/  # Word (python-docx), PDF
        └── storage/
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

## Bot

Servicio independiente de polling que procesa documentos e inspecciones en segundo plano.

### Puertos

No expone puertos. Se comunica con el backend vía HTTP y con Redis para estado/cola.

### Cómo ejecutar

**Docker:**
```bash
docker compose up --build bot
```

**Desarrollo (local):**
```bash
cd bot
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
set BOT_API_BASE_URL=http://localhost:8000/api
set BOT_REDIS_URL=redis://localhost:6379/0
python -m src.main
```

Requiere Redis en `localhost:6379` y backend corriendo.

### Ciclo de vida

```
Inicia → check_api_health()
  └── loop cada N segundos (default 30):
        ├── GET /api/documents → filtrar "pending"
        │   └── POST /api/documents/{id}/generate
        └── GET /api/inspections → filtrar "in_progress"
            └── procesar (stub)
```

### Variables de entorno (prefijo `BOT_`)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BOT_API_BASE_URL` | `http://backend:8000/api` | URL base API |
| `BOT_API_KEY` | _(vacío)_ | Bearer token (opcional) |
| `BOT_REDIS_URL` | `redis://redis:6379/0` | Conexión Redis |
| `BOT_POLLING_INTERVAL_SECONDS` | `30` | Intervalo de polling |
| `BOT_LOG_LEVEL` | `INFO` | Nivel de log |
| `BOT_MAX_RETRIES` | `3` | Reintentos máximos |

### Métodos stub (listos para implementar)

- `process_image_ocr(image_url)` — OCR sobre imágenes
- `notify_whatsapp(to, message)` — Notificaciones WhatsApp
- `process_batch(inspection_ids)` — Procesamiento por lote

### Estructura

```
bot/
├── Dockerfile
├── requirements.txt
└── src/
    ├── main.py           # InspectionBot: ciclo asíncrono
    ├── config.py         # BotSettings (pydantic-settings)
    ├── services/         # Integraciones externas (stub)
    └── handlers/         # Manejadores de eventos
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
docker compose up -d --scale bot=3  # Escalar bot
```

### Diagrama de arranque

```
docker compose up --build
         │
    ┌────┴────┐
    ▼         ▼
 postgres   redis
 healthy   healthy
    │         │
    └──┬──────┘
       ▼
    backend
 create_tables()
       │
  ┌────┼────┐
  ▼    ▼    ▼
frontend bot  backend API
nginx:80 poll  :8000
```

---

## API REST

Documentación interactiva: `http://localhost:8000/docs`

**Flujo vivo** (lo que usa el frontend actual):

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auto-analyze` | Clasifica las fotos y detecta la placa |
| POST | `/api/generate-pdf/auto` | Genera el PDF desde el flujo asistido |
| POST | `/api/generate-pdf` | Genera el PDF con asignación manual |
| GET | `/api/history` | Reportes generados |

**Capa CRUD** (registrada y funcional, pero no la consume el frontend actual):

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/health` | Health check API |
| GET/POST | `/api/vehicles` | Listar/Crear vehículos |
| GET/PUT/DELETE | `/api/vehicles/{id}` | Obtener/Actualizar/Eliminar |
| GET/POST | `/api/inspections` | Listar/Crear inspecciones |
| GET/PUT | `/api/inspections/{id}` | Obtener/Actualizar |
| POST | `/api/inspections/{id}/items` | Agregar item |
| POST | `/api/inspections/{id}/images` | Agregar imagen |
| POST | `/api/inspections/{id}/complete` | Completar |
| GET/POST | `/api/documents` | Listar/Crear documentos |
| POST | `/api/documents/{id}/generate` | Generar documento |
| GET/POST | `/api/templates` | Listar/Crear plantillas |
| GET/POST | `/api/users` | Listar/Crear usuarios |

### Estados

| Entidad | Estados |
|---------|---------|
| Inspección | `draft` → `in_progress` → `completed` / `cancelled` |
| Documento | `pending` → `generated` / `error` |
| Tipo doc. | `word`, `pdf` |

### Diagrama de flujo de dominio

```
Inspección:
  draft ──→ in_progress ──→ completed
                │                 │
                └── cancelled ←──┘

Documento:
  pending ──→ generated
      │
      └──→ error

Generación:
  POST /api/documents/{id}/generate
       │
       ├──→ word (python-docx)
       │       └──→ pdf (docx2pdf / LibreOffice)
       │
       └──→ upload → /data/uploads/
```

---

## Convenciones del proyecto

- **Idioma:** Código en inglés. UI y mensajes al usuario en español.
- **IDs:** UUIDs como strings (`str(uuid4())`).
- **Fechas:** ISO 8601 (`datetime.utcnow().isoformat()`).
- **Async toda la pila:** Backend async/await con SQLAlchemy async. Bot con asyncio + httpx.
- **Sin autenticación:** Endpoints abiertos. `BOT_API_KEY` aceptado como Bearer pero no validado.
- **Testing:** Directorios `tests/` sin framework configurado. La precisión del clasificador se mide con `backend/eval/evaluate.py` (no es pytest); ver `CLAUDE.md` para los comandos.
- **Linter:** El frontend tiene ESLint 9 (`frontend/eslint.config.js`) y typecheck vía `tsc -b` dentro de `npm run build`. En Python no hay ruff ni mypy.

### Documentos

- **Word:** `python-docx` con plantillas `{{variable}}`.
- **PDF:** Conversión vía `docx2pdf` o LibreOffice headless.
- **Uploads:** `/data/uploads` (volumen Docker `uploads_data`).

---

## Cómo contribuir

### Agregar un nuevo endpoint

1. Crear ruta en `backend/src/api/routes/`
2. Definir caso de uso en `backend/src/application/use_cases/`
3. Implementar lógica de dominio si es necesario
4. Agregar repositorio concreto en `backend/src/infrastructure/database/`
5. Registrar el router en `backend/src/api/routes/__init__.py`
6. Consumirlo desde el frontend con `fetch` (y TanStack Query si necesita cacheo)
7. Crear página/componente en `frontend/src/pages/`, construyéndolo sobre los primitivos de `frontend/src/components/ui/`

### Agregar una nueva entidad

1. Crear entidad en `backend/src/domain/entities/`
2. Crear repositorio interfaz en `backend/src/domain/repositories/`
3. Crear modelo SQLAlchemy en `backend/src/infrastructure/database/models.py`
4. Crear repositorio concreto en `backend/src/infrastructure/database/`
5. Agregar caso de uso CRUD en `backend/src/application/use_cases/`
6. Agregar rutas API en `backend/src/api/routes/`

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
├── frontend/         → Documentación arriba
│   └── DESIGN.md     # Sistema de diseño de la interfaz
└── bot/              → Documentación arriba
```
