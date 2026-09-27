from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.domain.value_objects.access_token_policy import AccessTokenPolicy

DEFAULT_API_SCOPE = "access_as_user"


class Settings(BaseSettings):
    """Configuración del backend cargada desde variables de entorno."""

    model_config = SettingsConfigDict(extra="ignore")

    entra_tenant_id: str
    entra_api_client_id: str
    entra_api_scope: str = DEFAULT_API_SCOPE
    cors_allowed_origins: str = ""

    def access_token_policy(self) -> AccessTokenPolicy:
        """Política de validación de los tokens de acceso del tenant.

        Returns:
            Política con emisor, audiencia, scope y JWKS del tenant configurado.
        """
        return AccessTokenPolicy.from_tenant(
            tenant_id=self.entra_tenant_id,
            audience=self.entra_api_client_id,
            required_scope=self.entra_api_scope,
        )

    def cors_origins(self) -> list[str]:
        """Orígenes permitidos por CORS.

        Returns:
            Lista de orígenes a partir de `CORS_ALLOWED_ORIGINS` separada por comas.
        """
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Devuelve la configuración del proceso; falla si faltan las variables de Entra ID.

    Returns:
        Configuración cargada del entorno.
    """
    return Settings()  # type: ignore[call-arg]
