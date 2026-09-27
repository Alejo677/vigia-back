from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.dtos.authenticate_user_request import AuthenticateUserRequest
from src.application.use_cases.authenticate_user_use_case import AuthenticateUserUseCase
from src.core.configuration.settings import get_settings
from src.core.exceptions.forbidden_exception import ForbiddenException
from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.enums.user_role import UserRole
from src.domain.interfaces.i_access_token_validator import IAccessTokenValidator
from src.infrastructure.auth.entra_id_access_token_validator import (
    EntraIdAccessTokenValidator,
    build_jwks_client,
)

_bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def get_access_token_validator() -> IAccessTokenValidator:
    """Validador único por proceso, para compartir la caché del JWKS.

    Returns:
        Validador de tokens de Entra ID.
    """
    policy = get_settings().access_token_policy()
    return EntraIdAccessTokenValidator(policy, build_jwks_client(policy.jwks_uri))


def get_authenticate_user_use_case(
    validator: Annotated[IAccessTokenValidator, Depends(get_access_token_validator)],
) -> AuthenticateUserUseCase:
    """Provider del caso de uso de autenticación.

    Args:
        validator: validador de tokens.

    Returns:
        Caso de uso de autenticación.
    """
    return AuthenticateUserUseCase(validator)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    use_case: Annotated[AuthenticateUserUseCase, Depends(get_authenticate_user_use_case)],
) -> AuthenticatedUser:
    """Valida el token de la cabecera Authorization y devuelve el usuario autenticado.

    Args:
        credentials: credenciales Bearer, o None si no hay cabecera válida.
        use_case: caso de uso de autenticación.

    Returns:
        Usuario autenticado con su rol.

    Raises:
        UnauthorizedException: token ausente o inválido (401).
        ForbiddenException: token sin rol de OneWatch (403).
    """
    token = credentials.credentials if credentials else None
    return await use_case.execute(AuthenticateUserRequest(bearer_token=token))


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def require_role(*roles: UserRole) -> Callable[[AuthenticatedUser], Awaitable[AuthenticatedUser]]:
    """Dependencia que restringe un endpoint a los roles indicados (ESP-14, Regla 4).

    Uso: `Depends(require_role(UserRole.ADMIN))`. En el MVP ningún endpoint la usa.

    Args:
        roles: roles admitidos.

    Returns:
        Dependencia de FastAPI que devuelve el usuario o lanza ForbiddenException (403).
    """

    async def _require_role(user: CurrentUser) -> AuthenticatedUser:
        if not user.has_role(*roles):
            raise ForbiddenException("Rol insuficiente")
        return user

    return _require_role
