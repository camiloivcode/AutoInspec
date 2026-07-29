from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def setup_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "message": str(exc),
            },
        )
