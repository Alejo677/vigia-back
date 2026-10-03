import logging

from src.application.dtos.delete_prompt_template_request import DeletePromptTemplateRequest
from src.core.exceptions.conflict_exception import ConflictException
from src.core.exceptions.delete_prompt_template_exception import DeletePromptTemplateException
from src.core.exceptions.not_found_exception import NotFoundException
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository

logger = logging.getLogger(__name__)


class DeletePromptTemplateUseCase:
    """Elimina físicamente una plantilla, salvo que sea el único `generico` activo de su categoría
    (ESP-13, Regla 3; Constitución §2.4 permite el borrado físico aquí).
    """

    def __init__(self, templates: IPromptTemplateRepository) -> None:
        self._templates = templates

    async def execute(self, request: DeletePromptTemplateRequest) -> None:
        """Elimina la plantilla y su historial de versiones.

        Args:
            request: identificador de la plantilla a eliminar.

        Raises:
            NotFoundException: no existe una plantilla con ese `id` (404).
            ConflictException: la categoría se quedaría sin plantilla de respaldo (409).
            DeletePromptTemplateException: error no atribuible al cliente.
        """
        try:
            current = await self._templates.get_by_id(request.id)
        except Exception as e:
            logger.error(
                "❌ Error al leer plantilla de prompt",
                extra={"template_id": str(request.id), "error": str(e)},
            )
            raise DeletePromptTemplateException("No se pudo eliminar la plantilla") from None
        if current is None:
            raise NotFoundException(f"No existe la plantilla de prompt '{request.id}'")
        if current.enabled and current.key.is_generic():
            active_generics = await self._templates.count_active_with_identifier_in_category(
                current.key.category, current.key.identifier
            )
            if active_generics <= 1:
                raise ConflictException(
                    f"La categoría '{current.key.category}' se quedaría sin plantilla de respaldo"
                )
        try:
            await self._templates.delete(request.id)
        except Exception as e:
            logger.error(
                "❌ Error al eliminar plantilla de prompt",
                extra={"template_id": str(request.id), "error": str(e)},
            )
            raise DeletePromptTemplateException("No se pudo eliminar la plantilla") from None
        logger.info("🗑️ Plantilla de prompt eliminada", extra={"template_id": str(request.id)})
