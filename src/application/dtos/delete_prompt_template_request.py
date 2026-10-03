from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class DeletePromptTemplateRequest:
    """Petición de eliminación física de una plantilla de prompt (ESP-13, Constitución §2.4)."""

    id: UUID
