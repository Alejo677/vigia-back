from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.set_prompt_template_enabled_request import SetPromptTemplateEnabledRequest
from src.application.use_cases.set_prompt_template_enabled_use_case import SetPromptTemplateEnabledUseCase
from src.core.exceptions.conflict_exception import ConflictException
from src.core.exceptions.not_found_exception import NotFoundException
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.domain.value_objects.prompt_template_key import PromptTemplateKey

pytestmark = pytest.mark.unit


def _generic_template(template_id: object) -> PromptTemplate:
    return PromptTemplate(
        id=template_id,
        key=PromptTemplateKey(category="vigilancia", identifier="generico"),
        name="Genérico",
        template="texto: {texto}",
        created_by="seed",
        updated_by="seed",
    )


async def test_set_prompt_template_enabled_false_when_last_generico_active_in_category_is_denied() -> None:
    # Arrange
    template_id = uuid4()
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = _generic_template(template_id)
    repo.count_active_with_identifier_in_category.return_value = 1
    use_case = SetPromptTemplateEnabledUseCase(repo)

    # Act / Assert
    with pytest.raises(ConflictException):
        await use_case.execute(
            SetPromptTemplateEnabledRequest(enabled=False, id=template_id, updated_by="ana")
        )
    repo.update_enabled.assert_not_called()


async def test_set_prompt_template_enabled_false_when_second_generico_of_category_exists_succeeds() -> None:
    template_id = uuid4()
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = _generic_template(template_id)
    repo.count_active_with_identifier_in_category.return_value = 2
    repo.update_enabled.return_value = _generic_template(template_id)
    use_case = SetPromptTemplateEnabledUseCase(repo)

    await use_case.execute(SetPromptTemplateEnabledRequest(enabled=False, id=template_id, updated_by="ana"))

    repo.update_enabled.assert_awaited_once_with(template_id, False, "ana")


async def test_set_prompt_template_enabled_when_template_not_found_raises_not_found_exception() -> None:
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = None
    use_case = SetPromptTemplateEnabledUseCase(repo)

    with pytest.raises(NotFoundException):
        await use_case.execute(SetPromptTemplateEnabledRequest(enabled=False, id=uuid4(), updated_by="ana"))
