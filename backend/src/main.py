import os
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .api.routes import routers
from .api.middleware.cors import setup_cors
from .api.middleware.error_handler import setup_error_handlers
from .infrastructure.database.settings import create_tables

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await create_tables()
    except Exception as e:
        logger.warning(f"Base de datos no disponible (opcional): {e}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AutoInspec API",
        description="API REST para gestión de inspecciones vehiculares con generación de documentos",
        version="1.0.0",
        lifespan=lifespan,
    )

    setup_cors(app)
    setup_error_handlers(app)

    for router in routers:
        app.include_router(router)

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("src.main:app", host=host, port=port, reload=True)
