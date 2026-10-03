import logging

from src.application.dtos.test_prompt_template_request import (
    TestPromptTemplateRequest,
    TestPromptTemplateResponse,
)
from src.core.exceptions.not_found_exception import NotFoundException
from src.core.exceptions.test_prompt_template_exception import TestPromptTemplateException
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository

logger = logging.getLogger(__name__)


class TestPromptTemplateUseCase:
    """Renderiza una plantilla con valores de ejemplo, sin llamar al LLM ni guardar nada (ESP-13)."""

    def __init__(self, templates: IPromptTemplateRepository) -> None:
        self._templates = templates

    async def execute(self, request: TestPromptTemplateRequest) -> TestPromptTemplateResponse:
        """Sustituye los placeholders de la plantilla por los valores de ejemplo recibidos.

        Args:
            request: identificador de la plantilla y valores de ejemplo por placeholder.

        Returns:
            Texto final renderizado.

        Raises:
            NotFoundException: no existe una plantilla con ese `id` (404).
            TestPromptTemplateException: error no atribuible al cliente al renderizar.
        """
        if request.id is None:
            raise ValueError("request.id es obligatorio para probar una plantilla")
        try:
            template = await self._templates.get_by_id(request.id)
        except Exception as e:
            logger.error(
                "❌ Error al leer plantilla de prompt",
                extra={"template_id": str(request.id), "error": str(e)},
            )
            raise TestPromptTemplateException("No se pudo probar la plantilla") from None
        if template is None:
            raise NotFoundException(f"No existe la plantilla de prompt '{request.id}'")
        try:
            rendered = template.template.format(**request.sample_values)
        except (KeyError, IndexError, ValueError) as e:
            raise TestPromptTemplateException(f"No se pudo renderizar la plantilla: {e}") from None
        return TestPromptTemplateResponse(rendered_text=rendered)
