import asyncio
from typing import Any

import jwt
from jwt import PyJWK, PyJWKClient
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    MissingRequiredClaimError,
    PyJWKClientConnectionError,
    PyJWKClientError,
    PyJWTError,
)

from src.domain.enums.token_rejection_reason import TokenRejectionReason
from src.domain.interfaces.i_access_token_validator import IAccessTokenValidator
from src.domain.value_objects.access_token_claims import AccessTokenClaims
from src.domain.value_objects.access_token_policy import AccessTokenPolicy
from src.infrastructure.auth.entra_id_token_validator_exception import EntraIdTokenValidatorException

# Único algoritmo admitido: evita la confusión de algoritmos (none, HS256 con la clave pública)
ALLOWED_ALGORITHM = "RS256"
REQUIRED_CLAIMS = ["exp", "nbf", "iss", "aud", "oid"]
JWKS_CACHE_SECONDS = 3600
# Mínimo entre refrescos forzados por un kid desconocido (plan ESP-14, D5)
JWKS_MIN_REFRESH_SECONDS = 60
JWKS_TIMEOUT_SECONDS = 10

# Orden relevante: las subclases van antes que sus padres (InvalidSignatureError hereda de DecodeError)
_REJECTION_BY_ERROR: tuple[tuple[type[PyJWTError], TokenRejectionReason], ...] = (
    (ExpiredSignatureError, TokenRejectionReason.EXPIRED),
    (ImmatureSignatureError, TokenRejectionReason.NOT_YET_VALID),
    (InvalidAudienceError, TokenRejectionReason.INVALID_AUDIENCE),
    (InvalidIssuerError, TokenRejectionReason.INVALID_ISSUER),
    (InvalidSignatureError, TokenRejectionReason.INVALID_SIGNATURE),
    (PyJWKClientConnectionError, TokenRejectionReason.KEYS_UNAVAILABLE),
    (PyJWKClientError, TokenRejectionReason.INVALID_SIGNATURE),
    (DecodeError, TokenRejectionReason.MALFORMED),
)


def build_jwks_client(jwks_uri: str) -> PyJWKClient:
    """Crea el cliente JWKS con la caché y el límite de refrescos de ESP-14.

    Args:
        jwks_uri: URL del JWKS del tenant.

    Returns:
        Cliente JWKS configurado.
    """
    return PyJWKClient(
        jwks_uri,
        cache_jwk_set=True,
        lifespan=JWKS_CACHE_SECONDS,
        cooldown_duration=JWKS_MIN_REFRESH_SECONDS,
        timeout=JWKS_TIMEOUT_SECONDS,
    )


class EntraIdAccessTokenValidator(IAccessTokenValidator):
    """Valida tokens de acceso v2.0 de Microsoft Entra ID contra el JWKS del tenant."""

    def __init__(self, policy: AccessTokenPolicy, jwks_client: PyJWKClient) -> None:
        self._policy = policy
        self._jwks_client = jwks_client

    async def validate(self, raw_token: str) -> AccessTokenClaims:
        """Valida firma RS256, emisor, audiencia, exp/nbf y scope del token.

        Args:
            raw_token: token de acceso sin el prefijo `Bearer`.

        Returns:
            Claims del token validado.

        Raises:
            EntraIdTokenValidatorException: con el motivo del rechazo.
        """
        try:
            kid = self._read_kid(raw_token)
            signing_key = self._cached_signing_key(kid)
            if signing_key is None:
                signing_key = await asyncio.to_thread(self._jwks_client.get_signing_key, kid)
            payload = self._decode(raw_token, signing_key)
        except MissingRequiredClaimError as e:
            reason = (
                TokenRejectionReason.MISSING_IDENTITY if e.claim == "oid" else TokenRejectionReason.MALFORMED
            )
            raise EntraIdTokenValidatorException(reason) from None
        except PyJWTError as e:
            raise EntraIdTokenValidatorException(self._reason_for(e)) from None
        self._check_scope(payload)
        return self._to_claims(payload)

    @staticmethod
    def _read_kid(raw_token: str) -> str:
        header = jwt.get_unverified_header(raw_token)
        if header.get("alg") != ALLOWED_ALGORITHM:
            raise InvalidSignatureError("Algoritmo no admitido")
        kid = header.get("kid")
        if not isinstance(kid, str) or not kid:
            raise DecodeError("Cabecera sin kid")
        return kid

    def _cached_signing_key(self, kid: str) -> PyJWK | None:
        """Busca la clave ya en la caché en memoria del JWKS, sin tocar la red.

        Evita el salto a un hilo (`asyncio.to_thread`) en el caso común de un `kid`
        ya conocido; solo cuando esto devuelve `None` hace falta ir a `PyJWKClient`.

        Args:
            kid: identificador de la clave del token.

        Returns:
            La clave si ya está en la caché vigente, o `None` si no (cache fría o `kid` no visto).
        """
        cache = self._jwks_client.jwk_set_cache
        jwk_set = cache.get() if cache is not None else None
        if jwk_set is None:
            return None
        signing_keys = [key for key in jwk_set.keys if key.public_key_use in ("sig", None)]
        return self._jwks_client.match_kid(signing_keys, kid)

    def _decode(self, raw_token: str, signing_key: PyJWK) -> dict[str, Any]:
        payload: dict[str, Any] = jwt.decode(
            raw_token,
            signing_key.key,
            algorithms=[ALLOWED_ALGORITHM],
            audience=self._policy.audience,
            issuer=self._policy.issuer,
            leeway=self._policy.clock_skew_seconds,
            options={"require": REQUIRED_CLAIMS},
        )
        return payload

    def _check_scope(self, payload: dict[str, Any]) -> None:
        scopes = payload.get("scp")
        if not isinstance(scopes, str) or self._policy.required_scope not in scopes.split():
            raise EntraIdTokenValidatorException(TokenRejectionReason.MISSING_SCOPE)

    @staticmethod
    def _to_claims(payload: dict[str, Any]) -> AccessTokenClaims:
        email = payload.get("preferred_username") or payload.get("email")
        if not isinstance(email, str) or not email:
            raise EntraIdTokenValidatorException(TokenRejectionReason.MISSING_IDENTITY)
        name = payload.get("name")
        roles = payload.get("roles") or []
        return AccessTokenClaims(
            oid=str(payload["oid"]),
            email=email,
            name=name if isinstance(name, str) and name else email,
            roles=tuple(r for r in roles if isinstance(r, str)) if isinstance(roles, list) else (),
        )

    @staticmethod
    def _reason_for(error: PyJWTError) -> TokenRejectionReason:
        for error_type, reason in _REJECTION_BY_ERROR:
            if isinstance(error, error_type):
                return reason
        return TokenRejectionReason.MALFORMED
