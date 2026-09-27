import time

import pytest

from src.domain.enums.token_rejection_reason import TokenRejectionReason
from src.infrastructure.auth.entra_id_access_token_validator import (
    JWKS_MIN_REFRESH_SECONDS,
    EntraIdAccessTokenValidator,
)
from src.infrastructure.auth.entra_id_token_validator_exception import EntraIdTokenValidatorException
from tests.support.tokens import (
    SIGNING_KEY,
    TEST_EMAIL,
    TEST_NAME,
    TEST_OID,
    TEST_POLICY,
    LocalJwksClient,
    jwks_for,
    make_hs256_token_with_public_key,
    make_token,
)

pytestmark = pytest.mark.unit


async def _rejection(validator: EntraIdAccessTokenValidator, token: str) -> TokenRejectionReason:
    with pytest.raises(EntraIdTokenValidatorException) as exc:
        await validator.validate(token)
    return exc.value.reason


async def test_validate_with_valid_token_returns_claims(validator: EntraIdAccessTokenValidator) -> None:
    # Act
    claims = await validator.validate(make_token(roles=["user", "admin"]))

    # Assert
    assert claims.oid == TEST_OID
    assert claims.email == TEST_EMAIL
    assert claims.name == TEST_NAME
    assert claims.roles == ("user", "admin")


async def test_validate_without_preferred_username_uses_email_claim(
    validator: EntraIdAccessTokenValidator,
) -> None:
    claims = await validator.validate(make_token(remove=("preferred_username",), email="ana@acme.com"))

    assert claims.email == "ana@acme.com"


async def test_validate_without_email_claims_raises_missing_identity(
    validator: EntraIdAccessTokenValidator,
) -> None:
    token = make_token(remove=("preferred_username", "email"))

    assert await _rejection(validator, token) is TokenRejectionReason.MISSING_IDENTITY


async def test_validate_without_oid_raises_missing_identity(validator: EntraIdAccessTokenValidator) -> None:
    assert await _rejection(validator, make_token(remove=("oid",))) is TokenRejectionReason.MISSING_IDENTITY


async def test_validate_with_hs256_token_raises_invalid_signature(
    validator: EntraIdAccessTokenValidator,
) -> None:
    token = make_hs256_token_with_public_key()

    assert await _rejection(validator, token) is TokenRejectionReason.INVALID_SIGNATURE


async def test_validate_with_scope_list_without_required_scope_raises_missing_scope(
    validator: EntraIdAccessTokenValidator,
) -> None:
    token = make_token(scp="User.Read openid")

    assert await _rejection(validator, token) is TokenRejectionReason.MISSING_SCOPE


async def test_validate_with_required_scope_among_others_returns_claims(
    validator: EntraIdAccessTokenValidator,
) -> None:
    claims = await validator.validate(make_token(scp="openid access_as_user"))

    assert claims.oid == TEST_OID


async def test_validate_with_unknown_kid_refreshes_jwks_at_most_once_per_interval(
    validator: EntraIdAccessTokenValidator, jwks_client: LocalJwksClient
) -> None:
    # Arrange: JWKS ya en caché y el último refresco fuera del intervalo mínimo
    await validator.validate(make_token())
    jwks_client._last_successful_fetch = time.monotonic() - JWKS_MIN_REFRESH_SECONDS - 1

    # Act
    first = await _rejection(validator, make_token(kid="kid-desconocido-1"))
    second = await _rejection(validator, make_token(kid="kid-desconocido-2"))

    # Assert: carga inicial + un único refresco forzado
    assert first is TokenRejectionReason.INVALID_SIGNATURE
    assert second is TokenRejectionReason.INVALID_SIGNATURE
    assert jwks_client.fetch_count == 2


async def test_validate_when_jwks_unreachable_raises_keys_unavailable() -> None:
    # Arrange
    jwks_client = LocalJwksClient(jwks_for(SIGNING_KEY))
    jwks_client.unavailable = True
    validator = EntraIdAccessTokenValidator(TEST_POLICY, jwks_client)

    # Act / Assert
    assert await _rejection(validator, make_token()) is TokenRejectionReason.KEYS_UNAVAILABLE


async def test_validate_with_expired_token_raises_expired(validator: EntraIdAccessTokenValidator) -> None:
    token = make_token(exp=int(time.time()) - 600)

    assert await _rejection(validator, token) is TokenRejectionReason.EXPIRED
