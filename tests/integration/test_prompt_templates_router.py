from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from tests.support.tokens import TEST_EMAIL, make_token

pytestmark = pytest.mark.integration

TEMPLATES_URL = "/api/v1/prompt-templates"


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(roles=['admin'])}"}


def _unique_category() -> str:
    return f"test-{uuid4().hex[:12]}"


def _create_payload(category: str, identifier: str = "generico") -> dict[str, object]:
    return {
        "category": category,
        "identifier": identifier,
        "name": "Genérico de prueba",
        "template": "texto: {texto}",
        "alert_keywords": [],
        "enabled": True,
    }


def test_create_prompt_template_endpoint_with_valid_token_returns_201(client: TestClient) -> None:
    category = _unique_category()

    response = client.post(TEMPLATES_URL, json=_create_payload(category), headers=_auth())

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == category
    assert body["version"] == 1
    assert body["created_by"] == TEST_EMAIL


def test_create_prompt_template_with_duplicated_identifier_returns_422_with_field(client: TestClient) -> None:
    category = _unique_category()
    client.post(TEMPLATES_URL, json=_create_payload(category), headers=_auth())

    response = client.post(TEMPLATES_URL, json=_create_payload(category), headers=_auth())

    assert response.status_code == 422
    assert response.json()["field"] == "identifier"


def test_delete_last_generico_of_category_returns_409(client: TestClient) -> None:
    category = _unique_category()
    created = client.post(TEMPLATES_URL, json=_create_payload(category), headers=_auth()).json()

    response = client.delete(f"{TEMPLATES_URL}/{created['id']}", headers=_auth())

    assert response.status_code == 409


def test_update_prompt_template_creates_new_version_and_keeps_history(client: TestClient) -> None:
    category = _unique_category()
    created = client.post(TEMPLATES_URL, json=_create_payload(category), headers=_auth()).json()

    response = client.put(
        f"{TEMPLATES_URL}/{created['id']}",
        json={"name": "Genérico editado", "template": "nuevo texto: {texto}", "alert_keywords": []},
        headers=_auth(),
    )

    assert response.status_code == 200
    assert response.json()["version"] == 2

    detail = client.get(f"{TEMPLATES_URL}/{created['id']}", headers=_auth()).json()
    assert [v["version"] for v in detail["versions"]] == [1]


def test_get_prompt_template_when_not_found_returns_404(client: TestClient) -> None:
    response = client.get(f"{TEMPLATES_URL}/{uuid4()}", headers=_auth())

    assert response.status_code == 404


def test_resolve_prompt_template_falls_back_to_generico(client: TestClient) -> None:
    category = _unique_category()
    client.post(TEMPLATES_URL, json=_create_payload(category, "generico"), headers=_auth())

    response = client.get(
        f"{TEMPLATES_URL}/resolve",
        params={"category": category, "identifier": "huggingface-blog"},
        headers=_auth(),
    )

    assert response.status_code == 200
    assert response.json()["identifier"] == "generico"
