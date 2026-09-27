import pytest

from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.enums.user_role import UserRole
from src.domain.value_objects.access_token_claims import AccessTokenClaims

pytestmark = pytest.mark.unit


def _claims(*roles: str) -> AccessTokenClaims:
    return AccessTokenClaims(oid="oid-1", email="ana@acme.com", name="Ana", roles=roles)


def test_from_claims_with_admin_and_user_roles_returns_admin() -> None:
    # Act
    user = AuthenticatedUser.from_claims(_claims("user", "admin"))

    # Assert
    assert user.role is UserRole.ADMIN


def test_from_claims_with_only_user_role_returns_user() -> None:
    user = AuthenticatedUser.from_claims(_claims("user"))

    assert user.role is UserRole.USER
    assert user.email == "ana@acme.com"


def test_from_claims_with_unrecognized_roles_raises_value_error() -> None:
    with pytest.raises(ValueError):
        AuthenticatedUser.from_claims(_claims("reader"))
