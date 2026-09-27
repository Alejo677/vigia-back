from abc import ABC, abstractmethod

from src.domain.value_objects.access_token_claims import AccessTokenClaims


class IAccessTokenValidator(ABC):
    """Valida tokens de acceso emitidos por el proveedor de identidad."""

    @abstractmethod
    async def validate(self, raw_token: str) -> AccessTokenClaims:
        """Valida firma, emisor, audiencia, vigencia y scope del token.

        Recibe el primitivo `str` porque el token es un valor opaco sin entidad de dominio.

        Args:
            raw_token: token de acceso sin el prefijo `Bearer`.

        Returns:
            Claims del token validado.

        Raises:
            Exception: la excepción de su infraestructura con el motivo de rechazo.
        """
