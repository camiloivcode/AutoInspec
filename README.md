# AutoInspec

Sistema integral para gestión de inspecciones vehiculares con generación automatizada de documentos (Word/PDF).

```
AutoInspec/
├── docker-compose.yml
│   ├── postgres:16     :5432   (persistencia)
│   ├── redis:7         :6379   (cola/estado bot)
│   ├── backend         :8000   (FastAPI async)
│   ├── frontend        :80     (React + Nginx)
│   └── bot             —       (polling, sin puerto expuesto)
```

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
├── requirements.txt
├── tests/
└── src/
    ├── main.py              # create_app(), lifespan, auto-migración
    ├── api/
    │   ├── routes/          # health, vehicles, inspections, documents, templates, users
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

React 18, React Router v6, TanStack Query, Zustand, TailwindCSS, Axios, Lucide icons, react-dropzone.

### Patrones

- **API calls:** Funciones tipadas en `services/api.ts` con axios.
- **Estado servidor:** TanStack Query (cacheo, refetch, mutaciones).
- **Estado global mínimo:** Zustand solo para UI local (sidebar, tema).
- **Ruteo:** React Router v6 con layout en `App.tsx`.

### Estructura

```
frontend/
├── Dockerfile
├── nginx.conf              # proxy_pass /api → backend:8000
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── index.html
└── src/
    ├── main.tsx            # Entrypoint
    ├── App.tsx             # Router + Layout
    ├── components/
    ├── pages/
    ├── services/           # api.ts (axios instance)
    ├── store/              # Zustand
    ├── hooks/
    ├── types/
    ├── utils/
    └── index.css           # Tailwind
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
- **Testing:** Directorios `tests/` sin framework configurado.
- **Sin linter/typecheck:** No hay ruff, mypy ni eslint. Frontend build corre `tsc -b`.

### Documentos

- **Word:** `python-docx` con plantillas `{{variable}}`.
- **PDF:** Conversión vía `docx2pdf` o LibreOffice headless.
- **Uploads:** `/data/uploads` (volumen Docker `uploads_data`).

---

## Shared (`shared/`)

Constantes compartidas entre backend, frontend y bot para mantener consistencia en la nomenclatura de la API.

```
shared/
└── types.py      # Estados de inspección, documento, roles, categorías
```

Incluye:
- Estados de inspección: `draft`, `in_progress`, `completed`, `cancelled`
- Tipos de documento: `word`, `pdf`
- Estados de documento: `pending`, `generated`, `error`
- Roles de usuario: `admin`, `inspector`, `client`
- Categorías de items: motor, transmisión, frenos, suspensión, etc.

---

## Cómo contribuir

### Agregar un nuevo endpoint

1. Crear ruta en `backend/src/api/routes/`
2. Definir caso de uso en `backend/src/application/use_cases/`
3. Implementar lógica de dominio si es necesario
4. Agregar repositorio concreto en `backend/src/infrastructure/database/`
5. Registrar el router en `backend/src/api/routes/__init__.py`
6. Agregar servicio frontend en `frontend/src/services/`
7. Crear página/componente en `frontend/src/pages/`

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
├── AGENTS.md
├── backend/          → Documentación arriba
├── frontend/         → Documentación arriba
├── bot/              → Documentación arriba
└── shared/
    └── types.py      # Constantes compartidas
```
