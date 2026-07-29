# AGENTS.md

## Arquitectura: 3 servicios desacoplados

```
AutoInspec/
├── docker-compose.yml
│   ├── postgres:16  (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
│   ├── redis:7      (bot cola/estado)
│   ├── backend/     (FastAPI async, puerto 8000)
│   ├── frontend/    (React+Vite, sirve en nginx :80, proxy /api → backend:8000)
│   └── bot/         (servicio polling independiente, httpx async)
```

Todos los servicios comparten red `vehicular-network`. Backend requiere postgres healthy. Bot requiere backend + redis.

## Backend (`backend/`) — Clean Architecture + DDD

**Capas (de adentro hacia afuera, sin dependencias circulares):**
- `domain/` — entidades, value objects, interfaces de repositorio, servicios de dominio. Sin imports de infraestructura.
- `application/` — casos de uso (orquestan repositorios), DTOs de entrada/salida.
- `infrastructure/` — SQLAlchemy async models, repositorios concretos, generación Word/PDF, file storage.
- `api/` — rutas FastAPI, middleware CORS/errores, factoría de dependencias.

**Entrypoint:** `backend/src/main.py` — `create_app()` construye la app, `lifespan` ejecuta `create_tables()` (auto-migración con `Base.metadata.create_all`).

**ORM:** SQLAlchemy 2.0 async (asyncpg). Modelos en `infrastructure/database/models.py`. Los repositorios convierten entre modelos SQLAlchemy y entidades de dominio.

**Documentos:** Word con `python-docx`, PDF vía `docx2pdf` o LibreOffice headless. Variables en plantillas con `{{variable}}`.

**Uploads:** Almacenamiento local en `/data/uploads` (volumen Docker `uploads_data`). Las imágenes se sirven por `file_url` en la respuesta.

**Comandos:**
```bash
# desarrollo (desde backend/)
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# docker
docker compose up --build
```

## Frontend (`frontend/`) — React 18 + TypeScript + Vite

**Stack:** Vite, React Router v6, TanStack Query, Zustand, TailwindCSS, Axios, Lucide icons.

**Entrypoint:** `src/main.tsx` → `App.tsx` con layout (`components/Layout.tsx`) y rutas.

**Proxy dev:** Vite proxy `/api` → `http://backend:8000` (solo en `vite dev`). En producción, nginx proxy_pass.

**Comandos:**
```bash
cd frontend
npm install
npm run dev        # vite dev :5173
npm run build      # tsc -b && vite build
```

**Patrones:**
- Llamadas API vía `services/api.ts` (axios instance). Cada servicio exporta funciones que retornan datos tipados.
- Estado global mínimo via Zustand (`store/useAppStore.ts`). Estado servidor via TanStack Query.
- Tipos compartidos en `types/index.ts`.

## Bot (`bot/`) — Servicio polling independiente

**Entrypoint:** `src/main.py` — `InspectionBot` con ciclo asíncrono que cada `BOT_POLLING_INTERVAL_SECONDS` consulta documentos pendientes e inspecciones en progreso.

**Configuración vía variables `BOT_*`** (ver `src/config.py`).

**Futuras integraciones:** métodos stub `process_image_ocr()`, `notify_whatsapp()`, `process_batch()` listos para implementar.

**Comandos:**
```bash
cd bot
pip install -r requirements.txt
python -m src.main
```

## Convenciones del proyecto

- **Idioma:** Código (variables, clases, métodos) y comentarios en inglés. Strings de UI y mensajes al usuario en español.
- **IDs:** UUIDs generados como strings (`str(uuid4())`).
- **Fechas:** ISO 8601 strings (`datetime.utcnow().isoformat()`).
- **Async toda la pila:** Backend usa `async/await` con SQLAlchemy async. Bot usa `asyncio` + `httpx.AsyncClient`.
- **Sin typecheck/lint configurado:** No hay `pyproject.toml`, `ruff`, `mypy` ni `eslintrc` — el build de frontend corre `tsc -b`.
- **Testing:** Directorios `backend/tests/` y `bot/tests/` vacíos — no hay framework de test configurado ni comandos en `package.json`.
- **Sin autenticación implementada:** El bot acepta `BOT_API_KEY` como Bearer token pero el backend no valida. Endpoints abiertos.

## API REST (FastAPI auto-docs en `/docs`)

| Recurso | Prefix |
|---|---|
| Health | `/health`, `/api/health` |
| Vehicles | `/api/vehicles` |
| Inspections | `/api/inspections` (+ `/items`, `/images`) |
| Documents | `/api/documents` |
| Templates | `/api/templates` |
| Users | `/api/users` |

Estados de inspección: `draft`, `in_progress`, `completed`, `cancelled`.  
Tipos de documento: `word`, `pdf`. Estados: `pending`, `generated`, `error`.

## Shared (`shared/`)

Constantes compartidas entre backend, frontend y bot. Ver `shared/types.py`.

- Estados de inspección, documento, roles de usuario y categorías de items.
- Mantiene consistencia en la nomenclatura de la API entre los 3 servicios.
