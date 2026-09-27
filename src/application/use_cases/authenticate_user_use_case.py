import logging

from src.application.dtos.authenticate_user_request import AuthenticateUserRequest
from src.core.exceptions.authenticate_user_exception import AuthenticateUserException
from src.core.exceptions.forbidden_exception import ForbiddenException
from src.core.exceptions.unauthorized_exception import UnauthorizedException
from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.enums.token_rejection_reason import TokenRejectionReason
from src.domain.interfaces.i_access_token_validator import IAccessTokenValidator
from src.infrastructure.auth.entra_id_token_validator_exception import EntraIdTokenValidatorException

logger = logging.getLogger(__name__)


class AuthenticateUserUseCase:
    """Obtiene el usuario autenticado y su rol a partir del token de acceso (ESP-14)."""

    def __init__(self, validator: IAccessTokenValidator) -> None:
        self._validator = validator

    async def execute(self, request: AuthenticateUserRequest) -> AuthenticatedUser:
        """Valida el token y resuelve el usuario con su rol.

        Args:
            request: petición con el token de la cabecera Authorization.

        Returns:
            Usuario autenticado.

        Raises:
            UnauthorizedException: token ausente o inválido (401).
            ForbiddenException: token válido sin rol reconocido (403).
            AuthenticateUserException: no se pudo validar por causas ajenas al cliente (503).
        """
        if not request.bearer_token:
            logger.info("🔐 Petición sin token", extra={"reason": TokenRejectionReason.MISSING.value})
            raise UnauthorizedException("Falta el token de acceso", TokenRejectionReason.MISSING)
        try:
            claims = await self._validator.validate(request.bearer_token)
        except EntraIdTokenValidatorException as e:
            raise self._rejection_to_exception(e.reason) from None
        except Exception as e:
            logger.error("❌ Error inesperado al validar el token", extra={"error": type(e).__name__})
            raise AuthenticateUserException("No se pudo validar el token") from None
        try:
            return AuthenticatedUser.from_claims(claims)
        except ValueError:
            logger.warning("🔐 Token sin rol de OneWatch", extra={"oid": claims.oid})
            raise ForbiddenException("El usuario no tiene ningún rol de OneWatch") from None

    @staticmethod
    def _rejection_to_exception(reason: TokenRejectionReason) -> Exception:
        if reason is TokenRejectionReason.KEYS_UNAVAILABLE:
            logger.error("❌ Claves de Entra ID no disponibles", extra={"reason": reason.value})
            return AuthenticateUserException("No se pudieron obtener las claves de Entra ID")
        logger.info("🔐 Token rechazado", extra={"reason": reason.value})
        return UnauthorizedException("Token de acceso no válido", reason)
