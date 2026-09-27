from fastapi import APIRouter

from src.application.dtos.current_user_response import CurrentUserResponse
from src.core.dependencies.auth import CurrentUser

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(user: CurrentUser) -> CurrentUserResponse:
    """Devuelve el usuario autenticado a partir del token. No persiste nada."""
    return CurrentUserResponse.from_user(user)
