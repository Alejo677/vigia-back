import logging
from unittest.mock import AsyncMock

import pytest

from src.application.dtos.authenticate_user_request import AuthenticateUserRequest
from src.application.use_cases.authenticate_user_use_case import AuthenticateUserUseCase
from src.core.exceptions.authenticate_user_exception import AuthenticateUserException
from src.core.exceptions.forbidden_exception import ForbiddenException
from src.core.exceptions.unauthorized_exception import UnauthorizedException
from src.domain.enums.token_rejection_reason import TokenRejectionReason
from src.domain.enums.user_role import UserRole
from src.domain.interfaces.i_access_token_validator import IAccessTokenValidator
from src.domain.value_objects.access_token_claims import AccessTokenClaims
from src.infrastructure.auth.entra_id_token_validator_exception import EntraIdTokenValidatorException

pytestmark = pytest.mark.unit

RAW_TOKEN = "eyJhbGciOiJSUzI1NiJ9.secreto-que-no-debe-aparecer.firma"


def _use_case(validator: AsyncMock) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(validator)


def _validator_returning(*roles: str) -> AsyncMock:
    validator = AsyncMock(spec=IAccessTokenValidator)
    validator.validate.return_value = AccessTokenClaims(
        oid="oid-1", email="ana@acme.com", name="Ana", roles=roles
    )
    return validator


def _validator_rejecting(reason: TokenRejectionReason) -> AsyncMock:
    validator = AsyncMock(spec=IAccessTokenValidator)
    validator.validate.side_effect = EntraIdTokenValidatorException(reason)
    return validator


async def test_authenticate_user_with_valid_token_returns_user_with_role() -> None:
    # Arrange
    use_case = _use_case(_validator_returning("user"))

    # Act
    user = await use_case.execute(AuthenticateUserRequest(bearer_token=RAW_TOKEN))

    # Assert
    assert user.role is UserRole.USER
    assert user.oid == "oid-1"


async def test_authenticate_user_without_token_raises_unauthorized_exception() -> None:
    validator = _validator_returning("user")

    with pytest.raises(UnauthorizedException) as exc:
        await _use_case(validator).execute(AuthenticateUserRequest(bearer_token=None))

    assert exc.value.reason is TokenRejectionReason.MISSING
    validator.validate.assert_not_called()


async def test_authenticate_user_when_validator_rejects_token_raises_unauthorized_exception() -> None:
    use_case = _use_case(_validator_rejecting(TokenRejectionReason.EXPIRED))

    with pytest.raises(UnauthorizedException) as exc:
        await use_case.execute(AuthenticateUserRequest(bearer_token=RAW_TOKEN))

    assert exc.value.reason is TokenRejectionReason.EXPIRED


async def test_authenticate_user_without_roles_raises_forbidden_exception() -> None:
    use_case = _use_case(_validator_returning())

    with pytest.raises(ForbiddenException):
        await use_case.execute(AuthenticateUserRequest(bearer_token=RAW_TOKEN))


async def test_authenticate_user_when_keys_unavailable_raises_authenticate_user_exception() -> None:
    use_case = _use_case(_validator_rejecting(TokenRejectionReason.KEYS_UNAVAILABLE))

    with pytest.raises(AuthenticateUserException):
        await use_case.execute(AuthenticateUserRequest(bearer_token=RAW_TOKEN))


async def test_authenticate_user_rejected_token_never_logs_token(caplog: pytest.LogCaptureFixture) -> None:
    # Arrange
    caplog.set_level(logging.DEBUG)
    use_case = _use_case(_validator_rejecting(TokenRejectionReason.INVALID_SIGNATURE))

    # Act
    with pytest.raises(UnauthorizedException):
        await use_case.execute(AuthenticateUserRequest(bearer_token=RAW_TOKEN))

    # Assert
    assert caplog.records
    for record in caplog.records:
        dumped = f"{record.getMessage()} {record.__dict__}"
        assert RAW_TOKEN not in dumped
        assert "secreto-que-no-debe-aparecer" not in dumped
        assert "Bearer" not in dumped


def test_authenticate_user_request_repr_masks_token() -> None:
    request = AuthenticateUserRequest(bearer_token=RAW_TOKEN)

    assert RAW_TOKEN not in repr(request)
    assert RAW_TOKEN not in str(request)
