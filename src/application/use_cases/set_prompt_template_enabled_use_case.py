import logging

from src.application.dtos.prompt_template_response import PromptTemplateResponse
from src.application.dtos.set_prompt_template_enabled_request import SetPromptTemplateEnabledRequest
from src.core.exceptions.conflict_exception import ConflictException
from src.core.exceptions.not_found_exception import NotFoundException
from src.core.exceptions.set_prompt_template_enabled_exception import SetPromptTemplateEnabledException
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository

logger = logging.getLogger(__name__)


class SetPromptTemplateEnabledUseCase:
    """Activa o desactiva una plantilla, sin dejar sin respaldo a su categoría (ESP-13, Regla 3)."""

    def __init__(self, templates: IPromptTemplateRepository) -> None:
        self._templates = templates

    async def execute(self, request: SetPromptTemplateEnabledRequest) -> PromptTemplateResponse:
        """Cambia el estado activo de la plantilla, salvo que sea el único `generico` activo.

        Args:
            request: identificador de la plantilla y estado deseado.

        Returns:
            Plantilla actualizada.

        Raises:
            NotFoundException: no existe una plantilla con ese `id` (404).
            ConflictException: la categoría se quedaría sin plantilla de respaldo (409).
            SetPromptTemplateEnabledException: error no atribuible al cliente.
        """
        if request.id is None:
            raise ValueError("request.id es obligatorio para cambiar el estado de una plantilla")
        try:
            current = await self._templates.get_by_id(request.id)
        except Exception as e:
            logger.error(
                "❌ Error al leer plantilla de prompt",
                extra={"template_id": str(request.id), "error": str(e)},
            )
            raise SetPromptTemplateEnabledException("No se pudo cambiar el estado de la plantilla") from None
        if current is None:
            raise NotFoundException(f"No existe la plantilla de prompt '{request.id}'")
        if not request.enabled and current.key.is_generic():
            active_generics = await self._templates.count_active_with_identifier_in_category(
                current.key.category, current.key.identifier
            )
            if active_generics <= 1:
                raise ConflictException(
                    f"La categoría '{current.key.category}' se quedaría sin plantilla de respaldo"
                )
        try:
            updated = await self._templates.update_enabled(request.id, request.enabled, request.updated_by)
        except Exception as e:
            logger.error(
                "❌ Error al cambiar estado de plantilla de prompt",
                extra={"template_id": str(request.id), "error": str(e)},
            )
            raise SetPromptTemplateEnabledException("No se pudo cambiar el estado de la plantilla") from None
        logger.info(
            "📝 Estado de plantilla de prompt actualizado",
            extra={"template_id": str(request.id), "enabled": request.enabled},
        )
        return PromptTemplateResponse.from_entity(updated)
