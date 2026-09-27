from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Health Check de App Service. Público: no requiere token."""
    return {"status": "ok"}
