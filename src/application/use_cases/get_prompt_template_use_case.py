from src.application.dtos.get_prompt_template_request import GetPromptTemplateRequest
from src.application.dtos.prompt_template_response import PromptTemplateDetailResponse
from src.core.exceptions.not_found_exception import NotFoundException
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository


class GetPromptTemplateUseCase:
    """Detalle de una plantilla de prompt, con su versión vigente y el historial anterior (ESP-13)."""

    def __init__(self, templates: IPromptTemplateRepository) -> None:
        self._templates = templates

    async def execute(self, request: GetPromptTemplateRequest) -> PromptTemplateDetailResponse:
        """Busca la plantilla y su historial de versiones anteriores.

        Args:
            request: identificador de la plantilla.

        Returns:
            Detalle de la plantilla con su historial.

        Raises:
            NotFoundException: no existe una plantilla con ese `id` (404).
        """
        template = await self._templates.get_by_id(request.id)
        if template is None:
            raise NotFoundException(f"No existe la plantilla de prompt '{request.id}'")
        versions = await self._templates.list_versions(request.id)
        return PromptTemplateDetailResponse.from_entity_with_history(template, versions)
