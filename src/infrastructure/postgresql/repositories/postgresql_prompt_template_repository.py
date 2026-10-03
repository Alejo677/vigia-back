from uuid import UUID

import asyncpg

from src.domain.entities.prompt_template import PromptTemplate
from src.domain.entities.prompt_template_version import PromptTemplateVersion
from src.domain.interfaces.i_prompt_template_repository import IPromptTemplateRepository
from src.domain.value_objects.prompt_template_key import GENERIC_IDENTIFIER, PromptTemplateKey
from src.infrastructure.postgresql.base_repository import PostgreSQLBaseRepository

_ALLOWED_SORT_COLUMNS = {"category", "identifier", "name", "version", "enabled", "updated_at"}


class PostgreSQLPromptTemplateRepository(PostgreSQLBaseRepository, IPromptTemplateRepository):
    """Repositorio de plantillas de prompt sobre PostgreSQL (ESP-13)."""

    async def save(self, template: PromptTemplate) -> PromptTemplate:
        row = await self.execute_query(
            """
            INSERT INTO prompt_template
                (category, identifier, name, template, alert_keywords, version, enabled,
                 created_by, updated_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, created_at, updated_at
            """,
            template.key.category,
            template.key.identifier,
            template.name,
            template.template,
            template.alert_keywords,
            template.version,
            template.enabled,
            template.created_by,
            template.updated_by,
        )
        return self._with_row(template, row[0])

    async def save_new_version(self, template: PromptTemplate) -> PromptTemplate:
        async with self.transaction() as connection:
            previous = await connection.fetchrow(
                "SELECT version, name, template, alert_keywords, updated_at, updated_by "
                "FROM prompt_template WHERE id = $1",
                template.id,
            )
            await connection.execute(
                """
                INSERT INTO prompt_template_version
                    (template_id, version, name, template, alert_keywords, created_at, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                template.id,
                previous["version"],
                previous["name"],
                previous["template"],
                previous["alert_keywords"],
                previous["updated_at"],
                previous["updated_by"],
            )
            row = await connection.fetchrow(
                """
                UPDATE prompt_template
                SET name = $2, template = $3, alert_keywords = $4, version = $5,
                    updated_by = $6, updated_at = now()
                WHERE id = $1
                RETURNING created_at, updated_at
                """,
                template.id,
                template.name,
                template.template,
                template.alert_keywords,
                template.version,
                template.updated_by,
            )
        return self._with_row(template, row)

    async def update_enabled(self, template_id: UUID, enabled: bool, updated_by: str) -> PromptTemplate:
        row = await self.execute_query(
            """
            UPDATE prompt_template
            SET enabled = $2, updated_by = $3, updated_at = now()
            WHERE id = $1
            RETURNING category, identifier, name, template, alert_keywords, version, enabled,
                      created_at, created_by, updated_at, updated_by
            """,
            template_id,
            enabled,
            updated_by,
        )
        return self._to_entity(row[0])

    async def delete(self, template_id: UUID) -> None:
        await self.execute_update("DELETE FROM prompt_template WHERE id = $1", template_id)

    async def get_by_id(self, template_id: UUID) -> PromptTemplate | None:
        rows = await self.execute_query(
            """
            SELECT id, category, identifier, name, template, alert_keywords, version, enabled,
                   created_at, created_by, updated_at, updated_by
            FROM prompt_template
            WHERE id = $1
            """,
            template_id,
        )
        return self._to_entity(rows[0]) if rows else None

    async def get_active_by_key(self, key: PromptTemplateKey) -> PromptTemplate | None:
        rows = await self.execute_query(
            """
            SELECT id, category, identifier, name, template, alert_keywords, version, enabled,
                   created_at, created_by, updated_at, updated_by
            FROM prompt_template
            WHERE category = $1 AND identifier = $2 AND enabled = TRUE
            """,
            key.category,
            key.identifier,
        )
        return self._to_entity(rows[0]) if rows else None

    async def exists_with_key(self, key: PromptTemplateKey) -> bool:
        rows = await self.execute_query(
            "SELECT 1 FROM prompt_template WHERE category = $1 AND identifier = $2",
            key.category,
            key.identifier,
        )
        return len(rows) > 0

    async def count_active_with_identifier_in_category(self, category: str, identifier: str) -> int:
        rows = await self.execute_query(
            "SELECT count(*) AS n FROM prompt_template "
            "WHERE category = $1 AND identifier = $2 AND enabled = TRUE",
            category,
            identifier,
        )
        return int(rows[0]["n"])

    async def list_versions(self, template_id: UUID) -> list[PromptTemplateVersion]:
        rows = await self.execute_query(
            """
            SELECT template_id, version, name, template, alert_keywords, created_at, created_by
            FROM prompt_template_version
            WHERE template_id = $1
            ORDER BY version DESC
            """,
            template_id,
        )
        return [
            PromptTemplateVersion(
                template_id=row["template_id"],
                version=row["version"],
                name=row["name"],
                template=row["template"],
                alert_keywords=list(row["alert_keywords"] or []),
                created_at=row["created_at"],
                created_by=row["created_by"],
            )
            for row in rows
        ]

    async def list(
        self,
        page: int,
        page_size: int,
        search: str | None,
        category: str | None,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[list[PromptTemplate], int]:
        column = sort_by if sort_by in _ALLOWED_SORT_COLUMNS else "category"
        direction = "DESC" if sort_dir.lower() == "desc" else "ASC"
        conditions = []
        args: list[str | int] = []
        if search:
            args.append(f"%{search.lower()}%")
            conditions.append(
                f"(lower(category) LIKE ${len(args)} OR lower(identifier) LIKE ${len(args)} "
                f"OR lower(name) LIKE ${len(args)})"
            )
        if category:
            args.append(category)
            conditions.append(f"category = ${len(args)}")
        # where_clause solo referencia placeholders ($1, $2…) resueltos vía *args; category/identifier
        # nunca se interpolan como texto. `column` y `direction` vienen de un conjunto cerrado
        # (_ALLOWED_SORT_COLUMNS y "ASC"/"DESC"), no de entrada libre del cliente.
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        total_rows = await self.execute_query(
            f"SELECT count(*) AS n FROM prompt_template {where_clause}", *args  # noqa: S608
        )
        total = int(total_rows[0]["n"])
        args.extend([page_size, (page - 1) * page_size])
        rows = await self.execute_query(
            f"""
            SELECT id, category, identifier, name, template, alert_keywords, version, enabled,
                   created_at, created_by, updated_at, updated_by
            FROM prompt_template
            {where_clause}
            ORDER BY category ASC, (identifier != '{GENERIC_IDENTIFIER}') ASC, {column} {direction}
            LIMIT ${len(args) - 1} OFFSET ${len(args)}
            """,  # noqa: S608
            *args,
        )
        return [self._to_entity(row) for row in rows], total

    @staticmethod
    def _to_entity(row: asyncpg.Record) -> PromptTemplate:
        return PromptTemplate(
            id=row["id"],
            key=PromptTemplateKey(category=row["category"], identifier=row["identifier"]),
            name=row["name"],
            template=row["template"],
            alert_keywords=list(row["alert_keywords"] or []),
            version=row["version"],
            enabled=row["enabled"],
            created_at=row["created_at"],
            created_by=row["created_by"],
            updated_at=row["updated_at"],
            updated_by=row["updated_by"],
        )

    @staticmethod
    def _with_row(template: PromptTemplate, row: asyncpg.Record) -> PromptTemplate:
        template.id = row["id"] if "id" in row.keys() else template.id
        template.created_at = row["created_at"]
        template.updated_at = row["updated_at"]
        return template
