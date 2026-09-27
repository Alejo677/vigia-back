from dataclasses import dataclass

ENTRA_AUTHORITY = "https://login.microsoftonline.com"
DEFAULT_CLOCK_SKEW_SECONDS = 60


@dataclass(frozen=True, slots=True)
class AccessTokenPolicy:
    """Qué debe cumplir un token de acceso para aceptarse (ESP-14)."""

    issuer: str
    audience: str
    required_scope: str
    jwks_uri: str
    clock_skew_seconds: int = DEFAULT_CLOCK_SKEW_SECONDS

    @classmethod
    def from_tenant(cls, tenant_id: str, audience: str, required_scope: str) -> "AccessTokenPolicy":
        """Construye la política para los tokens v2.0 de un tenant de Entra ID.

        Args:
            tenant_id: identificador del tenant corporativo.
            audience: client id del registro de aplicación de la API.
            required_scope: scope delegado que debe aparecer en `scp`.

        Returns:
            Política con el emisor y el JWKS del tenant.
        """
        return cls(
            issuer=f"{ENTRA_AUTHORITY}/{tenant_id}/v2.0",
            audience=audience,
            required_scope=required_scope,
            jwks_uri=f"{ENTRA_AUTHORITY}/{tenant_id}/discovery/v2.0/keys",
        )
