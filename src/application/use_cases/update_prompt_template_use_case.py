import logging
from dataclasses import replace

from src.application.dtos.prompt_template_response import PromptTemplateResponse
from src.application.dtos.update_prompt_template_request import UpdatePromptTemplateRequest
from src.core.exceptions.not_found_exception import NotFoundException
from src.core.exceptions.update_prompt_template_exception import UpdatePromptTemplateException
from src.core.exceptions.validation_exception import ValidationException
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository

logger = logging.getLogger(__name__)


class UpdatePromptTemplateUseCase:
    """Modifica el texto de una plantilla: crea una versión nueva y conserva el historial (Regla 5)."""

    def __init__(self, templates: IPromptTemplateRepository) -> None:
        self._templates = templates

    async def execute(self, request: UpdatePromptTemplateRequest) -> PromptTemplateResponse:
        """Guarda la versión actual en el historial y actualiza la plantilla a la nueva versión.

        Args:
            request: datos nuevos de la plantilla (identificador y categoría no se tocan).

        Returns:
            Plantilla actualizada.

        Raises:
            NotFoundException: no existe una plantilla con ese `id` (404).
            UpdatePromptTemplateException: error no atribuible al cliente.
        """
        if request.id is None:
            raise ValueError("request.id es obligatorio para modificar una plantilla")
        try:
            current = await self._templates.get_by_id(request.id)
        except Exception as e:
            logger.error(
                "❌ Error al leer plantilla de prompt",
                extra={"template_id": str(request.id), "error": str(e)},
            )
            raise UpdatePromptTemplateException("No se pudo modificar la plantilla de prompt") from None
        if current is None:
            raise NotFoundException(f"No existe la plantilla de prompt '{request.id}'")
        try:
            next_version = replace(
                current,
                name=request.name,
                template=request.template,
                alert_keywords=request.alert_keywords,
                updated_by=request.updated_by,
                version=current.version + 1,
            )
        except ValidationException:
            raise
        try:
            updated = await self._templates.save_new_version(next_version)
        except Exception as e:
            logger.error(
                "❌ Error al modificar plantilla de prompt",
                extra={"template_id": str(request.id), "error": str(e)},
            )
            raise UpdatePromptTemplateException("No se pudo modificar la plantilla de prompt") from None
        logger.info(
            "📝 Plantilla de prompt actualizada",
            extra={
                "category": updated.key.category,
                "identifier": updated.key.identifier,
                "version": updated.version,
            },
        )
        return PromptTemplateResponse.from_entity(updated)
