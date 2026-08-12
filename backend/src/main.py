import os
import uvicorn
from fastapi import FastAPI

from .api.routes import routers
from .api.middleware.cors import setup_cors
from .api.middleware.error_handler import setup_error_handlers


def create_app() -> FastAPI:
    app = FastAPI(
        title="AutoInspec API",
        description="API REST para gestión de inspecciones vehiculares con generación de documentos",
        version="1.0.0",
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
