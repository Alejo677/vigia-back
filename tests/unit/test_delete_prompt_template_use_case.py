from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.delete_prompt_template_request import DeletePromptTemplateRequest
from src.application.use_cases.delete_prompt_template_use_case import DeletePromptTemplateUseCase
from src.core.exceptions.conflict_exception import ConflictException
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.domain.value_objects.prompt_template_key import PromptTemplateKey

pytestmark = pytest.mark.unit


def _generic_template(template_id: object, enabled: bool = True) -> PromptTemplate:
    return PromptTemplate(
        id=template_id,
        key=PromptTemplateKey(category="vigilancia", identifier="generico"),
        name="Genérico",
        template="texto: {texto}",
        enabled=enabled,
        created_by="seed",
        updated_by="seed",
    )


async def test_delete_prompt_template_when_last_generico_active_in_category_is_denied() -> None:
    # Arrange
    template_id = uuid4()
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = _generic_template(template_id)
    repo.count_active_with_identifier_in_category.return_value = 1
    use_case = DeletePromptTemplateUseCase(repo)

    # Act / Assert
    with pytest.raises(ConflictException):
        await use_case.execute(DeletePromptTemplateRequest(id=template_id))
    repo.delete.assert_not_called()


async def test_delete_prompt_template_when_second_generico_of_category_exists_succeeds() -> None:
    template_id = uuid4()
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = _generic_template(template_id)
    repo.count_active_with_identifier_in_category.return_value = 2
    use_case = DeletePromptTemplateUseCase(repo)

    await use_case.execute(DeletePromptTemplateRequest(id=template_id))

    repo.delete.assert_awaited_once_with(template_id)


async def test_delete_prompt_template_when_specific_identifier_does_not_check_generico_count() -> None:
    template_id = uuid4()
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = PromptTemplate(
        id=template_id,
        key=PromptTemplateKey(category="vigilancia", identifier="azure-updates"),
        name="Azure updates",
        template="texto: {texto}",
        created_by="seed",
        updated_by="seed",
    )
    use_case = DeletePromptTemplateUseCase(repo)

    await use_case.execute(DeletePromptTemplateRequest(id=template_id))

    repo.count_active_with_identifier_in_category.assert_not_called()
    repo.delete.assert_awaited_once_with(template_id)
