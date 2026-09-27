from pydantic import BaseModel

from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.enums.user_role import UserRole


class CurrentUserResponse(BaseModel):
    """Usuario autenticado devuelto por `GET /api/v1/auth/me`."""

    oid: str
    email: str
    name: str
    role: UserRole

    @classmethod
    def from_user(cls, user: AuthenticatedUser) -> "CurrentUserResponse":
        """Convierte el usuario autenticado en el cuerpo de la respuesta.

        Args:
            user: usuario obtenido del token.

        Returns:
            Respuesta con los datos del usuario y su rol.
        """
        return cls(oid=user.oid, email=user.email, name=user.name, role=user.role)
