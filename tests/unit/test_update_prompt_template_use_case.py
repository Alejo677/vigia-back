from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.update_prompt_template_request import UpdatePromptTemplateRequest
from src.application.use_cases.update_prompt_template_use_case import UpdatePromptTemplateUseCase
from src.core.exceptions.not_found_exception import NotFoundException
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.domain.value_objects.prompt_template_key import PromptTemplateKey

pytestmark = pytest.mark.unit


def _template(template_id: object, version: int = 2) -> PromptTemplate:
    return PromptTemplate(
        id=template_id,
        key=PromptTemplateKey(category="vigilancia", identifier="azure-updates"),
        name="Azure updates",
        template="texto viejo: {texto}",
        version=version,
        created_by="ana",
        updated_by="ana",
    )


async def test_update_prompt_template_changing_text_creates_new_version() -> None:
    # Arrange
    template_id = uuid4()
    current = _template(template_id, version=2)
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = current
    repo.save_new_version.side_effect = lambda t: t
    use_case = UpdatePromptTemplateUseCase(repo)

    # Act
    result = await use_case.execute(
        UpdatePromptTemplateRequest(
            id=template_id, name="Azure updates", template="texto nuevo: {texto}", updated_by="ana"
        )
    )

    # Assert
    assert result.version == 3
    saved_template = repo.save_new_version.await_args.args[0]
    assert saved_template.template == "texto nuevo: {texto}"


async def test_update_prompt_template_cannot_change_identifier() -> None:
    template_id = uuid4()
    current = _template(template_id)
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = current
    repo.save_new_version.side_effect = lambda t: t
    use_case = UpdatePromptTemplateUseCase(repo)

    result = await use_case.execute(
        UpdatePromptTemplateRequest(
            id=template_id, name="Nuevo nombre", template="texto: {texto}", updated_by="ana"
        )
    )

    assert result.identifier == "azure-updates"
    assert result.category == "vigilancia"


async def test_update_prompt_template_when_not_found_raises_not_found_exception() -> None:
    repo = AsyncMock(spec=IPromptTemplateRepository)
    repo.get_by_id.return_value = None
    use_case = UpdatePromptTemplateUseCase(repo)

    with pytest.raises(NotFoundException):
        await use_case.execute(
            UpdatePromptTemplateRequest(id=uuid4(), name="X", template="texto: {texto}", updated_by="ana")
        )
