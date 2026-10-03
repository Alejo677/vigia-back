import pytest

from src.core.exceptions.validation_exception import ValidationException
from src.domain.value_objects.prompt_template_key import PromptTemplateKey

pytestmark = pytest.mark.unit


def test_prompt_template_key_with_valid_slugs_creates_key() -> None:
    key = PromptTemplateKey(category="vigilancia", identifier="azure-updates")

    assert key.category == "vigilancia"
    assert key.identifier == "azure-updates"


def test_prompt_template_key_with_generico_identifier_is_generic() -> None:
    key = PromptTemplateKey(category="vigilancia", identifier="generico")

    assert key.is_generic() is True


def test_prompt_template_key_with_specific_identifier_is_not_generic() -> None:
    key = PromptTemplateKey(category="vigilancia", identifier="azure-updates")

    assert key.is_generic() is False


@pytest.mark.parametrize("category", ["Vigilancia", "vigilancia con espacios", "vigilancia_bad", ""])
def test_prompt_template_key_with_invalid_category_slug_raises_validation_exception(category: str) -> None:
    with pytest.raises(ValidationException) as exc_info:
        PromptTemplateKey(category=category, identifier="generico")

    assert exc_info.value.field == "category"


def test_prompt_template_key_with_invalid_identifier_slug_raises_validation_exception() -> None:
    with pytest.raises(ValidationException) as exc_info:
        PromptTemplateKey(category="vigilancia", identifier="Azure Updates")

    assert exc_info.value.field == "identifier"
