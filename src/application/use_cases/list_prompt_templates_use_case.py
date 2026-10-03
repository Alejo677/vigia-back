from src.application.dtos.list_prompt_templates_request import (
    ListPromptTemplatesRequest,
    PromptTemplateListResponse,
)
from src.application.dtos.prompt_template_response import PromptTemplateResponse
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository


class ListPromptTemplatesUseCase:
    """Listado paginado de plantillas de prompt, con el `generico` de cada categoría destacado (ESP-13)."""

    def __init__(self, templates: IPromptTemplateRepository) -> None:
        self._templates = templates

    async def execute(self, request: ListPromptTemplatesRequest) -> PromptTemplateListResponse:
        """Lista las plantillas según los filtros y la paginación pedidos.

        Args:
            request: página, tamaño, búsqueda, filtro de categoría y ordenación.

        Returns:
            Página de plantillas y el total de resultados.
        """
        items, total = await self._templates.list(
            page=request.page,
            page_size=request.page_size,
            search=request.search,
            category=request.category,
            sort_by=request.sort_by,
            sort_dir=request.sort_dir,
        )
        return PromptTemplateListResponse(
            items=[PromptTemplateResponse.from_entity(t) for t in items], total=total
        )
