from .health import router as health_router
from .generate import router as generate_router
from .history import router as history_router

routers = [
    health_router,
    generate_router,
    history_router,
]
