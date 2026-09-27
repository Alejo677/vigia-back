from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticateUserRequest:
    """Petición de autenticación con el token de la cabecera Authorization."""

    bearer_token: str | None

    def __repr__(self) -> str:
        # El token nunca debe aparecer en logs ni trazas (ESP-14, Regla 6)
        return f"AuthenticateUserRequest(bearer_token={'***' if self.bearer_token else None})"

    __str__ = __repr__
