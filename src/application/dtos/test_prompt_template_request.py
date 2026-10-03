from dataclasses import dataclass, field, replace
from uuid import UUID

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class TestPromptTemplateRequest:
    """Petición de renderizado de prueba: no llama al LLM ni persiste nada (ESP-13). `id` lo
    completa el router a partir de la ruta.
    """

    sample_values: dict[str, str] = field(default_factory=dict)
    id: UUID | None = None

    def with_id(self, template_id: UUID) -> "TestPromptTemplateRequest":
        """Devuelve una copia con el identificador tomado de la ruta.

        Args:
            template_id: identificador de la plantilla a probar.

        Returns:
            Copia de la petición con `id` completado.
        """
        return replace(self, id=template_id)


class TestPromptTemplateResponse(BaseModel):
    """Texto final resultante de renderizar la plantilla con los valores de ejemplo."""

    rendered_text: str
