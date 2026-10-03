from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GetPromptTemplateRequest:
    """Petición de detalle de una plantilla de prompt, con su historial de versiones (ESP-13)."""

    id: UUID
