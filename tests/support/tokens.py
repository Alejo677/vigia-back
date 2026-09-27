"""Tokens de Entra ID de pruebas firmados con una clave RSA local (nunca del tenant real)."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWKClient
from jwt.algorithms import RSAAlgorithm
from jwt.exceptions import PyJWKClientConnectionError

from src.domain.value_objects.access_token_policy import AccessTokenPolicy

TEST_TENANT_ID = "11111111-1111-1111-1111-111111111111"
OTHER_TENANT_ID = "22222222-2222-2222-2222-222222222222"
TEST_API_CLIENT_ID = "33333333-3333-3333-3333-333333333333"
OTHER_API_CLIENT_ID = "44444444-4444-4444-4444-444444444444"
TEST_SCOPE = "access_as_user"
TEST_KID = "test-kid"
TEST_OID = "55555555-5555-5555-5555-555555555555"
TEST_EMAIL = "ana.perez@acme.com"
TEST_NAME = "Ana Pérez"
ONE_HOUR = 3600
TEN_MINUTES = 600

TEST_POLICY = AccessTokenPolicy.from_tenant(TEST_TENANT_ID, TEST_API_CLIENT_ID, TEST_SCOPE)


def new_private_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


SIGNING_KEY = new_private_key()
FOREIGN_KEY = new_private_key()


def jwks_for(private_key: rsa.RSAPrivateKey, kid: str = TEST_KID) -> dict[str, Any]:
    jwk = RSAAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    jwk.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return {"keys": [jwk]}


class LocalJwksClient(PyJWKClient):
    """PyJWKClient que sirve un JWKS local en lugar de descargarlo; cuenta las descargas."""

    def __init__(self, jwks: dict[str, Any], cooldown_duration: float = 60) -> None:
        super().__init__(
            "https://jwks.test/discovery/v2.0/keys",
            cache_jwk_set=True,
            lifespan=ONE_HOUR,
            cooldown_duration=cooldown_duration,
        )
        self._jwks = jwks
        self.fetch_count = 0
        self.unavailable = False

    def fetch_data(self) -> Any:
        if self.unavailable:
            raise PyJWKClientConnectionError("JWKS no accesible")
        self.fetch_count += 1
        self._last_successful_fetch = time.monotonic()
        return self._jwks


def base_claims() -> dict[str, Any]:
    now = int(time.time())
    return {
        "iss": TEST_POLICY.issuer,
        "aud": TEST_API_CLIENT_ID,
        "iat": now,
        "nbf": now,
        "exp": now + ONE_HOUR,
        "oid": TEST_OID,
        "preferred_username": TEST_EMAIL,
        "name": TEST_NAME,
        "scp": TEST_SCOPE,
        "roles": ["user"],
        "ver": "2.0",
    }


def make_token(
    remove: tuple[str, ...] = (),
    key: rsa.RSAPrivateKey = SIGNING_KEY,
    kid: str = TEST_KID,
    **overrides: Any,
) -> str:
    """Token RS256 de pruebas; `overrides` sustituye claims y `remove` los elimina."""
    claims = base_claims() | overrides
    for claim in remove:
        claims.pop(claim, None)
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": kid})


def make_hs256_token_with_public_key() -> str:
    """Token HS256 firmado usando la clave pública como secreto (ataque de confusión de algoritmo)."""
    secret = SIGNING_KEY.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )

    def b64(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = b64(json.dumps({"alg": "HS256", "typ": "JWT", "kid": TEST_KID}).encode())
    payload = b64(json.dumps(base_claims()).encode())
    signature = hmac.new(secret, f"{header}.{payload}".encode(), hashlib.sha256).digest()
    return f"{header}.{payload}.{b64(signature)}"
