from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.application.use_cases.create_prompt_template_use_case import CreatePromptTemplateUseCase
from src.application.use_cases.delete_prompt_template_use_case import DeletePromptTemplateUseCase
from src.application.use_cases.get_prompt_template_use_case import GetPromptTemplateUseCase
from src.application.use_cases.list_prompt_templates_use_case import ListPromptTemplatesUseCase
from src.application.use_cases.resolve_prompt_template_use_case import ResolvePromptTemplateUseCase
from src.application.use_cases.set_prompt_template_enabled_use_case import SetPromptTemplateEnabledUseCase
from src.application.use_cases.test_prompt_template_use_case import TestPromptTemplateUseCase
from src.application.use_cases.update_prompt_template_use_case import UpdatePromptTemplateUseCase
from src.core.configuration.settings import get_settings
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.infrastructure.postgresql.repositories.postgresql_prompt_template_repository import (
    PostgreSQLPromptTemplateRepository,
)


@lru_cache
def get_prompt_template_repository() -> IPromptTemplateRepository:
    """Repositorio único por proceso, para compartir el pool de conexiones.

    Returns:
        Repositorio de plantillas de prompt.
    """
    return PostgreSQLPromptTemplateRepository(get_settings().database_url)


PromptTemplateRepository = Annotated[IPromptTemplateRepository, Depends(get_prompt_template_repository)]


def get_create_prompt_template_use_case(
    templates: PromptTemplateRepository,
) -> CreatePromptTemplateUseCase:
    """Provider del caso de uso de alta de plantillas."""
    return CreatePromptTemplateUseCase(templates)


def get_update_prompt_template_use_case(
    templates: PromptTemplateRepository,
) -> UpdatePromptTemplateUseCase:
    """Provider del caso de uso de modificación de plantillas."""
    return UpdatePromptTemplateUseCase(templates)


def get_set_prompt_template_enabled_use_case(
    templates: PromptTemplateRepository,
) -> SetPromptTemplateEnabledUseCase:
    """Provider del caso de uso de activar/desactivar plantillas."""
    return SetPromptTemplateEnabledUseCase(templates)


def get_delete_prompt_template_use_case(
    templates: PromptTemplateRepository,
) -> DeletePromptTemplateUseCase:
    """Provider del caso de uso de eliminación de plantillas."""
    return DeletePromptTemplateUseCase(templates)


def get_test_prompt_template_use_case(
    templates: PromptTemplateRepository,
) -> TestPromptTemplateUseCase:
    """Provider del caso de uso de prueba de plantillas."""
    return TestPromptTemplateUseCase(templates)


def get_list_prompt_templates_use_case(
    templates: PromptTemplateRepository,
) -> ListPromptTemplatesUseCase:
    """Provider del caso de uso de listado de plantillas."""
    return ListPromptTemplatesUseCase(templates)


def get_get_prompt_template_use_case(
    templates: PromptTemplateRepository,
) -> GetPromptTemplateUseCase:
    """Provider del caso de uso de detalle de una plantilla."""
    return GetPromptTemplateUseCase(templates)


def get_resolve_prompt_template_use_case(
    templates: PromptTemplateRepository,
) -> ResolvePromptTemplateUseCase:
    """Provider del caso de uso de resolución de plantillas, usado por otras funcionalidades (ESP-08)."""
    return ResolvePromptTemplateUseCase(templates)


CreatePromptTemplateUseCaseDep = Annotated[
    CreatePromptTemplateUseCase, Depends(get_create_prompt_template_use_case)
]
UpdatePromptTemplateUseCaseDep = Annotated[
    UpdatePromptTemplateUseCase, Depends(get_update_prompt_template_use_case)
]
SetPromptTemplateEnabledUseCaseDep = Annotated[
    SetPromptTemplateEnabledUseCase, Depends(get_set_prompt_template_enabled_use_case)
]
DeletePromptTemplateUseCaseDep = Annotated[
    DeletePromptTemplateUseCase, Depends(get_delete_prompt_template_use_case)
]
TestPromptTemplateUseCaseDep = Annotated[
    TestPromptTemplateUseCase, Depends(get_test_prompt_template_use_case)
]
ListPromptTemplatesUseCaseDep = Annotated[
    ListPromptTemplatesUseCase, Depends(get_list_prompt_templates_use_case)
]
GetPromptTemplateUseCaseDep = Annotated[GetPromptTemplateUseCase, Depends(get_get_prompt_template_use_case)]
ResolvePromptTemplateUseCaseDep = Annotated[
    ResolvePromptTemplateUseCase, Depends(get_resolve_prompt_template_use_case)
]
