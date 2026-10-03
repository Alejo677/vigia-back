from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.core.exceptions.validation_exception import ValidationException
from src.domain.value_objects.prompt_template_key import PromptTemplateKey

MAX_NAME_LENGTH = 200


@dataclass
class PromptTemplate:
    """Plantilla de prompt versionada, resuelta por categoría + identificador (ESP-13)."""

    id: UUID | None
    key: PromptTemplateKey
    name: str
    template: str
    alert_keywords: list[str] = field(default_factory=list)
    version: int = 1
    enabled: bool = True
    created_at: datetime | None = None
    created_by: str = ""
    updated_at: datetime | None = None
    updated_by: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValidationException("El nombre es obligatorio", "name")
        if len(self.name) > MAX_NAME_LENGTH:
            raise ValidationException(f"El nombre no puede superar {MAX_NAME_LENGTH} caracteres", "name")
        if not self.template.strip():
            raise ValidationException("La plantilla de prompt es obligatoria", "template")
