# Análisis de Implementación — ESP-13: Maestro de plantillas de prompt

Estado: Aprobado

Fuente: File (`./docs/Spec/Especificaciones.md`)

---

## 1. Descripción funcional

**Historia de usuario**

Como responsable de vigilancia tecnológica, quiero mantener plantillas de prompt para LLM organizadas por categoría e identificador, con una plantilla genérica de respaldo por categoría, para poder personalizar el prompt de una fuente, un tipo de noticia o cualquier otro caso de uso del sistema sin tocar código, y reutilizar el mismo maestro en varias funcionalidades.

**Propósito**

Centralizar la configuración de los prompts que usan los distintos procesos con LLM del sistema, para poder ajustarlos sin desplegar código y sin duplicar esta gestión en cada funcionalidad. No pertenece a la vigilancia de noticias: es infraestructura común, aunque su primer consumidor sea ESP-08.

**UX** (prototipo: https://dimly-woven-86209062.figma.site → menú **Maestros › Plantillas de prompt**; sin URL de Figma con `node-id`, no aplica sección de diseño)

Tres vistas: listado (tabla paginada con Categoría, Identificador, Nombre, Versión, Activa, Última modificación; búsqueda libre; filtro por categoría; orden por defecto categoría+identificador; la plantilla `generico` de cada categoría destacada al inicio del grupo; botón **Nueva plantilla**; acciones Ver detalle / Editar / Probar / Activar-Desactivar / Eliminar), formulario de alta y edición (Categoría con autocompletar, Identificador con `generico` preseleccionado y sugerencia de sustituirlo, Nombre, Plantilla de prompt, Palabras de alerta, Activa; botón **Probar prompt** que renderiza sin llamar al LLM ni guardar; Guardar/Cancelar) y detalle (campos en lectura, versión vigente, historial de versiones anteriores, auditoría; accesos a Editar/Probar/Activar-Desactivar/Eliminar).

**Flujo principal (alta)**: Nueva plantilla → elegir/escribir categoría → identificador propuesto `generico`, sustituible → completar plantilla → Guardar → validación → se crea en versión 1 → confirmación.

**Flujo de resolución (consumo por otra funcionalidad)**: categoría + identificador de negocio → busca plantilla activa exacta → si no existe, busca la `generico` activa de la categoría → devuelve la encontrada o error de configuración si ninguna existe.

**Reglas de negocio**

1. Campos obligatorios: categoría, identificador, nombre, plantilla de prompt.
2. Categoría + identificador es única; ambas con formato slug (minúsculas, números y guiones). El identificador es inmutable tras el alta.
3. Cada categoría debe tener siempre una plantilla `generico` activa; no se puede eliminar ni desactivar si es la única con ese identificador en la categoría.
4. Al crear, el identificador se propone como `generico`, pero se recomienda sustituirlo salvo que sea la primera plantilla de una categoría nueva.
5. Editar el texto crea una nueva versión; se conserva el histórico de versiones anteriores.
6. Palabras de alerta y placeholders son de uso libre, sin formato impuesto por este maestro.
7. Cada alta y modificación registra fecha y usuario.
8. Todas las validaciones son de aplicación, nunca de base de datos.

**Excepciones**: (1) categoría+identificador duplicados → no se guarda, error en el campo identificador; (2) intento de eliminar/desactivar el único `generico` de una categoría → no se permite, se explica el motivo; (3) funcionalidad consumidora pide una categoría sin `generico` activo ni específica → error de configuración (no debería ocurrir si se respeta la Regla 3).

**Fuera de alcance de ESP-13**: placeholders predefinidos a nivel de plataforma, generación automática de plantillas, comparación A/B, traducción/localización.

**Notas de interfaz**: se entrega con la plantilla semilla `vigilancia`/`generico` que usa ESP-08 mientras no existan plantillas específicas.

## 2. Criterios de aceptación

1. Alta de la primera plantilla de una categoría nueva: dado que no existe ninguna plantilla de la categoría "facturacion", al crear una con categoría "facturacion" e identificador "generico", se crea en versión 1 y activa.
2. Alta de una plantilla específica: dada la categoría "vigilancia" con su "generico" activa, al crear una con identificador "azure-updates", ambas coexisten activas en la misma categoría.
3. Identificador duplicado en la misma categoría: dada "vigilancia"/"azure-updates" existente, al intentar crear otra igual, el sistema no guarda y muestra el error en el campo identificador.
4. Resolución por identificador específico: dadas "vigilancia"/"generico" y "vigilancia"/"azure-updates" activas, al pedir "vigilancia"/"azure-updates", se recibe esa plantilla.
5. Resolución por respaldo genérico: dada solo "vigilancia"/"generico" activa, al pedir "vigilancia"/"huggingface-blog", se recibe "generico".
6. Intento de eliminar el único genérico de una categoría: dada "vigilancia"/"generico" como única con ese identificador, al intentar eliminarla, el sistema no la elimina y explica que la categoría quedaría sin plantilla de respaldo.
7. Nueva versión al editar: dada "vigilancia"/"azure-updates" en versión 2, al editar su texto y guardar, queda en versión 3 y la versión 2 se conserva en el historial.

## 3. Análisis de impacto

### 3.1 Riesgos de regresión

Ninguno. No hay ningún proceso, endpoint ni entidad implementados todavía que dependan de plantillas de prompt (ESP-08, su primer consumidor, no está implementado). No se ha encontrado código, tests ni configuración previos sobre `prompt_template`.

### 3.2 TODOs a resolver

Ninguno. No hay comentarios `# TODO: ... ESP-13` en `back/`, `func/` ni `front/`.

### 3.3 Cambios transversales

ESP-13 es la **primera funcionalidad del backend que persiste datos**: hoy no existe pool de PostgreSQL, `DB.sql`, driver de base de datos en `pyproject.toml` ni variable `DATABASE_URL`. Este plan incluye construir esa base compartida (conexión, repositorio base, `DB.sql`) porque toda funcionalidad futura con persistencia la reutilizará; no es exclusiva de plantillas de prompt.

- **Esquema de BD**: nuevo `scripts/DB/DB.sql` con la tabla `prompt_template` (según la descripción técnica de ESP-13) y una tabla adicional `prompt_template_version` **no descrita en la especificación técnica**, necesaria para cumplir la Regla 5 y el Criterio 7 (conservar el histórico de versiones anteriores) — ver decisión en el punto 7.
- **Semilla**: `scripts/DB/seed/prompt_templates.sql` con la plantilla `vigilancia`/`generico` (Notas de interfaz).
- **Dependencias** (`pyproject.toml`): añadir driver de PostgreSQL asíncrono (`asyncpg`).
- **Variables de entorno** (`.env.example`, `src/core/configuration/settings.py`): añadir `DATABASE_URL` (y parámetros de pool si aplica).
- **Excepciones genéricas compartidas**: no existen aún `NotFoundException`, `ConflictException` ni `ValidationException` en `core/exceptions/` (el único CRUD implementado hasta ahora es `auth`, que no las necesita). Se crean aquí porque `_python.md` las da por existentes de forma genérica y las reutilizará cualquier maestro futuro (fuentes de noticias, catálogo…).
- **Frontend**: `features/` y `shared/components/` están vacíos; ESP-13 es la primera feature de negocio, así que este plan incluye los componentes compartidos mínimos (tabla paginada, modal de confirmación, etiqueta de estado) que reutilizarán `news-sources` y el resto de maestros, además de la primera entrada real del menú lateral (`shell.component.html`) y la primera ruta lazy en `app.routes.ts`.

## 4. Plan de implementación — Backend

| Capa | Archivo | Acción | Descripción |
|---|---|---|---|
| Enums/Excepciones | `src/core/exceptions/not_found_exception.py` | Crear | `NotFoundException(message)`, genérica, para recursos inexistentes (404) |
| Enums/Excepciones | `src/core/exceptions/conflict_exception.py` | Crear | `ConflictException(message)`, genérica (409) |
| Enums/Excepciones | `src/core/exceptions/validation_exception.py` | Crear | `ValidationException(message, field)`, genérica, para errores de campo (422) |
| Entidades | `src/domain/value_objects/slug.py` | Crear | `SLUG_PATTERN` (regex compartido minúsculas/números/guiones) y `validate_slug(value, field)` reutilizable por categoría e identificador (y por futuras specs con formato slug) |
| Entidades | `src/domain/value_objects/prompt_template_key.py` | Crear | VO `PromptTemplateKey(category, identifier)` inmutable, valida slug de ambos campos en `__post_init__` |
| Entidades | `src/domain/entities/prompt_template.py` | Crear | Entidad `PromptTemplate`: id, category, identifier, name, template, alert_keywords, version, enabled, created_at, created_by, updated_at, updated_by; valida en `__post_init__` (Regla 1: nombre y template no vacíos; longitud máx. 200 del nombre) |
| Entidades | `src/domain/entities/prompt_template_version.py` | Crear | Entidad de solo lectura para una entrada del historial: template_id, version, name, template, alert_keywords, created_at, created_by |
| Modelos de resultado | `src/application/dtos/prompt_template_response.py` | Crear | `PromptTemplateResponse` (listado/detalle) y `PromptTemplateVersionResponse` (item de historial) |
| Modelos de resultado | `src/application/dtos/create_prompt_template_request.py` | Crear | `CreatePromptTemplateRequest` (category, identifier, name, template, alert_keywords, enabled, created_by) |
| Modelos de resultado | `src/application/dtos/update_prompt_template_request.py` | Crear | `UpdatePromptTemplateRequest` (id, name, template, alert_keywords, updated_by) — identifier no editable (Regla 2) |
| Modelos de resultado | `src/application/dtos/set_prompt_template_enabled_request.py` | Crear | `SetPromptTemplateEnabledRequest` (id, enabled, updated_by) |
| Modelos de resultado | `src/application/dtos/test_prompt_template_request.py` | Crear | `TestPromptTemplateRequest` (id, sample_values: dict[str, str])` y `TestPromptTemplateResponse` (rendered_text) |
| Modelos de resultado | `src/application/dtos/list_prompt_templates_request.py` | Crear | `ListPromptTemplatesRequest` (page, page_size, search, category, sort_by, sort_dir) y `PromptTemplateListResponse` (items, total) |
| Modelos de resultado | `src/application/dtos/resolve_prompt_template_request.py` | Crear | `ResolvePromptTemplateRequest` (category, identifier) |
| Interfaces | `src/domain/interfaces/i_prompt_template_repository.py` | Crear | `IPromptTemplateRepository` (ABC): `save`, `get_by_id`, `get_by_key`, `list`, `list_versions`, `count_by_identifier_in_category` (para la Regla 3), `update_enabled`, `delete` |
| Casos de uso | `src/application/use_cases/create_prompt_template_use_case.py` | Crear | Valida unicidad categoría+identificador (Regla 2), crea en versión 1 y activa. Excepción propia `CreatePromptTemplateException` |
| Casos de uso | `src/application/use_cases/update_prompt_template_use_case.py` | Crear | Antes de sobrescribir, guarda una fila en `prompt_template_version` con el estado actual; incrementa `version`, actualiza texto/nombre/palabras de alerta y auditoría (Regla 5). Excepción `UpdatePromptTemplateException` |
| Casos de uso | `src/application/use_cases/set_prompt_template_enabled_use_case.py` | Crear | Si `enabled=False` e identificador `generico`, comprueba que no sea la última activa de esa categoría (Regla 3, Caso 2) antes de desactivar. Excepción `SetPromptTemplateEnabledException` |
| Casos de uso | `src/application/use_cases/delete_prompt_template_use_case.py` | Crear | Misma comprobación que la desactivación antes de eliminar (Regla 3, Caso 2). Excepción `DeletePromptTemplateException` |
| Casos de uso | `src/application/use_cases/test_prompt_template_use_case.py` | Crear | Renderiza la plantilla con los valores de ejemplo/reales recibidos sin llamar al LLM ni persistir. Excepción `TestPromptTemplateException` |
| Casos de uso | `src/application/use_cases/list_prompt_templates_use_case.py` | Crear | Listado paginado con búsqueda y filtro por categoría; ordena `generico` primero dentro de cada categoría |
| Casos de uso | `src/application/use_cases/get_prompt_template_use_case.py` | Crear | Detalle + historial de versiones. Excepción `NotFoundException` si no existe |
| Casos de uso | `src/application/use_cases/resolve_prompt_template_use_case.py` | Crear | Resuelve activa exacta → `generico` activa de la categoría → `ResolvePromptTemplateException` (error de configuración) si ninguna existe. Es el punto de entrada que usará ESP-08 |
| Infraestructura | `src/infrastructure/postgresql/connection.py` | Crear | `PostgreSQLConnection`: pool singleton `asyncpg` a partir de `DATABASE_URL` |
| Infraestructura | `src/infrastructure/postgresql/base_repository.py` | Crear | `PostgreSQLBaseRepository`: `execute_query` / `execute_update` sobre el pool, y `PostgreSQLBaseException` propia |
| Infraestructura | `src/infrastructure/postgresql/repositories/postgresql_prompt_template_repository.py` | Crear | Implementación de `IPromptTemplateRepository`: upsert/consulta sobre `prompt_template` y `prompt_template_version` en una transacción para `update_prompt_template` |
| Configuración | `src/core/configuration/settings.py` | Modificar | Añade `database_url: str` |
| Configuración | `.env.example` | Modificar | Añade sección `--- PostgreSQL ---` con `DATABASE_URL` |
| Dependencias | `pyproject.toml` | Modificar | Añade `asyncpg>=0.30` a `dependencies` |
| Dependencias | `src/core/dependencies/prompt_templates.py` | Crear | Providers de FastAPI: repositorio y cada caso de uso |
| Excepciones | `src/core/exceptions/handlers.py` | Modificar | Registra handlers globales para `NotFoundException` (404), `ConflictException` (409) y `ValidationException` (422, con `field` en el cuerpo) |
| Entrega | `src/api/v1/routers/prompt_templates.py` | Crear | Router `/prompt-templates`: `GET ""`, `GET "/{id}"`, `POST ""`, `PUT "/{id}"`, `PATCH "/{id}/enabled"`, `POST "/{id}/test"`, `DELETE "/{id}"`, `GET "/resolve"` (según tabla de API de ESP-13); captura excepciones de los casos de uso y las traduce a `HTTPException` |
| Entrega | `src/api/v1/api_router.py` | Modificar | Registra `prompt_templates.router` en `protected_router` |
| Scripts DB | `scripts/DB/DB.sql` | Crear | DDL de `prompt_template` (tal cual la especificación técnica) + `prompt_template_version` (ver punto 7) |
| Scripts DB | `scripts/DB/seed/prompt_templates.sql` | Crear | Inserta la plantilla semilla `vigilancia`/`generico` |

## 5. Plan de implementación — Frontend

| Capa | Archivo | Acción | Descripción |
|---|---|---|---|
| Modelos de dominio | `front/src/app/features/prompt-templates/models/prompt-template.ts` | Crear | Interfaces `PromptTemplate`, `PromptTemplateVersion`, `PromptTemplateListItem` |
| Modelos de dominio | `front/src/app/features/prompt-templates/models/prompt-template-form.ts` | Crear | Tipos de formulario de alta/edición (categoría, identificador, nombre, plantilla, palabras de alerta, activa) |
| Contratos de repositorio | `front/src/app/features/prompt-templates/services/prompt-template.repository.ts` | Crear | Interfaz abstracta (clase abstracta) con los métodos de acceso a datos (list, getById, create, update, setEnabled, test, delete) |
| Servicios de aplicación | `front/src/app/features/prompt-templates/services/prompt-template.service.ts` | Crear | Orquesta la vista: estado con signals (listado, filtros, paginación, plantilla seleccionada), llama al repositorio, expone errores de campo para el formulario |
| Infraestructura | `front/src/app/features/prompt-templates/services/http-prompt-template.repository.ts` | Crear | Implementación HTTP contra `/api/v1/prompt-templates`, provista en `prompt-templates.routes.ts` |
| Presentación | `front/src/app/features/prompt-templates/prompt-templates.routes.ts` | Crear | Rutas lazy: listado, alta, edición, detalle |
| Presentación | `front/src/app/features/prompt-templates/pages/prompt-template-list/prompt-template-list.component.ts` (+ `.html`) | Crear | Smart component: tabla paginada, búsqueda, filtro por categoría, agrupación con `generico` destacado, acciones por fila |
| Presentación | `front/src/app/features/prompt-templates/pages/prompt-template-form/prompt-template-form.component.ts` (+ `.html`) | Crear | Smart component de alta/edición con reactive forms, autocompletar de categoría, preselección de `generico`, botón Probar prompt, errores de campo del backend |
| Presentación | `front/src/app/features/prompt-templates/pages/prompt-template-detail/prompt-template-detail.component.ts` (+ `.html`) | Crear | Vista de solo lectura con historial de versiones y auditoría |
| Presentación | `front/src/app/shared/components/paginated-table/paginated-table.component.ts` (+ `.html`) | Crear | Tabla paginada genérica (columnas, orden, paginación) — primer componente compartido, lo reutilizarán el resto de maestros y pantallas de consulta |
| Presentación | `front/src/app/shared/components/confirm-dialog/confirm-dialog.component.ts` (+ `.html`) | Crear | Modal de confirmación genérico para acciones destructivas (Eliminar, Desactivar) |
| Presentación | `front/src/app/shared/components/status-badge/status-badge.component.ts` (+ `.html`) | Crear | Etiqueta de color reutilizable (activa/inactiva aquí; estados de fuente en ESP-06) |
| Integración | `front/src/app/app.routes.ts` | Modificar | Añade la ruta lazy de `prompt-templates` bajo el shell |
| Integración | `front/src/app/core/layout/shell/shell.component.html` | Modificar | Añade la entrada de menú **Maestros › Plantillas de prompt** |
| Configuración | `front/src/environments/environment.ts` / `environment.prod.ts` | Sin cambios | `apiUrl` ya apunta a `/api/v1`; no requiere variables nuevas |

No hay URLs de Figma en el issue (la única referencia es el prototipo general sin rutas por pantalla), así que no se añade sección de Diseño (Figma) y la UI se construye a mano siguiendo la descripción de UX del punto 1.

## 6. Plan de pruebas

| Test | Tipo | Escenario | Resultado esperado |
|---|---|---|---|
| `test_create_prompt_template_with_new_category_and_generico_creates_version_1_active` | Integración | Alta de la primera plantilla de una categoría nueva | Se crea en versión 1, `enabled=True` |
| `test_create_prompt_template_with_specific_identifier_coexists_with_generico` | Integración | Categoría con `generico` activa, se crea una específica | Ambas quedan activas en la misma categoría |
| `test_create_prompt_template_with_duplicated_category_and_identifier_raises_validation_exception` | Unitario | Categoría+identificador ya existentes | `ValidationException` con `field="identifier"`, no se guarda nada |
| `test_create_prompt_template_with_invalid_slug_format_raises_validation_exception` | Unitario | Categoría o identificador con mayúsculas/espacios | `ValidationException` antes de tocar el repositorio |
| `test_resolve_prompt_template_by_specific_identifier_returns_specific` | Unitario | `generico` y `azure-updates` activas | Devuelve `azure-updates` |
| `test_resolve_prompt_template_falls_back_to_generico_when_specific_missing` | Unitario | Solo `generico` activa | Devuelve `generico` |
| `test_resolve_prompt_template_without_any_active_template_raises_configuration_error` | Unitario | Categoría sin ninguna plantilla activa | `ResolvePromptTemplateException` (Caso 3) |
| `test_delete_prompt_template_when_last_generico_active_in_category_is_denied` | Integración | Único `generico` activo de la categoría | No se elimina; `ConflictException` explicando el motivo |
| `test_set_prompt_template_enabled_false_when_last_generico_active_in_category_is_denied` | Integración | Único `generico` activo, se intenta desactivar | No se desactiva; `ConflictException` |
| `test_delete_prompt_template_when_second_generico_of_category_exists_succeeds` | Integración | Dos plantillas `generico` en distintas versiones/categorías, no es la única | Se elimina sin error |
| `test_update_prompt_template_changing_text_creates_new_version_and_keeps_history` | Integración | Plantilla en versión 2, se edita el texto | Queda en versión 3; la versión 2 aparece en `list_versions` |
| `test_update_prompt_template_cannot_change_identifier` | Unitario | Se intenta cambiar `identifier` en `UpdatePromptTemplateRequest` | El campo no existe en el DTO / se ignora, el identificador persistido no cambia |
| `test_test_prompt_template_use_case_renders_without_calling_llm_or_persisting` | Unitario | Placeholders de ejemplo | Devuelve texto renderizado; no hay llamadas al repositorio de escritura ni a ningún cliente LLM |
| `test_list_prompt_templates_orders_generico_first_within_each_category` | Unitario | Categoría con `generico` y dos específicas | `generico` aparece primero dentro del grupo de su categoría |
| `test_create_prompt_template_endpoint_without_token_returns_401` | Integración | Sin cabecera Authorization | 401 |
| `test_create_prompt_template_endpoint_with_valid_token_returns_201` | Integración | Token válido, payload correcto | 201 con la plantilla creada, `created_by` = email del token |

## 7. Notas y decisiones de diseño

- **Tabla de historial no descrita en la especificación técnica.** La Regla 5 y el Criterio de aceptación 7 exigen conservar el histórico de versiones anteriores, pero el DDL de ESP-13 solo define `prompt_template` con una fila por `(category, identifier)` y una columna `version` que se incrementa in situ, sin lugar donde guardar el texto de las versiones previas. Decisión: añadir `prompt_template_version(id, template_id FK, version, name, template, alert_keywords, created_at, created_by)`; `update_prompt_template` inserta ahí el estado previo dentro de la misma transacción antes de sobrescribir `prompt_template`. Alternativa descartada: usar temporal tables / `system-versioning` de PostgreSQL — mayor complejidad operativa para un histórico de solo lectura que no la justifica en el MVP. **Este punto conviene confirmarlo explícitamente al aprobar el plan**, ya que amplía el esquema respecto a lo escrito en ESP-13.
- **Primera funcionalidad con persistencia real.** Se aprovecha este plan para crear la infraestructura común de PostgreSQL (`connection.py`, `base_repository.py`) y las excepciones genéricas (`NotFoundException`, `ConflictException`, `ValidationException`) que da por hechas `_python.md`. Cualquier maestro futuro (fuentes de noticias, catálogo) las reutilizará sin volver a crearlas.
- **Primera feature real de frontend.** Se crean también los componentes compartidos mínimos (tabla paginada, modal de confirmación, etiqueta de estado) y la primera entrada de menú/ruta real. Se mantienen deliberadamente genéricos (sin lógica de plantillas) para que ESP-06 y el resto de maestros los reutilicen sin reescritura.
- **Borrado físico.** La constitución (§2.4) permite borrado físico solo donde la especificación lo autoriza explícitamente; ESP-13 sí lo permite para una plantilla que no es la última `generico` activa de su categoría, así que `DELETE /api/v1/prompt-templates/{id}` borra físicamente (y sus filas de `prompt_template_version`, vía `ON DELETE CASCADE`), sin necesidad de un flag "inactivo".
- **Placeholders del "Probar prompt".** ESP-13 no define un formato de placeholder (Regla 6, Fuera de alcance); se usa un `dict[str, str]` de sustitución simple (`str.format` o similar) resuelto por el propio caso de uso; cada consumidor documenta sus claves en su especificación (ESP-08 lo hará en la suya). No se valida qué claves son válidas en este maestro.
