# Análisis de Implementación — ESP-06: Maestro de fuentes de noticias

Estado: pendiente de aprobacion

Fuente: File (`./docs/Spec/Especificaciones.md`) · Épica 3 Vigilancia

---

## 1. Descripción funcional

> Transcrita de la sección `### ESP-06` del archivo de especificaciones (Historia de usuario, Descripción de UX, Descripción funcional y Descripción técnica).

### Historia de usuario

**Como** responsable de vigilancia tecnológica,

**Quiero** crear, consultar, modificar y eliminar las fuentes de noticias de proveedores y productos que quiero seguir desde una pantalla de mantenimiento,

**Para** que el sistema sepa de dónde obtener novedades y con qué frecuencia.

### Descripción de UX

**Prototipo:** https://dimly-woven-86209062.figma.site → menú lateral, sección **Maestros › Fuentes de noticias**. El prototipo es una sola aplicación sin rutas propias por pantalla, así que el enlace es el mismo para todo el sitio; hay que navegar manualmente hasta esa opción del menú.

El maestro se abre desde el menú **Maestros › Fuentes de noticias** y tiene tres vistas: listado, formulario y detalle.

**Listado de fuentes**

- Tabla paginada con las columnas Identificador, Nombre, Tipo, Frecuencia (h), Estado, Activa y Última modificación.
- Búsqueda libre por identificador, nombre o URL.
- Filtros por tipo, estado (Pendiente de validar / Operativa / En error) y activa (sí/no).
- Ordenación por cualquier columna; por defecto, por nombre.
- El estado se muestra como etiqueta de color: gris para pendiente, verde para operativa y rojo para en error. Las fuentes desactivadas se muestran atenuadas.
- Botón **Nueva fuente**.
- Acciones por fila: Ver detalle, Editar, Activar/Desactivar, Validar ahora y Eliminar.

**Formulario de alta y edición**

| Campo | Control | Obligatorio | Observaciones |
| --- | --- | --- | --- |
| Identificador | Texto | Sí | Formato slug (`langchain-releases`). No editable una vez creada la fuente. |
| Nombre | Texto | Sí | Máx. 200 caracteres. |
| URL | Texto | Sí | http/https. |
| Tipo | Selector | Sí | RSS/Atom, Releases de GitHub o Versiones de PyPI. |
| Frecuencia de consulta (horas) | Numérico | Sí | Por defecto 24. Rango de 1 a 720. |
| Activa | Interruptor | Sí | Por defecto activa. |
| Filtro de inclusión | Texto | No | Expresión regular sobre el título. Si se informa, solo se ingieren las entradas que coinciden. |
| Filtro de exclusión | Texto | No | Expresión regular sobre el título. Se descartan las entradas que coinciden (por ejemplo, `^VSCode Extension` en las releases de Angular). |
| Incluir prereleases | Interruptor | No | Solo visible para Releases de GitHub y Versiones de PyPI. Por defecto desactivado. |

- Botón **Probar feed**: valida la URL sin guardar. Si la validación es correcta, muestra el título del feed, el número de entradas, cuántas pasan los filtros y la fecha de la última entrada; si falla, muestra el error obtenido.
- Botones **Guardar** y **Cancelar**. Los errores de validación se muestran junto a cada campo.

**Detalle de la fuente**

Muestra todos los campos en modo lectura, el estado y los datos de auditoría (fecha y usuario de alta y de última modificación). Desde esta vista se accede a Editar, Validar ahora, Activar/Desactivar y Eliminar.

Incluye además un bloque **Prompt de clasificación** que indica qué plantilla se le aplica (la propia de la fuente o la genérica de la categoría "Vigilancia") con un enlace **Personalizar** que abre el maestro de plantillas de prompt (ESP-13) con la categoría "Vigilancia" y el identificador de esa fuente ya propuestos.

### Descripción funcional

**Propósito de la funcionalidad**

Centralizar y mantener desde un maestro con interfaz gráfica las fuentes vigiladas, que son la base de la ingesta de noticias (ESP-07).

**Flujo principal (alta)**

El usuario pulsa **Nueva fuente** → Completa el formulario → Pulsa **Guardar** → El sistema valida los campos → Comprueba que la URL responde y es un feed válido → Crea la fuente con estado "Operativa" → Muestra un mensaje de confirmación.

**Flujos secundarios**

- **Consulta:** el usuario busca y filtra en el listado y abre el detalle de una fuente.
- **Modificación:** el usuario edita una fuente y guarda. Si cambia la URL o el tipo, el sistema vuelve a validar el feed y actualiza el estado.
- **Activar/Desactivar:** cambia el campo `enabled`. Las fuentes desactivadas no se consultan, pero se conservan.
- **Validar ahora:** fuerza la validación del feed. Si es correcta, la fuente pasa a "Operativa"; si falla, pasa a "En error".
- **Personalizar el prompt:** desde el detalle de la fuente, el usuario crea o edita la plantilla de la categoría "Vigilancia" con identificador igual al de la fuente (ESP-13). Si no la crea, la fuente usa la plantilla genérica de esa categoría.
- **Eliminación:** el sistema pide confirmación y solo elimina la fuente si no tiene noticias asociadas (Regla 8).

**Reglas de negocio**

- Regla 1: Los campos obligatorios son identificador, nombre, URL, tipo y frecuencia.
- Regla 2: El identificador es único, tiene formato slug (minúsculas, números y guiones) y no se puede modificar después del alta.
- Regla 3: La URL es única sin distinguir mayúsculas; no puede haber dos fuentes con la misma URL.
- Regla 4: Los tipos admitidos en el MVP son:
  - **RSS/Atom** (`rss_atom`): cualquier feed RSS 2.0 o Atom.
  - **Releases de GitHub** (`github_releases`): se consumen como Atom y su URL debe seguir el patrón `https://github.com/{owner}/{repo}/releases.atom`.
  - **Versiones de PyPI** (`pypi_releases`): su URL debe seguir el patrón `https://pypi.org/rss/project/{paquete}/releases.xml`. El paquete se obtiene de la URL, por lo que se crea una fuente por paquete.

  El tipo determina el adaptador que aplica la ingesta (ESP-07).
- Regla 5: La frecuencia de consulta se expresa en horas, entre 1 y 720; por defecto es 24.
- Regla 6: Una fuente puede desactivarse sin borrarla (campo `enabled`).
- Regla 7: La fuente tiene tres estados posibles:
  - "Pendiente de validar": aún no se ha validado.
  - "Operativa": la última validación fue correcta.
  - "En error": la última validación falló.

  El estado se actualiza al guardar y con Validar ahora.
- Regla 8: No se puede eliminar una fuente con noticias asociadas; en ese caso el sistema propone desactivarla.
- Regla 9: Cada alta y cada modificación registran la fecha y el usuario que la realizó.
- Regla 10: La aplicación realiza todas las validaciones de estas reglas; la base de datos no contiene lógica.
- Regla 11: Los filtros de inclusión y exclusión son opcionales, deben ser expresiones regulares válidas (máx. 500 caracteres) y se evalúan sobre el título de la entrada sin distinguir mayúsculas. Si hay ambos, primero se aplica la inclusión y después la exclusión. Los filtros se aplican en la ingesta (ESP-07); cambiarlos no vuelve a validar el feed.
- Regla 12: La opción "Incluir prereleases" solo aplica a Releases de GitHub y Versiones de PyPI; en RSS/Atom se ignora. Por defecto las prereleases (alpha, beta, rc, dev, next) no se ingieren.

**Flujos alternativos o de excepción**

Caso 1: La URL no responde o no es un feed válido al guardar. El sistema muestra una advertencia con el error y ofrece dos opciones: *Guardar igualmente*, con lo que la fuente queda "En error", o *Corregir*, que vuelve al formulario.

Caso 2: Identificador o URL duplicados. No se guarda y se muestra el error en el campo correspondiente.

Caso 3: Un campo tiene formato incorrecto o un valor fuera de rango (incluidas una URL que no sigue el patrón de su tipo o una expresión regular no válida en los filtros). No se guarda y se muestra el error junto al campo.

Caso 4: Eliminación de una fuente con noticias asociadas. No se elimina, se informa del número de noticias y se ofrece desactivarla.

**Punto de entrada**

Menú **Maestros › Fuentes de noticias** de la aplicación web.

**Sistemas / Servicios afectados**

Sitios web de las fuentes (validación HTTP del feed).

**Persistencia de datos**

- Fuente: identificador, nombre, URL, tipo, frecuencia, activa, filtros de inclusión y exclusión, incluir prereleases, estado y auditoría (fecha y usuario de alta y de última modificación).

**Notas sobre la interfaz**

Se entregan cargadas de 10 a 15 fuentes semilla mediante un script de datos iniciales. Incluyen, como mínimo, las fuentes de referencia:

| Identificador | Tipo | URL | Filtros |
| --- | --- | --- | --- |
| `azure-updates` | RSS/Atom | `https://www.microsoft.com/releasecommunications/api/v2/azure/rss` | — |
| `huggingface-blog` | RSS/Atom | `https://huggingface.co/blog/feed.xml` | — |
| `pypi-{paquete}` (una por paquete del catálogo semilla) | Versiones de PyPI | `https://pypi.org/rss/project/{paquete}/releases.xml` | Sin prereleases |
| `dotnet-blog` | RSS/Atom | `https://devblogs.microsoft.com/dotnet/feed/` | — |
| `angular-releases` | Releases de GitHub | `https://github.com/angular/angular/releases.atom` | Exclusión `^VSCode Extension`, sin prereleases |

El resto son blogs y changelogs de proveedores de IA y páginas de deprecación de modelos que ofrezcan feed. Quedan en estado "Pendiente de validar" hasta su primera validación y se mantienen desde el maestro como cualquier otra fuente.

**Fuera de alcance**

- Relación de fuentes con componentes del catálogo (se detallará en otra especificación).
- Mantenimiento de las plantillas de prompt (maestro propio en ESP-13); este maestro solo enlaza a él.
- Seguimiento de fallos consecutivos y resultado de las consultas periódicas (dominio de la ingesta, ESP-07).
- Scraping de páginas HTML sin feed.
- Fuentes que requieren autenticación.
- Redes sociales.
- Newsletters por email.
- Importación o exportación masiva de fuentes.


### Descripción técnica

**Validación del feed**

- Se valida con `feedparser`. El feed es válido si responde HTTP 2xx, `bozo` no indica un error fatal y contiene `feed.title` o al menos una entrada.
- Timeout de 10 segundos y hasta 5 redirecciones.
- User-Agent identificable (por ejemplo `VigilanciaTecBot/1.0 (+url-de-contacto)`) y respeto de `robots.txt`; si `robots.txt` prohíbe el acceso, se trata como error de validación. El User-Agent de bot es obligatorio y no debe sustituirse por uno de navegador: algunas fuentes, como Azure Updates, devuelven 403 a los User-Agent de navegador. La ingesta (ESP-07) usa el mismo.
- Además de la validación del feed, se comprueba que la URL cumple el patrón de su tipo (Regla 4) y que los filtros compilan como expresión regular (Regla 11).
- La validación se ejecuta en el backend. *Probar feed* llama a un endpoint que no persiste nada.

**API (backend del maestro)**

| Método | Ruta | Uso |
| --- | --- | --- |
| GET | `/api/news-sources` | Listado con paginación, filtros y búsqueda |
| GET | `/api/news-sources/{id}` | Detalle |
| POST | `/api/news-sources` | Alta |
| PUT | `/api/news-sources/{id}` | Modificación |
| PATCH | `/api/news-sources/{id}/enabled` | Activar/Desactivar |
| POST | `/api/news-sources/{id}/validate` | Validar ahora |
| POST | `/api/news-sources/test-feed` | Probar feed sin guardar |
| DELETE | `/api/news-sources/{id}` | Eliminación (409 si tiene noticias asociadas) |

**Modelo de datos en PostgreSQL**

Tabla `news_source`:

| Columna | Tipo | Nulo | Por defecto | Descripción |
| --- | --- | --- | --- | --- |
| `id` | `UUID` | No | `gen_random_uuid()` | Clave primaria técnica |
| `code` | `VARCHAR(64)` | No | — | Identificador de negocio (slug), inmutable |
| `name` | `VARCHAR(200)` | No | — | Nombre visible |
| `url` | `VARCHAR(2048)` | No | — | URL del feed |
| `source_type` | `VARCHAR(20)` | No | — | `rss_atom`, `github_releases` o `pypi_releases` |
| `fetch_frequency_hours` | `INTEGER` | No | `24` | Frecuencia de consulta (1–720) |
| `enabled` | `BOOLEAN` | No | `TRUE` | Fuente activa o desactivada |
| `include_pattern` | `VARCHAR(500)` | Sí | — | Filtro de inclusión (expresión regular sobre el título) |
| `exclude_pattern` | `VARCHAR(500)` | Sí | — | Filtro de exclusión (expresión regular sobre el título) |
| `include_prereleases` | `BOOLEAN` | No | `FALSE` | Ingerir prereleases (solo `github_releases` y `pypi_releases`) |
| `status` | `VARCHAR(20)` | No | `'pending'` | `pending` (Pendiente de validar), `ok` (Operativa) o `error` (En error) |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Fecha de alta |
| `created_by` | `VARCHAR(100)` | No | — | Usuario que la creó |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Fecha de última modificación |
| `updated_by` | `VARCHAR(100)` | No | — | Usuario que la modificó |

```sql
CREATE TABLE news_source (
    id                     UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    code                   VARCHAR(64)   NOT NULL,
    name                   VARCHAR(200)  NOT NULL,
    url                    VARCHAR(2048) NOT NULL,
    source_type            VARCHAR(20)   NOT NULL,
    fetch_frequency_hours  INTEGER       NOT NULL DEFAULT 24,
    enabled                BOOLEAN       NOT NULL DEFAULT TRUE,
    include_pattern        VARCHAR(500),
    exclude_pattern        VARCHAR(500),
    include_prereleases    BOOLEAN       NOT NULL DEFAULT FALSE,
    status                 VARCHAR(20)   NOT NULL DEFAULT 'pending',
    created_at             TIMESTAMPTZ   NOT NULL DEFAULT now(),
    created_by             VARCHAR(100)  NOT NULL,
    updated_at             TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_by             VARCHAR(100)  NOT NULL
);
```

## 2. Criterios de aceptación

1. **Alta de fuente de releases de GitHub**: dado que el usuario está en el formulario "Nueva fuente" y completa identificador "langchain-releases", tipo "Releases de GitHub" y URL "https://github.com/langchain-ai/langchain/releases.atom", cuando pulsa "Guardar", entonces la fuente se crea activa con estado "Operativa" y aparece en el listado de fuentes.
2. **Alta de fuente de versiones de PyPI**: dado que el usuario está en el formulario "Nueva fuente" y completa identificador "pypi-langchain", tipo "Versiones de PyPI" y URL "https://pypi.org/rss/project/langchain/releases.xml", cuando pulsa "Guardar", entonces la fuente se crea activa con estado "Operativa" y con "Incluir prereleases" desactivado.
3. **URL que no sigue el patrón de su tipo**: dado que el usuario elige el tipo "Versiones de PyPI" y completa la URL "https://pypi.org/project/langchain/", cuando pulsa "Guardar", entonces el sistema no guarda y muestra el patrón esperado en el campo URL.
4. **Filtro con expresión regular no válida**: dado que el usuario completa el filtro de exclusión "^VSCode (Extension", cuando pulsa "Guardar", entonces el sistema no guarda y muestra el error en el campo filtro de exclusión.
5. **Alta de fuente con URL inválida**: dado que el usuario da de alta una fuente cuya URL devuelve error 404, cuando pulsa "Guardar", entonces el sistema muestra una advertencia con el error y, si elige "Guardar igualmente", la fuente queda en estado "En error".
6. **Identificador duplicado**: dado que ya existe la fuente "openai-blog", cuando el usuario intenta crear otra fuente con identificador "openai-blog", entonces el sistema no guarda y muestra el error "El identificador ya existe" en el campo identificador.
7. **Modificación de la URL**: dada la fuente "openai-blog" en estado "En error", cuando el usuario cambia la URL por una válida y pulsa "Guardar", entonces el sistema valida el nuevo feed y la fuente pasa a estado "Operativa".
8. **Desactivar una fuente**: dada la fuente activa "anthropic-news", cuando el usuario pulsa "Desactivar", entonces la fuente queda con activa = no y no se incluye en las consultas programadas.
9. **Eliminar fuente sin noticias**: dada la fuente "test-feed" sin noticias asociadas, cuando el usuario pulsa "Eliminar" y confirma, entonces la fuente se elimina.
10. **Eliminar fuente con noticias**: dada la fuente "openai-blog" con noticias asociadas, cuando el usuario pulsa "Eliminar", entonces el sistema no la elimina y ofrece desactivarla.
11. **Consulta con filtros**: dadas varias fuentes con distintos estados, cuando el usuario filtra por estado "En error", entonces el listado muestra solo las fuentes en ese estado.

## 3. Análisis de impacto

### 3.1 Riesgos de regresión

ESP-14 (implementada) y ESP-13 (código en `feature/ESP-13`, sin commitear ni mergear) son las únicas funcionalidades con código. ESP-06 es la segunda que persiste datos y **se apoya en la base que crea ESP-13**; el riesgo principal es de orden de integración, no de regresión funcional.

| Issue afectado | Fichero | Motivo |
|---|---|---|
| ESP-13 (dependencia de base) | `src/infrastructure/postgresql/connection.py`, `base_repository.py`, `src/core/exceptions/{validation,conflict,not_found}_exception.py`, `src/domain/value_objects/slug.py`, `scripts/DB/DB.sql` | ESP-06 reutiliza estos ficheros, que hoy solo existen como cambios sin commitear en `feature/ESP-13`. Si `feature/ESP-06` se crea desde `develop` antes de mergear ESP-13, no compila. **ESP-13 debe mergearse a `develop` antes de empezar ESP-06** (o crear la rama apilada sobre `feature/ESP-13`). |
| ESP-13 / ESP-14 | `src/core/exceptions/handlers.py` | Se añade un handler global para `FeedValidationFailedException` (422 con `field` y `code`). Solo se añade; los handlers existentes (401/403/404/409/422/500) no cambian, pero se registra antes del handler genérico `Exception` para no quedar oculto. |
| ESP-13 / ESP-14 | `src/core/configuration/settings.py` | Nueva propiedad `bot_user_agent` **con valor por defecto**: si fuese obligatoria, `tests/conftest.py` (que construye `Settings(...)` sin ella) y el arranque de ESP-13/ESP-14 fallarían. |
| ESP-13 / ESP-14 | `src/api/v1/api_router.py` | Se incluye `news_sources.router` en `protected_router`; hereda la validación del token de ESP-14. Sin cambio para los routers existentes. |
| ESP-13 (frontend) | `front/src/app/features/prompt-templates/pages/prompt-template-form/…` | El enlace **Personalizar** del detalle de la fuente abre el formulario de ESP-13 con `category=vigilancia` e `identifier={code}` propuestos: el formulario de ESP-13 debe leer esos *query params*. Cambio aditivo; si el formulario aún no existe cuando se implemente ESP-06, se deja el enlace y un `// TODO: ESP-13` en el formulario. |
| ESP-13 (frontend) | `front/src/app/shared/components/{paginated-table,confirm-dialog,status-badge}` | El plan de ESP-13 los crea genéricos; ESP-06 los reutiliza. `status-badge` necesita las variantes gris/verde/rojo de estado de fuente: se amplía sin cambiar las que use ESP-13. |
| ESP-07 (futuro) | `news_source` (esquema) y `src/domain/value_objects/title_filter.py` | ESP-07 leerá `news_source` (fuentes activas vencidas) y aplicará los mismos filtros. El esquema que fija ESP-06 es contrato para `func/`. |

### 3.2 TODOs a resolver

Ninguno. No hay comentarios `# TODO: ... ESP-06` en `back/`, `front/` ni `func/`.

### 3.3 Cambios transversales

- **Esquema de BD** (`scripts/DB/DB.sql`): tabla `news_source` exactamente con el DDL de la especificación, más dos índices únicos **no escritos en la especificación** (ver §7, D2):
  - `CREATE UNIQUE INDEX ux_news_source_code ON news_source (code);`
  - `CREATE UNIQUE INDEX ux_news_source_url ON news_source (lower(url));`
- **Semilla** (`scripts/DB/seed/news_sources.sql`): 10–15 fuentes en estado `pending`, `created_by = 'seed'`, idempotente con `ON CONFLICT (code) DO NOTHING` (necesita el índice único sobre `code`).
- **Variables de entorno**: `BOT_USER_AGENT` en `.env.example` y `Settings` (compartida con `func/`, guía Azure). Timeout (10 s) y redirecciones (5) **no** son variables: son parámetros fijos de la constitución §3.4 → constantes de dominio.
- **Dependencias** (`pyproject.toml`): añadir `feedparser>=6.0`; mover `httpx>=0.28` de `dev` a `dependencies` (cliente HTTP asíncrono de la validación). `robots.txt` con `urllib.robotparser` (stdlib). Regenerar `uv.lock` y `requirements.txt`.
- **Frontend**: sin dependencias nuevas en `package.json`; nueva ruta lazy y primera entrada de menú **Maestros › Fuentes de noticias**.
- `func/`: sin cambios en esta ESP (la ingesta es ESP-07).

## 4. Plan de implementación — Backend

Rutas relativas a `back/`. Las rutas de la especificación (`/api/news-sources`) se exponen como `/api/v1/news-sources`.

| Capa | Archivo | Acción | Descripción |
|---|---|---|---|
| Enums | `src/domain/enums/news_source_type.py` | Crear | `NewsSourceType(str, Enum)`: `RSS_ATOM="rss_atom"`, `GITHUB_RELEASES="github_releases"`, `PYPI_RELEASES="pypi_releases"`; propiedad `supports_prereleases` (Regla 12) |
| Enums | `src/domain/enums/news_source_status.py` | Crear | `NewsSourceStatus(str, Enum)`: `PENDING="pending"`, `OK="ok"`, `ERROR="error"` (Regla 7) |
| Excepciones | `src/core/exceptions/feed_validation_failed_exception.py` | Crear | `FeedValidationFailedException(message, feed_error)`: el feed no es válido y el usuario no ha elegido *Guardar igualmente* (Caso 1). Handler global → 422 `{detail, field: "url", code: "feed_invalid"}` para que Angular abra la advertencia |
| Excepciones | `src/core/exceptions/news_source_in_use_exception.py` | Crear | `NewsSourceInUseException(ConflictException)` con `news_count` (Regla 8, Caso 4); el router responde 409 `{detail, news_count}` |
| Excepciones | `src/core/exceptions/{create,update,set_enabled,validate,test_feed,delete}_news_source_exception.py` | Crear | Una excepción por caso de uso (`CreateNewsSourceException`, `UpdateNewsSourceException`, `SetNewsSourceEnabledException`, `ValidateNewsSourceException`, `TestNewsSourceFeedException`, `DeleteNewsSourceException`) para errores no atribuibles al cliente (→ 502) |
| Value objects | `src/domain/value_objects/news_source_limits.py` | Crear | Constantes de constitución §3.4: `MIN_FREQUENCY_HOURS=1`, `MAX_FREQUENCY_HOURS=720`, `DEFAULT_FREQUENCY_HOURS=24`, `MAX_PATTERN_LENGTH=500`, `MAX_NAME_LENGTH=200`, `MAX_URL_LENGTH=2048`, `FEED_TIMEOUT_SECONDS=10`, `FEED_MAX_REDIRECTS=5` |
| Value objects | `src/domain/value_objects/news_source_url.py` | Crear | `validate_source_url(url, source_type)`: http/https, longitud, y patrón por tipo (Regla 4): `^https://github\.com/[^/]+/[^/]+/releases\.atom$` y `^https://pypi\.org/rss/project/[^/]+/releases\.xml$`. El mensaje de error incluye el patrón esperado (`https://pypi.org/rss/project/{paquete}/releases.xml`) → `ValidationException(field="url")` (Criterio 3). Lógica de dominio compartida con la ingesta (guía Python) |
| Value objects | `src/domain/value_objects/title_filter.py` | Crear | `TitleFilter(include_pattern, exclude_pattern)` inmutable: compila ambas regex con `re.IGNORECASE`, valida longitud ≤ 500 y sintaxis (`ValidationException(field="include_pattern"/"exclude_pattern")`, Criterio 4); `matches(title)` aplica inclusión y después exclusión (Regla 11). Lo reutilizan *Probar feed* y ESP-07 |
| Entidades | `src/domain/entities/news_source.py` | Crear | `NewsSource`: id, code, name, url, source_type, fetch_frequency_hours, enabled, include_pattern, exclude_pattern, include_prereleases, status, created_at, created_by, updated_at, updated_by. `__post_init__`: `validate_slug(code, "code")` (reutiliza ESP-13), nombre obligatorio ≤ 200, `validate_source_url`, frecuencia 1–720 (`field="fetch_frequency_hours"`), `TitleFilter(...)`; si el tipo es `rss_atom` fuerza `include_prereleases=False` (Regla 12). Métodos `with_status(status)` y `url_or_type_changed(other)` |
| Entidades | `src/domain/entities/feed_check.py` | Crear | Resultado de validar un feed: `ok`, `title`, `entry_count`, `entry_titles`, `last_entry_at`, `error` (texto del error: HTTP 404, timeout, bloqueado por `robots.txt`, no es un feed…). Método `matching_count(title_filter)` para "cuántas pasan los filtros" |
| Entidades | `src/domain/entities/feed_check_request.py` | Crear | `FeedCheckRequest(url, source_type)` inmutable: lo que el validador necesita (la infraestructura no recibe primitivos sueltos) |
| Modelos de resultado | `src/application/dtos/news_source_response.py` | Crear | `NewsSourceResponse` (listado/detalle, `from_entity`) y `NewsSourceDetailResponse` = fuente + bloque `prompt_template: {category, identifier, is_specific, template_id, name}` o `null` si ni la específica ni la `generico` existen |
| Modelos de resultado | `src/application/dtos/feed_check_response.py` | Crear | `FeedCheckResponse`: `ok`, `title`, `entry_count`, `matching_count`, `last_entry_at`, `error` (respuesta de *Probar feed* y *Validar ahora*) |
| Modelos de resultado | `src/application/dtos/create_news_source_request.py` | Crear | `CreateNewsSourceRequest` (code, name, url, source_type, fetch_frequency_hours=24, enabled=True, include_pattern, exclude_pattern, include_prereleases=False, `save_even_if_feed_fails=False`, created_by) + `with_user(email)` |
| Modelos de resultado | `src/application/dtos/update_news_source_request.py` | Crear | `UpdateNewsSourceRequest` sin `code` (inmutable, Regla 2) + `save_even_if_feed_fails` + `with_id_and_user` |
| Modelos de resultado | `src/application/dtos/set_news_source_enabled_request.py` | Crear | `SetNewsSourceEnabledRequest(id, enabled, updated_by)` |
| Modelos de resultado | `src/application/dtos/list_news_sources_request.py` | Crear | `ListNewsSourcesRequest` (page, page_size, search, source_type, status, enabled, sort_by="name", sort_dir="asc") y `NewsSourceListResponse(items, total)` |
| Modelos de resultado | `src/application/dtos/{get,delete,validate}_news_source_request.py` | Crear | Peticiones por id |
| Modelos de resultado | `src/application/dtos/test_news_source_feed_request.py` | Crear | `TestNewsSourceFeedRequest(url, source_type, include_pattern, exclude_pattern)` |
| Interfaces | `src/domain/interfaces/i_news_source_repository.py` | Crear | `INewsSourceRepository(ABC)`: `save`, `update`, `update_enabled(NewsSourceEnabledChange)`, `update_status(source_id, status)`, `delete`, `get_by_id`, `exists_with_code`, `exists_with_url(url, exclude_id)` (sin distinguir mayúsculas, Regla 3), `count_news(source_id)` (Regla 8), `list(...)` |
| Interfaces | `src/domain/interfaces/i_feed_validator.py` | Crear | `IFeedValidator(ABC)`: `async check(request: FeedCheckRequest) -> FeedCheck`. Nunca lanza por un feed inválido: lo devuelve en `FeedCheck.error` |
| Entidades | `src/domain/entities/news_source_enabled_change.py` | Crear | `NewsSourceEnabledChange(source_id, enabled, updated_by)` (el ejemplo de la guía Python) |
| Casos de uso | `src/application/use_cases/create_news_source_use_case.py` | Crear | Construye la entidad (validaciones de campo) → unicidad de `code` ("El identificador ya existe", `field="code"`, Criterio 6) y de `url` (`field="url"`) → valida el feed → si es válido estado `ok`; si no y `save_even_if_feed_fails=False` lanza `FeedValidationFailedException`; si no y `True`, guarda con estado `error` (Criterios 1, 2, 5) |
| Casos de uso | `src/application/use_cases/update_news_source_use_case.py` | Crear | Carga la fuente (404) → aplica cambios → unicidad de URL excluyéndose a sí misma → **solo si cambian URL o tipo** revalida el feed con la misma política de *Guardar igualmente* (Criterio 7); cambiar filtros o frecuencia no revalida (Regla 11) y conserva el estado |
| Casos de uso | `src/application/use_cases/set_news_source_enabled_use_case.py` | Crear | Cambia `enabled` y auditoría (Criterio 8). No toca `status` |
| Casos de uso | `src/application/use_cases/validate_news_source_use_case.py` | Crear | *Validar ahora*: valida el feed y persiste `ok`/`error`; devuelve `FeedCheckResponse` + fuente actualizada. No modifica auditoría (§7, D6) |
| Casos de uso | `src/application/use_cases/test_news_source_feed_use_case.py` | Crear | *Probar feed*: valida URL por tipo y filtros, llama al validador y devuelve título, nº de entradas, nº que pasan los filtros y fecha de la última. **No persiste nada** |
| Casos de uso | `src/application/use_cases/delete_news_source_use_case.py` | Crear | 404 si no existe → `count_news` > 0 ⇒ `NewsSourceInUseException(news_count)` (Criterio 10) → si no, borrado físico (Criterio 9; autorizado por la constitución §2.4) |
| Casos de uso | `src/application/use_cases/list_news_sources_use_case.py` | Crear | Listado paginado con búsqueda (code, name, url), filtros por tipo, estado y activa (Criterio 11), orden por columna en lista blanca; por defecto `name asc` |
| Casos de uso | `src/application/use_cases/get_news_source_use_case.py` | Crear | Detalle + bloque *Prompt de clasificación*: usa `IPromptTemplateRepository.get_active_by_key` (ESP-13) con categoría `vigilancia` e identificador `code`; si no hay específica, la `generico`; indica cuál aplica. Constante `NEWS_CLASSIFICATION_PROMPT_CATEGORY = "vigilancia"` en `src/domain/value_objects/prompt_template_key.py` (la usará ESP-08) |
| Prompts de IA | — | N/A | ESP-06 no llama al LLM; solo enlaza con el maestro de ESP-13 |
| Infraestructura | `src/infrastructure/feeds/feedparser_feed_validator.py` | Crear | `FeedparserFeedValidator(IFeedValidator)`: `httpx.AsyncClient` con `User-Agent = BOT_USER_AGENT`, `timeout=10`, `follow_redirects=True`, `max_redirects=5`; comprueba antes `robots.txt` con `urllib.robotparser` (prohibido ⇒ error de validación); rechaza hosts que resuelven a IP privada, *loopback* o *link-local* (SSRF, §7 D7); `feedparser.parse(body)`; válido si HTTP 2xx, `bozo` sin error fatal y `feed.title` o ≥ 1 entrada (Descripción técnica) |
| Infraestructura | `src/infrastructure/feeds/feed_validator_exception.py` | Crear | `FeedValidatorException`: única excepción de esta infraestructura (errores inesperados, no feeds inválidos) |
| Infraestructura | `src/infrastructure/postgresql/repositories/postgresql_news_source_repository.py` | Crear | Implementación de `INewsSourceRepository` sobre `PostgreSQLBaseRepository`. `exists_with_url` con `lower(url) = lower($1)`; lista blanca de columnas de orden; búsqueda `ILIKE` escapando `%`/`_`. `count_news` devuelve `0` con `# TODO: ESP-07 — contar filas de news por source_id` mientras no exista la tabla `news` (§7, D1) |
| Configuración | `src/core/configuration/settings.py` | Modificar | `bot_user_agent: str = DEFAULT_BOT_USER_AGENT` (`OneWatchBot/1.0 (+<url-de-contacto>)`) |
| Configuración | `.env.example` | Modificar | Sección `--- Recolección de fuentes (ESP-06) ---` con `BOT_USER_AGENT` y comentario: nunca un User-Agent de navegador (constitución §2.9) |
| Dependencias | `pyproject.toml` / `uv.lock` / `requirements.txt` | Modificar | `feedparser>=6.0`; `httpx>=0.28` pasa a `dependencies` |
| Dependencias | `src/core/dependencies/news_sources.py` | Crear | Providers: repositorio (`lru_cache`, comparte pool), `get_feed_validator` (`lru_cache`, con `BOT_USER_AGENT`) y un provider por caso de uso; `GetNewsSourceUseCase` recibe además `get_prompt_template_repository` de ESP-13 |
| Excepciones | `src/core/exceptions/handlers.py` | Modificar | Registra `FeedValidationFailedException` → 422 `{detail, field: "url", code: "feed_invalid", feed_error}` |
| Entrega | `src/api/v1/routers/news_sources.py` | Crear | Router `/news-sources`: `GET ""`, `POST "/test-feed"` (declarado antes de las rutas con `{source_id}`), `GET "/{id}"`, `POST ""` (201), `PUT "/{id}"`, `PATCH "/{id}/enabled"`, `POST "/{id}/validate"`, `DELETE "/{id}"` (204; 409 `{detail, news_count}`). Añade el email del token como `created_by`/`updated_by` (Regla 9, ESP-14 Regla 9). Sin lógica |
| Entrega | `src/api/v1/api_router.py` | Modificar | `protected_router.include_router(news_sources.router)` |
| Scripts DB | `scripts/DB/DB.sql` | Modificar | Sección `-- ESP-06` con `CREATE TABLE news_source` (DDL literal de la especificación) + los dos índices únicos (§3.3) |
| Scripts DB | `scripts/DB/seed/news_sources.sql` | Crear | Fuentes semilla (§7, D8): `azure-updates`, `huggingface-blog`, `dotnet-blog`, `angular-releases` (exclusión `^VSCode Extension`), `pypi-openai`, `pypi-anthropic`, `pypi-langchain`, `pypi-llama-index`, `pypi-transformers`, `openai-news`, `google-ai-blog`, `langchain-releases` y otras con feed de proveedores de IA hasta 10–15; todas `pending` |

## 5. Plan de implementación — Frontend

Rutas relativas a `front/src/app/`. Se asume mergeado el frontend de ESP-13 (componentes compartidos); si no, ESP-06 los crea tal como los describe el plan de ESP-13.

| Capa | Archivo | Acción | Descripción |
|---|---|---|---|
| Modelos de dominio | `features/news-sources/models/news-source.ts` | Crear | `NewsSourceType`, `NewsSourceStatus` (uniones literales), `NewsSource`, `NewsSourceDetail` (con `promptTemplate`), `NewsSourcePage`, etiquetas visibles por tipo y estado |
| Modelos de dominio | `features/news-sources/models/news-source-form.ts` | Crear | `NewsSourceFormValue`, `NewsSourceQuery` (página, búsqueda, filtros, orden), `FieldErrors` (mapa campo → mensaje del backend) |
| Modelos de dominio | `features/news-sources/models/feed-check.ts` | Crear | `FeedCheck` (ok, título, entradas, pasan filtros, última entrada, error) |
| Contratos de repositorio | `features/news-sources/services/news-source.repository.ts` | Crear | Clase abstracta: `list`, `getById`, `create`, `update`, `setEnabled`, `validate`, `testFeed`, `delete` |
| Servicios de aplicación | `features/news-sources/services/news-source.service.ts` | Crear | Estado con signals (página, filtros, orden por defecto `name`, fuente seleccionada, `fieldErrors`, `feedWarning`); traduce 422 `feed_invalid` en advertencia *Guardar igualmente / Corregir* (reenvía con `saveEvenIfFeedFails: true`), 422 con `field` en error de campo, 409 de borrado en oferta de desactivar |
| Infraestructura | `features/news-sources/services/http-news-source.repository.ts` | Crear | Implementación HTTP contra `${environment.apiUrl}/news-sources`, provista en `news-sources.routes.ts` (el token lo añade `MsalInterceptor` de ESP-14) |
| Presentación | `features/news-sources/news-sources.routes.ts` | Crear | Rutas lazy: listado (`''`), alta (`nueva`), edición (`:id/editar`), detalle (`:id`) |
| Presentación | `features/news-sources/pages/news-source-list/news-source-list.component.{ts,html}` | Crear | Smart: tabla paginada (Identificador, Nombre, Tipo, Frecuencia (h), Estado, Activa, Última modificación), búsqueda libre, filtros tipo/estado/activa, orden por columna, filas desactivadas atenuadas, botón **Nueva fuente**, acciones Ver detalle / Editar / Activar-Desactivar / Validar ahora / Eliminar (con confirmación y, ante 409, oferta de desactivar) |
| Presentación | `features/news-sources/pages/news-source-form/news-source-form.component.{ts,html}` | Crear | Smart, reactive forms: campos de la tabla de UX; identificador de solo lectura en edición; **Incluir prereleases** visible solo para GitHub/PyPI; validaciones de ayuda (slug, 1–720, http/https); botón **Probar feed**; errores del backend junto a cada campo; diálogo *Guardar igualmente / Corregir* |
| Presentación | `features/news-sources/pages/news-source-detail/news-source-detail.component.{ts,html}` | Crear | Smart: campos en lectura, estado, auditoría, acciones Editar / Validar ahora / Activar-Desactivar / Eliminar y bloque **Prompt de clasificación** |
| Presentación | `features/news-sources/components/feed-check-result/feed-check-result.component.{ts,html}` | Crear | Dumb: resultado de *Probar feed* / *Validar ahora* (título, entradas, pasan filtros, última entrada, o el error) |
| Presentación | `features/news-sources/components/prompt-template-block/prompt-template-block.component.{ts,html}` | Crear | Dumb: plantilla aplicada (propia o genérica de "Vigilancia") y enlace **Personalizar** → `/plantillas-prompt/nueva?category=vigilancia&identifier={code}` o a la edición de la propia si existe |
| Presentación | `shared/components/status-badge/status-badge.component.ts` | Modificar | Variantes `pending` (gris), `ok` (verde), `error` (rojo) |
| Presentación | `features/prompt-templates/pages/prompt-template-form/prompt-template-form.component.ts` | Modificar | Lee los *query params* `category` e `identifier` para proponerlos en el alta (ESP-06, flujo *Personalizar el prompt*) |
| Integración | `app.routes.ts` | Modificar | Ruta hija `fuentes-noticias` con `loadChildren` de `NEWS_SOURCES_ROUTES`, bajo el shell con `authGuard` (sin `roleGuard`, ESP-14 Regla 3) |
| Integración | `core/layout/shell/shell.component.html` | Modificar | Entrada **Maestros › Fuentes de noticias** |

No hay URLs de Figma en el issue (solo el prototipo general sin rutas ni `node-id`), así que no se añade sección de Diseño (Figma) y la UI se construye a mano siguiendo la Descripción de UX.

## 6. Plan de pruebas

Backend en `back/tests/`; frontend en `front/src/app/features/news-sources/**/*.spec.ts`. Los feeds se prueban con fixtures grabadas (`tests/fixtures/feeds/*.xml`) servidas con `httpx.MockTransport`, nunca contra los sitios reales en CI.

| Test | Tipo | Escenario | Resultado esperado |
|---|---|---|---|
| `test_validate_source_url_pypi_with_project_page_raises_validation_exception_with_expected_pattern` | Unitario | Tipo PyPI, URL `https://pypi.org/project/langchain/` (Criterio 3) | `ValidationException(field="url")` cuyo mensaje contiene `https://pypi.org/rss/project/{paquete}/releases.xml` |
| `test_validate_source_url_github_releases_atom_is_accepted` | Unitario | `https://github.com/langchain-ai/langchain/releases.atom` | Sin error |
| `test_validate_source_url_rss_atom_with_ftp_scheme_raises_validation_exception` | Unitario | RSS/Atom con `ftp://…` | `ValidationException(field="url")` |
| `test_title_filter_with_invalid_exclude_regex_raises_validation_exception_on_exclude_field` | Unitario | Exclusión `^VSCode (Extension` (Criterio 4) | `ValidationException(field="exclude_pattern")` |
| `test_title_filter_with_pattern_over_500_chars_raises_validation_exception` | Unitario | Patrón de 501 caracteres | `ValidationException` en el campo del filtro |
| `test_title_filter_applies_include_then_exclude_case_insensitive` | Unitario | Inclusión `release`, exclusión `^vscode extension`; títulos variados | Solo pasan los que cumplen la inclusión y no la exclusión, sin distinguir mayúsculas |
| `test_news_source_with_frequency_out_of_range_raises_validation_exception` | Unitario | Frecuencia 0 y 721 | `ValidationException(field="fetch_frequency_hours")` |
| `test_news_source_rss_atom_forces_include_prereleases_false` | Unitario | RSS/Atom con `include_prereleases=True` | La entidad queda con `False` (Regla 12) |
| `test_create_news_source_with_valid_github_feed_creates_enabled_source_with_ok_status` | Unitario | Validador mock devuelve feed válido (Criterio 1) | `status=ok`, `enabled=True`, `created_by` = email |
| `test_create_news_source_pypi_defaults_include_prereleases_false` | Unitario | Alta PyPI sin indicar prereleases (Criterio 2) | `include_prereleases=False`, `status=ok` |
| `test_create_news_source_with_feed_404_and_no_force_raises_feed_validation_failed_and_saves_nothing` | Unitario | Validador devuelve error HTTP 404 (Criterio 5) | `FeedValidationFailedException` con el error; `save` no se llama |
| `test_create_news_source_with_feed_404_and_save_anyway_saves_with_error_status` | Unitario | Igual, con `save_even_if_feed_fails=True` (Criterio 5) | Se guarda con `status=error` |
| `test_create_news_source_with_duplicated_code_raises_validation_exception_on_code` | Unitario | `exists_with_code=True` (Criterio 6) | `ValidationException("El identificador ya existe", field="code")`; no valida el feed |
| `test_create_news_source_with_duplicated_url_different_case_raises_validation_exception_on_url` | Unitario | URL existente en mayúsculas (Regla 3) | `ValidationException(field="url")` |
| `test_update_news_source_changing_url_revalidates_feed_and_sets_ok` | Unitario | Fuente en `error`, nueva URL válida (Criterio 7) | Se llama al validador; `status=ok` |
| `test_update_news_source_changing_only_filters_does_not_revalidate_feed` | Unitario | Solo cambia el filtro de exclusión (Regla 11) | El validador no se llama; el estado se conserva |
| `test_delete_news_source_with_news_raises_in_use_exception_with_count` | Unitario | `count_news=12` (Criterio 10) | `NewsSourceInUseException(news_count=12)`; `delete` no se llama |
| `test_test_news_source_feed_returns_matching_count_and_persists_nothing` | Unitario | Feed de 5 entradas, 2 excluidas por el filtro | `entry_count=5`, `matching_count=3`; ningún método de escritura del repositorio se llama |
| `test_get_news_source_without_specific_template_returns_generic_prompt_block` | Unitario | Solo existe `vigilancia/generico` | Bloque con `is_specific=False` e identificador `generico` |
| `test_feed_validator_with_recorded_atom_fixture_returns_title_and_entries` | Integración | Fixture Atom de releases de GitHub | `ok=True`, título y nº de entradas correctos |
| `test_feed_validator_with_http_404_returns_error_result` | Integración | Respuesta 404 | `ok=False`, error con el código HTTP |
| `test_feed_validator_with_html_page_returns_not_a_feed_error` | Integración | HTML sin feed | `ok=False` (sin título ni entradas) |
| `test_feed_validator_when_robots_txt_disallows_returns_error_result` | Integración | `robots.txt` con `Disallow: /` para el bot | `ok=False` sin descargar el feed |
| `test_feed_validator_sends_bot_user_agent_on_every_request` | Integración | Captura cabeceras en `MockTransport` | `User-Agent` = `BOT_USER_AGENT` en `robots.txt` y en el feed |
| `test_feed_validator_with_more_than_5_redirects_returns_error_result` | Integración | Cadena de 6 redirecciones | `ok=False` |
| `test_feed_validator_with_private_ip_host_returns_error_result` | Integración | URL que resuelve a `127.0.0.1` / `169.254.169.254` | `ok=False` sin realizar la petición |
| `test_news_sources_endpoint_without_token_returns_401` | Integración | `GET /api/v1/news-sources` sin `Authorization` | 401 |
| `test_create_news_source_endpoint_with_valid_token_returns_201_and_lists_it` | Integración (BD) | Alta con token válido y validador de fixtures (Criterio 1) | 201; aparece en `GET` con `created_by` = email del token |
| `test_create_news_source_endpoint_with_invalid_pattern_url_returns_422_with_url_field` | Integración (BD) | Criterio 3 | 422 `{field: "url"}`; no se inserta fila |
| `test_create_news_source_endpoint_with_unreachable_feed_returns_422_feed_invalid` | Integración (BD) | Criterio 5 sin forzar | 422 `{code: "feed_invalid"}` |
| `test_create_news_source_endpoint_with_duplicated_code_returns_422_on_code` | Integración (BD) | Criterio 6 | 422 `{field: "code", detail: "El identificador ya existe"}` |
| `test_set_news_source_enabled_false_persists_and_updates_audit` | Integración (BD) | Criterio 8 | `enabled=false`, `updated_by` = email |
| `test_delete_news_source_without_news_removes_row` | Integración (BD) | Criterio 9 | 204 y la fila ya no existe |
| `test_delete_news_source_with_news_returns_409_with_news_count` | Integración (BD) | Criterio 10 — **pendiente de ESP-07** (`# TODO: ESP-07`, requiere tabla `news`) | 409 `{news_count: N}`; la fila sigue existiendo |
| `test_list_news_sources_filtered_by_error_status_returns_only_error_sources` | Integración (BD) | Fuentes en `pending`/`ok`/`error` (Criterio 11) | Solo las de `error`; `total` coherente |
| `test_list_news_sources_default_order_is_by_name` | Integración (BD) | Sin parámetros de orden | Ordenado por `name asc` |
| `test_seed_news_sources_script_is_idempotent` | Integración (BD) | Ejecutar la semilla dos veces | Mismo número de filas; todas `pending` |
| `news-source-form: shows include prereleases only for github and pypi types` | Unitario (front) | Cambio de tipo en el formulario | El interruptor aparece/desaparece |
| `news-source.service: maps 422 feed_invalid to save-anyway warning and resubmits with flag` | Unitario (front) | Repositorio mock devuelve 422 `feed_invalid` | Se expone la advertencia; *Guardar igualmente* reenvía con `saveEvenIfFeedFails: true` |
| `news-source.service: maps 409 on delete to deactivate offer` | Unitario (front) | Repositorio mock devuelve 409 | Se expone la oferta de desactivar con el nº de noticias |

## 7. Notas y decisiones de diseño

- **D1 — Regla 8 sin tabla `news` (conviene confirmarla al aprobar).** Las noticias las crea ESP-07, que aún no existe. Decisión: `INewsSourceRepository.count_news(source_id)` forma parte del contrato desde ya; su implementación devuelve `0` con `# TODO: ESP-07` y el plan de ESP-07 debe sustituirla por `SELECT count(*) FROM news WHERE source_id = $1` y declarar la FK `news.source_id → news_source(id)` **sin** `ON DELETE CASCADE`, para que la BD proteja la integridad aunque falle la comprobación. El caso de uso ya tiene la lógica y su test unitario; el test de integración del 409 queda marcado como pendiente de ESP-07. Alternativa descartada: crear ahora una tabla `news` mínima, que adelantaría decisiones de esquema de ESP-07 (URL canónica, `guid`, estados, datos estructurados) sin su análisis.
- **D2 — Índices únicos no escritos en la especificación (confirmar).** El DDL de ESP-06 no tiene `UNIQUE`, pero las Reglas 2 y 3 exigen unicidad de `code` y de `url` sin distinguir mayúsculas. La validación la hace la aplicación (Regla 10); los índices `ux_news_source_code` y `ux_news_source_url (lower(url))` son restricciones de integridad permitidas por la constitución §2.7, protegen de dos altas simultáneas y hacen idempotente la semilla (`ON CONFLICT (code)`). El `CREATE TABLE` se mantiene literal; los índices van aparte. Si se prefiere no tocar el esquema, la carrera entre dos altas simultáneas queda sin cubrir.
- **D3 — *Guardar igualmente* como segunda petición.** `POST`/`PUT` aceptan `save_even_if_feed_fails` (por defecto `false`). Sin él, un feed inválido responde 422 `code: "feed_invalid"` con el error y no guarda; Angular muestra la advertencia y, si el usuario elige *Guardar igualmente*, reenvía con el indicador y la fuente queda "En error". Así la validación ocurre siempre en el backend y no hay estado intermedio. Alternativa descartada: guardar siempre y devolver un aviso, que dejaría fuentes creadas cuando el usuario elige *Corregir*.
- **D4 — Errores de campo de uno en uno.** Se reutiliza `ValidationException(message, field)` de ESP-13, que informa del primer campo erróneo. Las validaciones de ayuda de Angular cubren la mayoría de los campos a la vez; si se quiere mostrar todos los errores del backend a la vez, habría que ampliar el contrato 422 para ESP-06 y ESP-13 juntos (fuera de este plan).
- **D5 — *Probar feed* y prereleases.** "Cuántas pasan los filtros" cuenta solo los filtros de inclusión y exclusión (Regla 11). Detectar prereleases necesita los adaptadores de ESP-07 (versión desde el tag o el título), que viven en `func/`. Duplicarlos ahora en el backend adelantaría ESP-07; se documenta en la respuesta y se puede ampliar cuando exista el adaptador.
- **D6 — *Validar ahora* no toca la auditoría.** Solo cambia `status`. La Regla 9 audita altas y modificaciones de los datos del maestro, y una validación no los modifica. Guardar (con o sin revalidación) y Activar/Desactivar sí actualizan `updated_at`/`updated_by`.
- **D7 — SSRF en la validación de feeds.** El backend descarga URLs que escribe el usuario desde App Service. Aunque el endpoint exige token, el validador rechaza hosts que resuelven a direcciones privadas, *loopback* o *link-local* (incluido `169.254.169.254`, metadatos de Azure) y comprueba cada salto de redirección. El error se muestra como fallo de validación normal.
- **D8 — Fuentes semilla.** Las 5 obligatorias de la especificación, más `pypi-{paquete}` para los SDK de Python del catálogo semilla que nombra ESP-04 (openai, anthropic, langchain, llama-index, transformers), y blogs/changelogs de proveedores de IA con feed hasta 10–15. Las URLs no se comprueban al cargar: quedan `pending` hasta su primera validación, como dice la especificación. La lista definitiva de URLs de proveedores se fija al implementar, comprobando que cada una publica feed.
- **D9 — Regex de usuario.** Los filtros se compilan con `re` de Python (el mismo motor en `back/` y `func/`) y se aplican sobre títulos cortos. El límite de 500 caracteres acota el riesgo de expresiones patológicas (ReDoS); no se añade un motor alternativo en el MVP.
- **D10 — `include_prereleases` en RSS/Atom.** La entidad lo fuerza a `false` cuando el tipo es `rss_atom`, en vez de guardar un valor que se ignoraría: la BD refleja el comportamiento real y el formulario ni siquiera muestra el interruptor.
- **D11 — Orden de integración.** ESP-13 (back y front) debe mergearse a `develop` antes de crear `feature/ESP-06`: este plan reutiliza su pool de PostgreSQL, sus excepciones genéricas, `validate_slug`, `IPromptTemplateRepository` y los componentes compartidos del frontend.
- **D12 — Categoría `vigilancia` como constante.** `NEWS_CLASSIFICATION_PROMPT_CATEGORY = "vigilancia"` se define una vez en el dominio junto a `GENERIC_IDENTIFIER`. No es un prompt ni una regla de negocio configurable: es la clave con la que ESP-06 y ESP-08 se refieren al mismo grupo de plantillas (constitución §3.5).
