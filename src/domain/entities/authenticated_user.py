from dataclasses import dataclass

from src.domain.enums.user_role import UserRole
from src.domain.value_objects.access_token_claims import AccessTokenClaims

# Orden de precedencia: si llegan varios roles, prevalece el primero (ESP-14, Regla 1)
ROLE_PRECEDENCE: tuple[UserRole, ...] = (UserRole.ADMIN, UserRole.USER)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Usuario autenticado por Entra ID. No se persiste: sale del token en cada petición."""

    oid: str
    email: str
    name: str
    role: UserRole

    @classmethod
    def from_claims(cls, claims: AccessTokenClaims) -> "AuthenticatedUser":
        """Construye el usuario resolviendo su rol a partir del claim `roles`.

        Args:
            claims: claims de un token ya validado.

        Returns:
            Usuario con el rol de mayor precedencia.

        Raises:
            ValueError: si el token no trae ningún rol reconocido de OneWatch.
        """
        role = next((r for r in ROLE_PRECEDENCE if r.value in claims.roles), None)
        if role is None:
            raise ValueError("El token no contiene ningún rol de OneWatch")
        return cls(oid=claims.oid, email=claims.email, name=claims.name, role=role)

    def has_role(self, *roles: UserRole) -> bool:
        """Indica si el usuario tiene alguno de los roles indicados.

        Args:
            roles: roles admitidos.

        Returns:
            True si el rol del usuario está entre los indicados.
        """
        return self.role in roles
