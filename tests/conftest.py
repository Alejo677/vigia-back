import os

# src.main crea la app al importarse y exige la configuración de Entra ID
os.environ.setdefault("ENTRA_TENANT_ID", "11111111-1111-1111-1111-111111111111")
os.environ.setdefault("ENTRA_API_CLIENT_ID", "33333333-3333-3333-3333-333333333333")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:4200")

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.configuration.settings import Settings
from src.core.dependencies.auth import get_access_token_validator
from src.infrastructure.auth.entra_id_access_token_validator import EntraIdAccessTokenValidator
from src.main import create_app
from tests.support.tokens import (
    SIGNING_KEY,
    TEST_API_CLIENT_ID,
    TEST_POLICY,
    TEST_TENANT_ID,
    LocalJwksClient,
    jwks_for,
)

ALLOWED_ORIGIN = "http://localhost:4200"


@pytest.fixture
def jwks_client() -> LocalJwksClient:
    return LocalJwksClient(jwks_for(SIGNING_KEY))


@pytest.fixture
def validator(jwks_client: LocalJwksClient) -> EntraIdAccessTokenValidator:
    """Validador real (firma incluida) contra el JWKS local de pruebas."""
    return EntraIdAccessTokenValidator(TEST_POLICY, jwks_client)


@pytest.fixture
def app(validator: EntraIdAccessTokenValidator) -> FastAPI:
    settings = Settings(
        entra_tenant_id=TEST_TENANT_ID,
        entra_api_client_id=TEST_API_CLIENT_ID,
        cors_allowed_origins=ALLOWED_ORIGIN,
    )
    application = create_app(settings)
    application.dependency_overrides[get_access_token_validator] = lambda: validator
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
