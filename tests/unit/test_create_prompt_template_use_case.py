from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.create_prompt_template_request import CreatePromptTemplateRequest
from src.application.use_cases.create_prompt_template_use_case import CreatePromptTemplateUseCase
from src.core.exceptions.create_prompt_template_exception import CreatePromptTemplateException
from src.core.exceptions.validation_exception import ValidationException
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository

pytestmark = pytest.mark.unit


def _saved(template: PromptTemplate) -> PromptTemplate:
    fields = {k: v for k, v in vars(template).items() if k != "id"}
    return PromptTemplate(id=uuid4(), **fields)


def _request(**overrides: object) -> CreatePromptTemplateRequest:
    defaults: dict[str, object] = {
        "category": "facturacion",
        "identifier": "generico",
        "name": "Genérico de facturación",
        "template": "Clasifica: {texto}",
        "created_by": "ana@acme.com",
    }
    return CreatePromptTemplateRequest(**(defaults | overrides))


async def test_create_prompt_template_with_new_category_and_generico_creates_version_1_active() -> None:
    # Arrange
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.exists_with_key.return_value = False
    repo.save.side_effect = _saved
    use_case = CreatePromptTemplateUseCase(repo)

    # Act
    result = await use_case.execute(_request())

    # Assert
    assert result.version == 1
    assert result.enabled is True
    repo.save.assert_awaited_once()


async def test_create_prompt_template_specific_identifier_coexists_with_generico() -> None:
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.exists_with_key.return_value = False
    repo.save.side_effect = _saved
    use_case = CreatePromptTemplateUseCase(repo)

    result = await use_case.execute(_request(category="vigilancia", identifier="azure-updates"))

    assert result.identifier == "azure-updates"
    assert result.category == "vigilancia"


async def test_create_prompt_template_with_duplicated_key_raises_validation_exception() -> None:
    # Arrange
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.exists_with_key.return_value = True
    use_case = CreatePromptTemplateUseCase(repo)

    # Act / Assert
    with pytest.raises(ValidationException) as exc_info:
        await use_case.execute(_request(category="vigilancia", identifier="azure-updates"))
    assert exc_info.value.field == "identifier"
    repo.save.assert_not_called()


@pytest.mark.parametrize("category", ["Vigilancia", "con espacios"])
async def test_create_prompt_template_with_invalid_slug_raises_validation_exception(category: str) -> None:
    repo = AsyncMock(spec=IPromptTemplateRepository)
    use_case = CreatePromptTemplateUseCase(repo)

    with pytest.raises(ValidationException):
        await use_case.execute(_request(category=category))
    repo.exists_with_key.assert_not_called()


async def test_create_prompt_template_when_repository_fails_raises_create_prompt_template_exception() -> None:
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.exists_with_key.return_value = False
    repo.save.side_effect = RuntimeError("boom")
    use_case = CreatePromptTemplateUseCase(repo)

    with pytest.raises(CreatePromptTemplateException):
        await use_case.execute(_request())
