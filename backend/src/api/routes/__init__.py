from .health import router as health_router
from .generate import router as generate_router
from .history import router as history_router
from .vehicles import router as vehicles_router
from .inspections import router as inspections_router
from .templates import router as templates_router
from .users import router as users_router
from .documents import router as documents_router

routers = [
    health_router,
    generate_router,
    history_router,
    vehicles_router,
    inspections_router,
    templates_router,
    users_router,
    documents_router,
]
