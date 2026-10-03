from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PromptTemplateVersion:
    """Entrada de solo lectura del historial de versiones anteriores de una plantilla (ESP-13, Regla 5)."""

    template_id: UUID
    version: int
    name: str
    template: str
    alert_keywords: list[str] = field(default_factory=list)
    created_at: datetime | None = None
    created_by: str = ""
