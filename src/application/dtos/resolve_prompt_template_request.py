from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResolvePromptTemplateRequest:
    """Petición de resolución de plantilla por categoría e identificador de negocio (ESP-13)."""

    category: str
    identifier: str
