import re

from src.core.exceptions.validation_exception import ValidationException

SLUG_PATTERN = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def validate_slug(value: str, field: str) -> None:
    """Valida que un valor tenga formato slug (minúsculas, números y guiones).

    Reutilizada por cualquier campo con este formato (categoría e identificador
    de plantilla de prompt, código de fuente de noticias, etc.).

    Args:
        value: valor a validar.
        field: nombre del campo, para el error de validación.

    Raises:
        ValidationException: si `value` no cumple el formato slug.
    """
    if not SLUG_PATTERN.fullmatch(value):
        raise ValidationException("Debe tener formato slug (minúsculas, números y guiones)", field)
