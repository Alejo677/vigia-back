from uuid import uuid4

import pytest

from src.domain.entities.prompt_template import PromptTemplate
from src.domain.value_objects.prompt_template_key import PromptTemplateKey
from src.infrastructure.postgresql.repositories.postgresql_prompt_template_repository import (
    PostgreSQLPromptTemplateRepository,
)

pytestmark = pytest.mark.integration


def _unique_category() -> str:
    return f"test-{uuid4().hex[:12]}"


def _template(category: str, identifier: str = "generico") -> PromptTemplate:
    return PromptTemplate(
        id=None,
        key=PromptTemplateKey(category=category, identifier=identifier),
        name="Genérico de prueba",
        template="texto: {texto}",
        created_by="test@onewatch.dev",
        updated_by="test@onewatch.dev",
    )


async def test_save_and_get_by_id_roundtrip(
    prompt_template_repository: PostgreSQLPromptTemplateRepository,
) -> None:
    category = _unique_category()

    created = await prompt_template_repository.save(_template(category))
    fetched = await prompt_template_repository.get_by_id(created.id)

    assert fetched is not None
    assert fetched.key.category == category
    assert fetched.version == 1
    assert fetched.enabled is True


async def test_exists_with_key_after_create_returns_true(
    prompt_template_repository: PostgreSQLPromptTemplateRepository,
) -> None:
    category = _unique_category()
    key = PromptTemplateKey(category=category, identifier="generico")

    assert await prompt_template_repository.exists_with_key(key) is False
    await prompt_template_repository.save(_template(category))
    assert await prompt_template_repository.exists_with_key(key) is True


async def test_get_active_by_key_ignores_disabled_templates(
    prompt_template_repository: PostgreSQLPromptTemplateRepository,
) -> None:
    category = _unique_category()
    template = _template(category)
    template.enabled = False
    await prompt_template_repository.save(template)

    result = await prompt_template_repository.get_active_by_key(
        PromptTemplateKey(category=category, identifier="generico")
    )

    assert result is None


async def test_save_new_version_keeps_previous_version_in_history(
    prompt_template_repository: PostgreSQLPromptTemplateRepository,
) -> None:
    # Arrange: plantilla en versión 2 (alta + una edición previa)
    category = _unique_category()
    created = await prompt_template_repository.save(_template(category))
    from dataclasses import replace

    v2 = replace(created, name="Genérico v2", template="texto v2: {texto}", version=2)
    await prompt_template_repository.save_new_version(v2)

    # Act: nueva edición a versión 3
    v3 = replace(v2, name="Genérico v3", template="texto v3: {texto}", version=3)
    updated = await prompt_template_repository.save_new_version(v3)

    # Assert
    assert updated.version == 3
    history = await prompt_template_repository.list_versions(created.id)
    versions_in_history = {v.version for v in history}
    assert versions_in_history == {1, 2}


async def test_count_active_with_identifier_in_category_counts_only_enabled(
    prompt_template_repository: PostgreSQLPromptTemplateRepository,
) -> None:
    category = _unique_category()
    await prompt_template_repository.save(_template(category, "generico"))

    count = await prompt_template_repository.count_active_with_identifier_in_category(category, "generico")

    assert count == 1


async def test_delete_removes_template_and_its_version_history(
    prompt_template_repository: PostgreSQLPromptTemplateRepository,
) -> None:
    from dataclasses import replace

    category = _unique_category()
    created = await prompt_template_repository.save(_template(category))
    await prompt_template_repository.save_new_version(replace(created, template="v2: {texto}", version=2))

    await prompt_template_repository.delete(created.id)

    assert await prompt_template_repository.get_by_id(created.id) is None
    assert await prompt_template_repository.list_versions(created.id) == []


async def test_list_orders_generico_first_within_each_category(
    prompt_template_repository: PostgreSQLPromptTemplateRepository,
) -> None:
    category = _unique_category()
    await prompt_template_repository.save(_template(category, "azure-updates"))
    await prompt_template_repository.save(_template(category, "generico"))
    await prompt_template_repository.save(_template(category, "huggingface-blog"))

    items, total = await prompt_template_repository.list(
        page=1, page_size=10, search=None, category=category, sort_by="category", sort_dir="asc"
    )

    assert total == 3
    assert items[0].key.identifier == "generico"
