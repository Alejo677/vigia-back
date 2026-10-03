from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.resolve_prompt_template_request import ResolvePromptTemplateRequest
from src.application.use_cases.resolve_prompt_template_use_case import ResolvePromptTemplateUseCase
from src.core.exceptions.resolve_prompt_template_exception import ResolvePromptTemplateException
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.domain.value_objects.prompt_template_key import PromptTemplateKey

pytestmark = pytest.mark.unit


def _template(category: str, identifier: str) -> PromptTemplate:
    return PromptTemplate(
        id=uuid4(),
        key=PromptTemplateKey(category=category, identifier=identifier),
        name=f"{category}/{identifier}",
        template="texto: {texto}",
        created_by="seed",
        updated_by="seed",
    )


async def test_resolve_prompt_template_by_specific_identifier_returns_specific() -> None:
    # Arrange
    specific = _template("vigilancia", "azure-updates")
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_active_by_key.return_value = specific
    use_case = ResolvePromptTemplateUseCase(repo)

    # Act
    result = await use_case.execute(
        ResolvePromptTemplateRequest(category="vigilancia", identifier="azure-updates")
    )

    # Assert
    assert result.identifier == "azure-updates"
    repo.get_active_by_key.assert_awaited_once()


async def test_resolve_prompt_template_falls_back_to_generico_when_specific_missing() -> None:
    # Arrange
    generic = _template("vigilancia", "generico")
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_active_by_key.side_effect = [None, generic]
    use_case = ResolvePromptTemplateUseCase(repo)

    # Act
    result = await use_case.execute(
        ResolvePromptTemplateRequest(category="vigilancia", identifier="huggingface-blog")
    )

    # Assert
    assert result.identifier == "generico"
    assert repo.get_active_by_key.await_count == 2


async def test_resolve_prompt_template_without_any_active_template_raises_configuration_error() -> None:
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_active_by_key.return_value = None
    use_case = ResolvePromptTemplateUseCase(repo)

    with pytest.raises(ResolvePromptTemplateException):
        await use_case.execute(
            ResolvePromptTemplateRequest(category="vigilancia", identifier="huggingface-blog")
        )
