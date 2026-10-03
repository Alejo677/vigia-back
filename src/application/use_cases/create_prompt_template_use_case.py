import logging

from src.application.dtos.create_prompt_template_request import CreatePromptTemplateRequest
from src.application.dtos.prompt_template_response import PromptTemplateResponse
from src.core.exceptions.create_prompt_template_exception import CreatePromptTemplateException
from src.core.exceptions.validation_exception import ValidationException
from src.domain.entities.prompt_template import PromptTemplate
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.domain.value_objects.prompt_template_key import PromptTemplateKey

logger = logging.getLogger(__name__)


class CreatePromptTemplateUseCase:
    """Alta de una plantilla de prompt en versión 1 y activa (ESP-13, Regla 2)."""

    def __init__(self, templates: IPromptTemplateRepository) -> None:
        self._templates = templates

    async def execute(self, request: CreatePromptTemplateRequest) -> PromptTemplateResponse:
        """Crea la plantilla tras validar que la categoría e identificador no estén en uso.

        Args:
            request: datos de la nueva plantilla.

        Returns:
            Plantilla creada.

        Raises:
            ValidationException: categoría e identificador ya existen (campo `identifier`).
            CreatePromptTemplateException: error no atribuible al cliente.
        """
        key = PromptTemplateKey(category=request.category, identifier=request.identifier)
        try:
            if await self._templates.exists_with_key(key):
                raise ValidationException(
                    f"Ya existe una plantilla '{key.category}' / '{key.identifier}'", "identifier"
                )
            template = PromptTemplate(
                id=None,
                key=key,
                name=request.name,
                template=request.template,
                alert_keywords=request.alert_keywords,
                enabled=request.enabled,
                created_by=request.created_by,
                updated_by=request.created_by,
            )
            created = await self._templates.save(template)
        except ValidationException:
            raise
        except Exception as e:
            logger.error(
                "❌ Error al crear plantilla de prompt",
                extra={"category": request.category, "identifier": request.identifier, "error": str(e)},
            )
            raise CreatePromptTemplateException("No se pudo crear la plantilla de prompt") from None
        logger.info(
            "📝 Plantilla de prompt creada",
            extra={"category": key.category, "identifier": key.identifier, "version": created.version},
        )
        return PromptTemplateResponse.from_entity(created)
