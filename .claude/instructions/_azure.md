# Experto: Azure — OneWatch

## Infraestructura del proyecto

| Servicio | Rol |
|---|---|
| Azure App Service (Linux, contenedor) | Backend (API REST FastAPI + endpoint de interactividad de Slack), desplegado a partir de una imagen publicada en Azure Container Registry |
| Azure Container Registry | Registro privado de imágenes del backend; el pipeline de CI/CD construye y publica, App Service hace `pull` vía Managed Identity |
| Azure Functions (**una única Function App**, Timer Triggers) | Tareas programadas de revisión de fuentes externas (GitHub, feeds, LLM) y validación de impacto sobre las aplicaciones (resolución de usos, correlación, notificación). Aloja también los comandos CLI |
| Azure PostgreSQL Flexible Server | Persistencia operacional de todo el sistema, compartida por backend y Function |
| Azure OpenAI | Clasificación de noticias con salida estructurada en JSON (ESP-08) |
| Azure Storage Account | `AzureWebJobsStorage` del runtime de la Function (locks de Timer Triggers) |
| App Settings | Variables de entorno en producción de App Service y Function App (aplicación pequeña; no se usa Key Vault) |
| Microsoft Entra ID | Identidad de los usuarios (ESP-14): registro de aplicación `onewatch-api` (*scope* `access_as_user`, *App Roles* `admin` / `user`), registro `onewatch-spa` (SPA, cliente público) y aplicación empresarial con asignación obligatoria. También provee las Managed Identities. Los registros los crea el proyecto de infraestructura |

**Servicios externos (no Azure):**

| Servicio | Uso |
|---|---|
| API de GitHub | Validación de acceso a repositorios (ESP-01), SBOM del dependency graph (ESP-02), descarga del contenido de la rama (ESP-03) |
| Feeds RSS/Atom y páginas de noticias | Validación de fuentes (ESP-06) e ingesta (ESP-07) |
| Slack | Webhook entrante para digest y alertas P1 (ESP-10); interactividad para valorar alertas (ESP-11) |
| SMTP | Email del digest por responsable (ESP-10) |

---

## Identidad y secretos

- **Entra ID autentica a los usuarios** (ESP-14). El frontend obtiene tokens de acceso con MSAL; el backend los valida sin secretos (claves públicas del JWKS del tenant, en caché) comprobando firma, emisor, audiencia (`ENTRA_API_CLIENT_ID`), expiración y *scope*. OneWatch no emite tokens ni guarda contraseñas.
- Roles como *App Roles* de `onewatch-api`, asignados a usuarios o, preferiblemente, a grupos en la aplicación empresarial. Con "Asignación obligatoria" activa, una cuenta sin rol no obtiene token.
- El tiempo de vida del token lo fija Entra ID; una baja o un cambio de rol surte efecto al renovarse el token (no se usa Continuous Access Evaluation en el MVP).
- Managed Identity asignada por sistema para acceder a los recursos Azure que lo admiten (ACR `AcrPull`, Storage, Azure OpenAI, PostgreSQL); sin claves estáticas cuando exista alternativa.
- Secretos que no admiten Managed Identity (token o credenciales de GitHub App, signing secret y webhook de Slack, credenciales SMTP) en App Settings marcados como valor sensible / *slot setting*; nunca en repositorio ni en logs. Los identificadores de Entra ID (tenant, client ids, *scope*) no son secretos.

---

## Azure Functions — Function App única (`func/`)

### Principio

Existe **una sola Function App** para todas las tareas de fondo (constitución §3.2). Cada proceso es un caso de uso; los Timer Triggers y los comandos CLI son solo puntos de entrada que los invocan, sin duplicar lógica.

### Pipelines programados

Los procesos que deben ejecutarse encadenados ("tras `import-sbom`", "después de cada ingesta", "después de `classify-news` y `resolve-usages`") se encadenan dentro del mismo Timer Trigger, en orden, para no depender de coincidencias de horario:

| Timer Trigger | Horario (NCRONTAB, configurable por App Setting) | Secuencia de casos de uso |
|---|---|---|
| `inventory_pipeline` | Diario (`%INVENTORY_SCHEDULE%`) | `sync-apps` → `import-sbom` → `resolve-usages` → `scan-ai` → `resolve-usages` → `correlate` |
| `news_pipeline` | Cada hora (`%NEWS_SCHEDULE%`, por defecto `0 0 * * * *`) | `ingest-news` → `classify-news` → `correlate` (incluye el envío inmediato de alertas P1 a Slack) |
| `weekly_digest` | Lunes 08:00 (`%DIGEST_SCHEDULE%`, por defecto `0 0 8 * * 1`) | `send-digest` |

```python
@app.timer_trigger(arg_name="timer", schedule="%NEWS_SCHEDULE%", run_on_startup=False)
async def news_pipeline(timer: func.TimerRequest) -> None:
    await run_news_pipeline()   # ingest → classify → correlate, cada paso registra su actividad
```

- Cada paso del pipeline registra su propia ejecución (proceso, resultado, duración) para **Sistema › Actividad**. El fallo de un paso se registra y **no** impide ejecutar los pasos siguientes que no dependan de él.
- Los Timer Triggers son singleton (lock en `AzureWebJobsStorage`): no hay dos ejecuciones simultáneas del mismo pipeline. Si `inventory_pipeline` y `news_pipeline` ejecutan `correlate` a la vez, la idempotencia (índice único noticia–aplicación) evita alertas duplicadas.
- El horario del digest se interpreta en la zona horaria configurada en la Function App (`WEBSITE_TIME_ZONE` / `TZ` según el plan); por defecto es UTC.
- Duración: `scan-ai` sobre repositorios grandes puede ser lento. El plan de hosting y el `functionTimeout` de `host.json` deben cubrir la duración del pipeline de inventario (TODO: fijar plan de hosting).

### Comandos CLI

Los comandos de las especificaciones se ejecutan desde `func/` con un único punto de entrada (`python -m src.cli <comando> [opciones]`) que invoca los mismos casos de uso:

`sync-apps`, `sync-catalog`, `import-sbom [repo]`, `scan-ai [repo]`, `resolve-usages`, `list-unresolved`, `export-bom <aplicación> --output <ruta>`, `ingest-news [fuente]`, `classify-news`, `show-news <id>`, `correlate`, `list-alerts`, `send-digest [--dry-run]`, `rate-alert <id> <valoración>`, `alert-stats`.

### Archivos de configuración

`applications.yaml`, `catalog.yaml` y `ai-detectors.yaml` se leen desde la ruta indicada en App Settings (`APPLICATIONS_YAML_PATH`, `CATALOG_YAML_PATH`, `AI_DETECTORS_YAML_PATH`). Ubicación en ejecución (empaquetados con `func/` o en Storage): TODO.

### Estructura de `func/` (proyecto independiente)

`func/` es un repositorio GitHub independiente desplegable sin dependencia del backend. Replica la Clean Architecture de `back/src/` (mismas reglas de [`_python.md`](_python.md)), omitiendo lo que no aplica a un procesador sin API REST:

```
func/
├── function_app.py       # entry point: los Timer Triggers (ver arriba)
├── host.json
├── requirements.txt
└── src/
    ├── cli.py             # entry point CLI: mapea cada comando a su caso de uso
    ├── application/       # use_cases/, services/ (pipelines) y dtos/
    ├── core/              # configuration/, dependencies/, exceptions/ de func/
    ├── domain/            # entities/, enums/, interfaces/, value_objects/
    └── infrastructure/    # postgresql/, github/, feeds/, llm/, slack/, email/
tests/
└── unit/
```

- Se omite `api/` (no expone API REST) y `scripts/` (el DDL es de `back/scripts/DB/`).
- **Identidad:** Managed Identity para Storage, Azure OpenAI y PostgreSQL.
- **Idempotencia:** todas las escrituras usan claves de negocio únicas y upsert (constitución §2.5).

---

## Integración con GitHub

- Autenticación con GitHub App o token de solo lectura (`contents:read`, `metadata:read`).
- SBOM: `GET /repos/{owner}/{repo}/dependency-graph/sbom` (SPDX JSON); el purl se toma de las referencias externas de cada paquete. El SBOM crudo se guarda para auditoría (columna JSONB o blob; decidir en el análisis de ESP-02).
- Contenido: tarball de la rama vía API o clonado superficial (`--depth 1`) en directorio `.tmp_`, eliminado en `finally`.
- Rate limit: leer `x-ratelimit-remaining` y `x-ratelimit-reset`; al agotarse, pausar hasta el reset y reanudar sin duplicar instantáneas.

---

## Recolección de fuentes (feeds y páginas)

- `feedparser` para feeds; `trafilatura` para extraer el texto principal de las páginas.
- User-Agent de bot identificable (`BOT_USER_AGENT`, ej. `VigilanciaTecBot/1.0 (+url-de-contacto)`) en **todas** las peticiones, y respeto de `robots.txt`. Nunca un User-Agent de navegador (Azure Updates devuelve 403).
- Timeout de 10 s y máximo 5 redirecciones.
- Peticiones condicionales con `ETag` / `If-Modified-Since`; `304 Not Modified` cuenta como consulta correcta.
- La validación del maestro (Probar feed / Validar ahora) se ejecuta en el **backend**; la ingesta, en la **Function**. Ambos usan la misma configuración de User-Agent y timeouts.

---

## Azure OpenAI

### Deployments

| Deployment | Modelo | Uso |
|---|---|---|
| `AOAI_CLASSIFY_DEPLOYMENT` | TODO | Clasificación de noticias (ESP-08) |

### Reglas

- Salida estructurada con esquema JSON (structured output / tool use) y validación posterior con Pydantic contra los valores admitidos de ESP-08 (tipo de evento, severidad, componentes del catálogo, resumen ≤ 300 caracteres).
- El prompt se resuelve siempre en el maestro de plantillas (ESP-13); nunca se construye con texto hardcodeado.
- JSON inválido o valores fuera de rango: 1 reintento; si falla de nuevo, "error de clasificación".
- Error de la API o throttling (429): la noticia sigue "pendiente de clasificar" y se reintenta en la siguiente ejecución.
- Guardar siempre el nombre del modelo/deployment y la respuesta cruda.
- Si el catálogo crece, enviar solo un subconjunto de identificadores preseleccionado por coincidencia de alias en el texto.
- Monitorizar TPM (tokens per minute) del deployment.

---

## Slack y email

- **Webhook entrante** (`SLACK_WEBHOOK_URL`): digest semanal y alertas P1 inmediatas, con Block Kit. Plantillas Jinja2 compartidas para Markdown (`--dry-run`), Slack y HTML.
- **Interactividad** (`/api/v1/slack/actions` en el backend): verifica la firma (`X-Slack-Signature`, `X-Slack-Request-Timestamp`, `SLACK_SIGNING_SECRET`) antes de procesar; tras valorar, sustituye los botones por el texto de la valoración.
- **SMTP**: un email por responsable con solo sus aplicaciones.
- Fallo de envío: 3 reintentos; si persiste, las alertas no se marcan "notificada" y se registra el error.

---

## Azure Container Registry + Azure App Service

### Registro de imágenes

- Repositorio `onewatch-api` en Azure Container Registry (ACR); el pipeline de CI/CD construye la imagen del backend y hace `push` a ACR en cada release.
- Imagen base: `mcr.microsoft.com/devcontainers/python:3.12`.
- Acceso de App Service a ACR: **Managed Identity + AcrPull** (rol RBAC), sin admin user ni credenciales estáticas.

### App Service desplegado

| App | Rol | Escalado |
|---|---|---|
| `onewatch-api` (Web App for Containers, Linux) | Backend FastAPI (API REST + interactividad de Slack), imagen `<acr>.azurecr.io/onewatch-api:<tag>` | Autoscale por CPU/memoria |

### Reglas
- Identidad: Managed Identity asignada por sistema; sin claves estáticas en variables de entorno.
- Health probes: `/health` para el API (Health Check de App Service).
- Continuous deployment: en producción se prefiere un paso explícito desde el pipeline de CI/CD.
- `WEBSITES_PORT` configurado al puerto que expone Uvicorn dentro del contenedor.

---

## Configuración de entorno

| Variable | Componente | Propósito |
|---|---|---|
| `DATABASE_URL` | back, func | Conexión PostgreSQL (Azure Flexible Server) |
| `ENTRA_TENANT_ID` | back | Tenant corporativo de Entra ID (emisor esperado y JWKS) |
| `ENTRA_API_CLIENT_ID` | back | Client id de `onewatch-api` (audiencia esperada del token) |
| `ENTRA_API_SCOPE` | back | *Scope* requerido en el claim `scp` (`access_as_user`) |
| `CORS_ALLOWED_ORIGINS` | back | Origen(es) del frontend |
| `SLACK_SIGNING_SECRET` | back | Verificación de firma de la interactividad de Slack |
| `BOT_USER_AGENT` | back, func | User-Agent de bot para feeds y páginas |
| `GITHUB_TOKEN` (o `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY` + `GITHUB_APP_INSTALLATION_ID`) | func | Acceso de solo lectura a la API de GitHub |
| `APPLICATIONS_YAML_PATH` / `CATALOG_YAML_PATH` / `AI_DETECTORS_YAML_PATH` | func | Rutas de los archivos de configuración |
| `AOAI_ENDPOINT` | func | Endpoint de Azure OpenAI |
| `AOAI_CLASSIFY_DEPLOYMENT` | func | Deployment de clasificación |
| `SLACK_WEBHOOK_URL` / `SLACK_CHANNEL` | func | Canal del digest y de las alertas P1 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | func | Envío del digest por email |
| `INVENTORY_SCHEDULE` / `NEWS_SCHEDULE` / `DIGEST_SCHEDULE` | func | Expresiones NCRONTAB de los Timer Triggers |
| `AzureWebJobsStorage` | func | Storage del runtime de la Function |

Referencia completa: `.env.example`
Entorno de desarrollo: `.env` (back) / `local.settings.json` (func)
Producción: App Settings de App Service y Function App

---

## Azure PostgreSQL

- DDL completo en `back/scripts/DB/DB.sql` (único dueño del esquema, compartido por back y func); cambios incrementales en `back/scripts/DB/migrations/`; datos semilla en `back/scripts/DB/seed/` (10–15 fuentes, plantilla `vigilancia`/`generico`). No hay usuario semilla: el primer Administrador es quien tenga el *App Role* `admin` en Entra ID.
- Las tablas definidas en las especificaciones (`news_source`, `prompt_template`) se crean exactamente con el DDL de la especificación; el resto se define en el análisis de cada ESP.
- Solo restricciones de integridad (PK, FK, `UNIQUE`, `NOT NULL`, `DEFAULT`); sin triggers ni lógica (constitución §2.7).
- Claves únicas relevantes: `key` de aplicación, `owner/nombre` de repositorio, identificador canónico de componente, alias normalizado, (categoría, identificador) de plantilla, (noticia, aplicación) de alerta.
- Consulta/vista `component_usage_current` (uso vigente ⨝ repositorio ⨝ aplicación): base de ESP-09 y ESP-12.
- Pool de conexiones: `PostgreSQLConnection` (singleton) en `src/infrastructure/postgresql/connection.py`.
- Si el pool lanza `RuntimeError("Pool de conexiones no inicializado")`, verificar que `load_dotenv()` se ejecuta antes de instanciar cualquier repositorio.

---

## Patrones obligatorios en clientes externos

Todos los clientes externos se definen como **interfaces** (ABC) en `domain/interfaces/` y se implementan en `infrastructure/`. Esto es lo que permite que los use cases sean mockeables en tests.

```python
class ISourceCodeHost(ABC):
    """Repositorios de código (implementación: API de GitHub)."""

    @abstractmethod
    async def check_access(self, repository: RepositoryRef) -> RepositoryAccess: ...

    @abstractmethod
    async def get_sbom(self, repository: RepositoryRef) -> RawSbom: ...

    @abstractmethod
    async def download_tree(self, repository: RepositoryRef, target_dir: Path) -> Path: ...


class IFeedReader(ABC):
    @abstractmethod
    async def fetch(self, request: FeedFetchRequest) -> FeedFetchResult: ...   # ETag / Last-Modified incluidos


class IPageTextExtractor(ABC):
    @abstractmethod
    async def extract_main_text(self, url: str) -> PageText | None: ...


class INewsClassifier(ABC):
    """Clasificación con LLM (implementación: Azure OpenAI)."""

    @abstractmethod
    async def classify(self, prompt: RenderedPrompt) -> RawClassification: ...


class IChatNotifier(ABC):
    """Mensajería del equipo (implementación: Slack)."""

    @abstractmethod
    async def publish_digest(self, digest: Digest) -> None: ...

    @abstractmethod
    async def publish_alert(self, alert: Alert) -> None: ...


class IEmailSender(ABC):
    @abstractmethod
    async def send(self, message: EmailMessage) -> None: ...
```

### Consultas paralelas

Cuando se invoque a múltiples servicios externos simultáneamente (p. ej. varias fuentes o repositorios), usar `asyncio.gather` con `return_exceptions=True` para que un fallo aislado no detenga el resto, acotando la concurrencia (semáforo) para respetar rate limits:

```python
results = await asyncio.gather(
    *[ingest_source(source) for source in due_sources],
    return_exceptions=True,
)
```

Los elementos que fallen se registran con warning y en el resumen de ejecución, pero **no bloquean** el procesamiento del resto.
