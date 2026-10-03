-- DDL de OneWatch. Único dueño del esquema, compartido por back/ y func/ (CONSTITUCION.md §3.2).
-- Sin lógica de negocio (triggers, procedimientos ni funciones): solo restricciones de integridad
-- (Constitución §2.7).

-- gen_random_uuid() es nativa desde PostgreSQL 13: no requiere la extensión pgcrypto
-- (que Azure PostgreSQL Flexible Server no permite por defecto).

-- ESP-13: Maestro de plantillas de prompt

CREATE TABLE prompt_template (
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

-- Historial de versiones anteriores de una plantilla (ESP-13, Regla 5; no está en la
-- descripción técnica de la especificación, ver docs/plan/ESP-13.md §7). Se guarda una fila
-- con el estado previo justo antes de sobrescribir `prompt_template` en cada edición.
CREATE TABLE prompt_template_version (
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
