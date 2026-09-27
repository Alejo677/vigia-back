from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    """Claims de un token de acceso ya validado. No contiene el token."""

    oid: str
    email: str
    name: str
    roles: tuple[str, ...]
