from dataclasses import dataclass

from src.domain.value_objects.slug import validate_slug

GENERIC_IDENTIFIER = "generico"


@dataclass(frozen=True, slots=True)
class PromptTemplateKey:
    """Clave de negocio de una plantilla de prompt: categoría + identificador (ESP-13, Regla 2)."""

    category: str
    identifier: str

    def __post_init__(self) -> None:
        validate_slug(self.category, "category")
        validate_slug(self.identifier, "identifier")

    def is_generic(self) -> bool:
        """Indica si esta clave es la plantilla de respaldo de su categoría.

        Returns:
            True si el identificador es `generico`.
        """
        return self.identifier == GENERIC_IDENTIFIER
