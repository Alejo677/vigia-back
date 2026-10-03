import os

import asyncpg
import pytest_asyncio

from src.infrastructure.postgresql.repositories.postgresql_prompt_template_repository import (
    PostgreSQLPromptTemplateRepository,
)

# El proyecto aún no tiene un runner de migraciones (scripts/DB/migrations/ está vacío):
# se aplica aquí el esquema de scripts/DB/DB.sql de forma idempotente para que la suite de
# integración funcione contra una BD de desarrollo recién creada.
_SCHEMA = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS prompt_template (
    id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    category          VARCHAR(64)   NOT NULL,
    identifier        VARCHAR(64)   NOT NULL DEFAULT 'generico',
    name              VARCHAR(200)  NOT NULL,
    template          TEXT          NOT NULL,
    alert_keywords    TEXT[],
    version           INTEGER       NOT NULL DEFAULT 1,
    enabled           BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    created_by        VARCHAR(100)  NOT NULL,
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_by        VARCHAR(100)  NOT NULL,
    UNIQUE (category, identifier)
);

CREATE TABLE IF NOT EXISTS prompt_template_version (
    id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id       UUID          NOT NULL REFERENCES prompt_template(id) ON DELETE CASCADE,
    version           INTEGER       NOT NULL,
    name              VARCHAR(200)  NOT NULL,
    template          TEXT          NOT NULL,
    alert_keywords    TEXT[],
    created_at        TIMESTAMPTZ   NOT NULL,
    created_by        VARCHAR(100)  NOT NULL,
    UNIQUE (template_id, version)
);
"""


@pytest_asyncio.fixture
async def prompt_template_repository() -> PostgreSQLPromptTemplateRepository:
    dsn = os.environ["DATABASE_URL"]
    connection = await asyncpg.connect(dsn=dsn)
    try:
        await connection.execute(_SCHEMA)
    finally:
        await connection.close()
    return PostgreSQLPromptTemplateRepository(dsn)
