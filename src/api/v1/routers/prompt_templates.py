from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from src.application.dtos.create_prompt_template_request import CreatePromptTemplateRequest
from src.application.dtos.delete_prompt_template_request import DeletePromptTemplateRequest
from src.application.dtos.get_prompt_template_request import GetPromptTemplateRequest
from src.application.dtos.list_prompt_templates_request import (
    DEFAULT_PAGE_SIZE,
    DEFAULT_SORT_BY,
    DEFAULT_SORT_DIR,
    ListPromptTemplatesRequest,
    PromptTemplateListResponse,
)
from src.application.dtos.prompt_template_response import PromptTemplateDetailResponse, PromptTemplateResponse
from src.application.dtos.resolve_prompt_template_request import ResolvePromptTemplateRequest
from src.application.dtos.set_prompt_template_enabled_request import SetPromptTemplateEnabledRequest
from src.application.dtos.test_prompt_template_request import (
    TestPromptTemplateRequest,
    TestPromptTemplateResponse,
)
from src.application.dtos.update_prompt_template_request import UpdatePromptTemplateRequest
from src.core.dependencies.auth import CurrentUser
from src.core.dependencies.prompt_templates import (
    CreatePromptTemplateUseCaseDep,
    DeletePromptTemplateUseCaseDep,
    GetPromptTemplateUseCaseDep,
    ListPromptTemplatesUseCaseDep,
    ResolvePromptTemplateUseCaseDep,
    SetPromptTemplateEnabledUseCaseDep,
    TestPromptTemplateUseCaseDep,
    UpdatePromptTemplateUseCaseDep,
)
from src.core.exceptions.create_prompt_template_exception import CreatePromptTemplateException
from src.core.exceptions.delete_prompt_template_exception import DeletePromptTemplateException
from src.core.exceptions.resolve_prompt_template_exception import ResolvePromptTemplateException
from src.core.exceptions.set_prompt_template_enabled_exception import SetPromptTemplateEnabledException
from src.core.exceptions.test_prompt_template_exception import TestPromptTemplateException
from src.core.exceptions.update_prompt_template_exception import UpdatePromptTemplateException

router = APIRouter(prefix="/prompt-templates", tags=["Prompt templates"])


@router.get("/resolve", response_model=PromptTemplateResponse)
async def resolve_prompt_template(
    category: str, identifier: str, _: CurrentUser, use_case: ResolvePromptTemplateUseCaseDep
) -> PromptTemplateResponse:
    """Resolución interna: plantilla del identificador o, en su defecto, la `generico` de la categoría."""
    try:
        return await use_case.execute(ResolvePromptTemplateRequest(category=category, identifier=identifier))
    except ResolvePromptTemplateException as e:
        raise HTTPException(status_code=500, detail=e.message) from None


@router.get("", response_model=PromptTemplateListResponse)
async def list_prompt_templates(
    _: CurrentUser,
    use_case: ListPromptTemplatesUseCaseDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=200),
    search: str | None = None,
    category: str | None = None,
    sort_by: str = DEFAULT_SORT_BY,
    sort_dir: str = DEFAULT_SORT_DIR,
) -> PromptTemplateListResponse:
    """Listado paginado con búsqueda y filtro por categoría."""
    return await use_case.execute(
        ListPromptTemplatesRequest(
            page=page,
            page_size=page_size,
            search=search,
            category=category,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
    )


@router.get("/{template_id}", response_model=PromptTemplateDetailResponse)
async def get_prompt_template(
    template_id: UUID, _: CurrentUser, use_case: GetPromptTemplateUseCaseDep
) -> PromptTemplateDetailResponse:
    """Detalle de una plantilla, con su historial de versiones anteriores."""
    return await use_case.execute(GetPromptTemplateRequest(id=template_id))


@router.post("", response_model=PromptTemplateResponse, status_code=201)
async def create_prompt_template(
    request: CreatePromptTemplateRequest, user: CurrentUser, use_case: CreatePromptTemplateUseCaseDep
) -> PromptTemplateResponse:
    """Alta de una plantilla en versión 1 y activa."""
    try:
        return await use_case.execute(request.with_user(user.email))
    except CreatePromptTemplateException as e:
        raise HTTPException(status_code=502, detail=e.message) from None


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: UUID,
    request: UpdatePromptTemplateRequest,
    user: CurrentUser,
    use_case: UpdatePromptTemplateUseCaseDep,
) -> PromptTemplateResponse:
    """Modifica el texto de la plantilla: crea una nueva versión y conserva el historial."""
    try:
        return await use_case.execute(request.with_id_and_user(template_id, user.email))
    except UpdatePromptTemplateException as e:
        raise HTTPException(status_code=502, detail=e.message) from None


@router.patch("/{template_id}/enabled", response_model=PromptTemplateResponse)
async def set_prompt_template_enabled(
    template_id: UUID,
    request: SetPromptTemplateEnabledRequest,
    user: CurrentUser,
    use_case: SetPromptTemplateEnabledUseCaseDep,
) -> PromptTemplateResponse:
    """Activa o desactiva la plantilla, salvo que sea el único `generico` activo de su categoría."""
    try:
        return await use_case.execute(request.with_id_and_user(template_id, user.email))
    except SetPromptTemplateEnabledException as e:
        raise HTTPException(status_code=502, detail=e.message) from None


@router.post("/{template_id}/test", response_model=TestPromptTemplateResponse)
async def test_prompt_template(
    template_id: UUID,
    request: TestPromptTemplateRequest,
    _: CurrentUser,
    use_case: TestPromptTemplateUseCaseDep,
) -> TestPromptTemplateResponse:
    """Renderiza la plantilla con los valores de ejemplo recibidos, sin llamar al LLM ni guardar nada."""
    try:
        return await use_case.execute(request.with_id(template_id))
    except TestPromptTemplateException as e:
        raise HTTPException(status_code=502, detail=e.message) from None


@router.delete("/{template_id}", status_code=204)
async def delete_prompt_template(
    template_id: UUID, _: CurrentUser, use_case: DeletePromptTemplateUseCaseDep
) -> None:
    """Eliminación física, salvo que sea el único `generico` activo de su categoría."""
    try:
        await use_case.execute(DeletePromptTemplateRequest(id=template_id))
    except DeletePromptTemplateException as e:
        raise HTTPException(status_code=502, detail=e.message) from None
