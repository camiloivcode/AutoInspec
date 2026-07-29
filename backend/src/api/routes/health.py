from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "autoinspec-api", "version": "1.0.0"}


@router.get("/api/health")
async def api_health_check():
    return {"status": "ok", "service": "autoinspec-api", "version": "1.0.0"}
