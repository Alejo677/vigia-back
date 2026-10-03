from dataclasses import dataclass

from pydantic import BaseModel

from src.application.dtos.prompt_template_response import PromptTemplateResponse

DEFAULT_PAGE_SIZE = 20
DEFAULT_SORT_BY = "category"
DEFAULT_SORT_DIR = "asc"


@dataclass(frozen=True, slots=True)
class ListPromptTemplatesRequest:
    """Petición de listado paginado de plantillas de prompt (ESP-13)."""

    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    search: str | None = None
    category: str | None = None
    sort_by: str = DEFAULT_SORT_BY
    sort_dir: str = DEFAULT_SORT_DIR


class PromptTemplateListResponse(BaseModel):
    """Página de plantillas de prompt, con el `generico` de cada categoría destacado al inicio."""

    items: list[PromptTemplateResponse]
    total: int
