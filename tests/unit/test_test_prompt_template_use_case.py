from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.test_prompt_template_request import TestPromptTemplateRequest
from src.application.use_cases.test_prompt_template_use_case import TestPromptTemplateUseCase
from src.core.exceptions.not_found_exception import NotFoundException
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.domain.value_objects.prompt_template_key import PromptTemplateKey

pytestmark = pytest.mark.unit


async def test_test_prompt_template_use_case_renders_without_calling_llm_or_persisting() -> None:
    # Arrange
    template_id = uuid4()
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = PromptTemplate(
        id=template_id,
        key=PromptTemplateKey(category="vigilancia", identifier="generico"),
        name="Genérico",
        template="Título: {titulo}",
        created_by="seed",
        updated_by="seed",
    )
    use_case = TestPromptTemplateUseCase(repo)

    # Act
    result = await use_case.execute(
        TestPromptTemplateRequest(id=template_id, sample_values={"titulo": "Nuevo modelo publicado"})
    )

    # Assert
    assert result.rendered_text == "Título: Nuevo modelo publicado"
    repo.save.assert_not_called()
    repo.save_new_version.assert_not_called()


async def test_test_prompt_template_use_case_when_not_found_raises_not_found_exception() -> None:
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = None
    use_case = TestPromptTemplateUseCase(repo)

    with pytest.raises(NotFoundException):
        await use_case.execute(TestPromptTemplateRequest(id=uuid4()))
