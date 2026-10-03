from src.application.dtos.prompt_template_response import PromptTemplateResponse
from src.application.dtos.resolve_prompt_template_request import ResolvePromptTemplateRequest
from src.core.exceptions.resolve_prompt_template_exception import ResolvePromptTemplateException
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.domain.value_objects.prompt_template_key import GENERIC_IDENTIFIER, PromptTemplateKey


class ResolvePromptTemplateUseCase:
    """Resuelve la plantilla activa de una categoría e identificador de negocio (ESP-13).

    Busca primero la plantilla activa exacta; si no existe, la `generico` activa de la categoría.
    Es el punto de entrada que usan las funcionalidades consumidoras (ESP-08).
    """

    def __init__(self, templates: IPromptTemplateRepository) -> None:
        self._templates = templates

    async def execute(self, request: ResolvePromptTemplateRequest) -> PromptTemplateResponse:
        """Resuelve la plantilla a usar para la categoría e identificador dados.

        Args:
            request: categoría e identificador de negocio (p. ej. el código de una fuente).

        Returns:
            Plantilla específica, o la `generico` de la categoría si no hay una específica.

        Raises:
            ResolvePromptTemplateException: ninguna de las dos existe activa (Caso 3, error de configuración).
        """
        specific_key = PromptTemplateKey(category=request.category, identifier=request.identifier)
        template = await self._templates.get_active_by_key(specific_key)
        if template is not None:
            return PromptTemplateResponse.from_entity(template)
        if not specific_key.is_generic():
            generic_key = PromptTemplateKey(category=request.category, identifier=GENERIC_IDENTIFIER)
            template = await self._templates.get_active_by_key(generic_key)
            if template is not None:
                return PromptTemplateResponse.from_entity(template)
        raise ResolvePromptTemplateException(
            f"La categoría '{request.category}' no tiene ninguna plantilla activa "
            f"ni '{request.identifier}' ni '{GENERIC_IDENTIFIER}'"
        )
