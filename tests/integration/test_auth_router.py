import re
import time

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from src.core.dependencies.auth import get_current_user, require_role
from src.domain.enums.user_role import UserRole
from tests.conftest import ALLOWED_ORIGIN
from tests.support.tokens import (
    FOREIGN_KEY,
    OTHER_API_CLIENT_ID,
    OTHER_TENANT_ID,
    TEN_MINUTES,
    TEST_EMAIL,
    TEST_NAME,
    TEST_OID,
    make_token,
)

pytestmark = pytest.mark.integration

ME_URL = "/api/v1/auth/me"
ADMIN_ONLY_URL = "/api/v1/test-admin-only"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _assert_unauthorized(client: TestClient, token: str) -> None:
    response = client.get(ME_URL, headers=_auth(token))
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json() == {"detail": "No autenticado"}


def test_get_me_with_valid_user_token_returns_200_with_user_role(client: TestClient) -> None:
    # Act
    response = client.get(ME_URL, headers=_auth(make_token(roles=["user"])))

    # Assert
    assert response.status_code == 200
    assert response.json() == {"oid": TEST_OID, "email": TEST_EMAIL, "name": TEST_NAME, "role": "user"}


def test_get_me_with_admin_and_user_roles_returns_admin_role(client: TestClient) -> None:
    response = client.get(ME_URL, headers=_auth(make_token(roles=["user", "admin"])))

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_get_me_without_authorization_header_returns_401(client: TestClient) -> None:
    response = client.get(ME_URL)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_get_me_with_expired_token_returns_401(client: TestClient) -> None:
    now = int(time.time())
    _assert_unauthorized(client, make_token(iat=now - 2 * TEN_MINUTES, exp=now - TEN_MINUTES))


def test_get_me_with_not_yet_valid_token_returns_401(client: TestClient) -> None:
    _assert_unauthorized(client, make_token(nbf=int(time.time()) + TEN_MINUTES))


def test_get_me_with_other_audience_token_returns_401(client: TestClient) -> None:
    _assert_unauthorized(client, make_token(aud=OTHER_API_CLIENT_ID))


def test_get_me_with_other_tenant_issuer_returns_401(client: TestClient) -> None:
    _assert_unauthorized(client, make_token(iss=f"https://login.microsoftonline.com/{OTHER_TENANT_ID}/v2.0"))


def test_get_me_with_token_signed_by_unknown_key_returns_401(client: TestClient) -> None:
    _assert_unauthorized(client, make_token(key=FOREIGN_KEY))


def test_get_me_without_access_as_user_scope_returns_401(client: TestClient) -> None:
    _assert_unauthorized(client, make_token(scp="User.Read"))


def test_get_me_with_malformed_token_returns_401(client: TestClient) -> None:
    _assert_unauthorized(client, "abc.def")


def test_get_me_without_roles_claim_returns_403(client: TestClient) -> None:
    response = client.get(ME_URL, headers=_auth(make_token(remove=("roles",))))

    assert response.status_code == 403
    assert response.json() == {"detail": "No tienes acceso a OneWatch"}


def test_get_me_with_unrecognized_role_returns_403(client: TestClient) -> None:
    response = client.get(ME_URL, headers=_auth(make_token(roles=["reader"])))

    assert response.status_code == 403


def _app_with_admin_only_route(app: FastAPI) -> FastAPI:
    router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_current_user)])

    @router.get("/test-admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
    async def admin_only() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return app


def test_require_role_admin_with_user_role_returns_403(app: FastAPI) -> None:
    # Arrange
    client = TestClient(_app_with_admin_only_route(app))

    # Act
    response = client.get(ADMIN_ONLY_URL, headers=_auth(make_token(roles=["user"])))

    # Assert
    assert response.status_code == 403


def test_require_role_admin_with_admin_role_returns_200(app: FastAPI) -> None:
    client = TestClient(_app_with_admin_only_route(app))

    response = client.get(ADMIN_ONLY_URL, headers=_auth(make_token(roles=["admin"])))

    assert response.status_code == 200


def test_all_api_v1_routes_without_token_return_401(app: FastAPI, client: TestClient) -> None:
    # Arrange: todas las operaciones publicadas bajo /api/v1
    operations = [
        (method.upper(), re.sub(r"\{[^}]+\}", "x", path))
        for path, methods in app.openapi()["paths"].items()
        if path.startswith("/api/v1")
        for method in methods
    ]
    assert operations

    # Act / Assert
    for method, path in operations:
        response = client.request(method, path)
        assert response.status_code == 401, f"{method} {path} no exige token"


def test_health_without_token_returns_200(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_preflight_from_allowed_origin_allows_authorization_header(client: TestClient) -> None:
    response = client.options(
        ME_URL,
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "authorization" in response.headers["access-control-allow-headers"].lower()
