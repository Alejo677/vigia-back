# Experto: Python & Arquitectura Limpia

## Capas y responsabilidades

Python 3.12 con **FastAPI** y arquitectura limpia (Clean Architecture). Estas reglas aplican a `back/` y, salvo la sección FastAPI, también a `func/` (ver estructura de `func/` en [`_azure.md`](_azure.md)).

**Estructura del proyecto** · Repositorio independiente: `back/`

```
back/
  pyproject.toml              # build system, dependencias y configuración de herramientas (ruff, mypy, pytest)
  scripts/
    DB/
      DB.sql                  # DDL completo (único dueño del esquema, compartido con func/)
      migrations/             # scripts incrementales de esquema
      seed/                   # datos iniciales: fuentes semilla, plantilla vigilancia/generico
    Azure/
    Deployment/
      config/
  src/
    main.py                   # entrada FastAPI: crea app, registra routers, configura middleware
    api/
      v1/
        routers/              # un router por recurso (auth, news_sources, prompt_templates, inventory, catalog, alerts, activity, slack)
    application/
      services/               # orquestadores: coordinan use cases y dependencias externas
      dtos/                   # Data Transfer Objects con los schemas de request/response (API y casos de uso)
      use_cases/              # un archivo por caso de uso; lógica de aplicación pura
    core/
      configuration/          # Settings con pydantic-settings; carga desde variables de entorno
      dependencies/           # providers de FastAPI (get_db, get_current_user → valida el token de Entra ID, require_role, etc.)
      exceptions/             # excepciones de aplicación y handlers HTTP globales
    domain/
      entities/               # clases de dominio puras (sin ORM, sin Pydantic)
      enums/                  # enumeraciones (ej. NewsSourceType, NewsSourceStatus, UserRole)
      interfaces/             # ABCs que definen contratos de repositorios y servicios
      value_objects/          # objetos de valor inmutables (ej. CanonicalId, NormalizedAlias, Purl)
    infrastructure/
      postgresql/
        connection.py         # PostgreSQLConnection: pool singleton
        base_repository.py    # PostgreSQLBaseRepository: execute_query / execute_update
        repositories/         # implementaciones concretas de los repositorios del dominio
      auth/                   # validación de tokens de acceso de Entra ID (JWKS del tenant en caché, PyJWT[crypto]); no emite tokens
      feeds/                  # validación de feeds con feedparser (Probar feed / Validar ahora)
      slack/                  # verificación de firma y actualización de mensajes de Slack
  tests/
    unit/                     # pruebas de use cases y domain (sin I/O)
    integration/              # pruebas con BD real y servicios reales o emulados
    conftest.py               # fixtures compartidos (cliente de prueba, BD, mocks)
```

## Interfaces

* Toda lógica de negocio depende de interfaces (`domain/interfaces/`), nunca de implementaciones concretas de infraestructura.

  ```python
  # ✅ Correcto
  def __init__(self, sources: INewsSourceRepository, feed_validator: IFeedValidator): ...

  # ❌ Incorrecto
  def __init__(self, sources: PostgreSQLNewsSourceRepository, feed_validator: FeedparserValidator): ...
  ```
* Las interfaces se nombran con el concepto de negocio y la implementación con el detalle técnico, NO el nombre de la infraestructura a implementar.

* Todas las interfaces implementarán Abstract Base Class (ABC) y los métodos @abstractmethod
   ```python
   class INewsSourceRepository(ABC):

       @abstractmethod
       async def save(self, source: NewsSource) -> NewsSource: ...

       @abstractmethod
       async def update_enabled(self, change: NewsSourceEnabledChange) -> None: ...
   ```

* Cada interfaz se define en un archivo .py independiente en domain/interfaces/

* Los métodos de las interfaces reciben entidades de dominio (domain/entities) no datos primitivos. Excepción: consultas por identificador único aceptan el primitivo directamente.

* Toda dependencia externa (Azure, GitHub, Slack, SMTP, feeds, terceros) se define como interfaz (`ABC`) en `domain/interfaces/` y se implementa en `infrastructure/`. Esto es lo que permite que los use cases sean mockeables en tests.

---

## Entidades de dominio

* Es opcional que sean inmutables
* Es opcional su validación, en caso de necesitarse se hará con `__post_init__`:

```python
@dataclass
class NewsSource:
    code: str
    name: str
    url: str
    source_type: NewsSourceType
    fetch_frequency_hours: int
    enabled: bool
    include_pattern: str | None
    exclude_pattern: str | None
    include_prereleases: bool
    status: NewsSourceStatus
    updated_by: str

    def __post_init__(self) -> None:
        if not SLUG_PATTERN.fullmatch(self.code):
            raise ValueError("El identificador debe tener formato slug")
        if not MIN_FREQUENCY_HOURS <= self.fetch_frequency_hours <= MAX_FREQUENCY_HOURS:
            raise ValueError("La frecuencia debe estar entre 1 y 720 horas")

@dataclass(frozen=True, slots=True)
class NewsSourceEnabledChange:
    source_id: UUID
    enabled: bool
    updated_by: str
```

* Cada entidad de dominio se crea en un archivo .py independiente.
* Las reglas de negocio de las especificaciones (formato slug, rangos, patrón de URL por tipo, regex válidas) se validan en la aplicación, nunca en la base de datos (constitución §2.7).
---

## Enumeraciones de dominio relevantes

```python
class NewsSourceType(str, Enum):
    RSS_ATOM = "rss_atom"
    GITHUB_RELEASES = "github_releases"
    PYPI_RELEASES = "pypi_releases"


class NewsSourceStatus(str, Enum):
    PENDING = "pending"
    OK = "ok"
    ERROR = "error"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class AlertPriority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
```

* Otros enums del dominio: `Criticality` (alta, media, baja), `ComponentType` (librería, modelo, proveedor), `EventType` y `Severity` (valores cerrados de ESP-08), `NewsStatus`, `AlertStatus`, `AlertRating` y `NoiseReason` (ESP-11), `UsageOrigin` (SBOM, escaneo).
* Cada enumeración se crea en un archivo .py independiente.
---

## Infraestructura

* La infraestructura no debería recibir parámetros primitivos sueltos, debe recibir objetos ya definidos en el dominio.

* Cada repositorio se define como interfaz en `domain/interfaces/` y se implementa en la carpeta
correspondiente de `infrastructure/` según la tecnología concreta (ej. `infrastructure/postgresql/`,
`infrastructure/github/`). El dominio nunca conoce la implementación.

```python
   class IPromptTemplateRepository(ABC):
       @abstractmethod
       async def get_active(self, key: PromptTemplateKey) -> PromptTemplate | None: ...

       @abstractmethod
       async def save_new_version(self, template: PromptTemplate) -> PromptTemplate: ...

       @abstractmethod
       async def get_by_id(self, template_id: UUID) -> PromptTemplate | None: ...
```

* Cada archivo de infraestructura retornará un único tipo de excepción específico para ellos. (ej. PostgreSQLBaseException para la infraestructura PostgreSQLBaseRepository)

* Cada infraestructura se genera en un archivo .py independiente.

* `PostgreSQLConnection` en `infrastructure/postgresql/connection.py` gestiona el pool singleton de conexiones.

* `PostgreSQLBaseRepository` en `infrastructure/postgresql/base_repository.py` hereda de esta conexión y provee los métodos `execute_query` / `execute_update` que usan los repositorios concretos.
---

## Casos de uso

* Responsabilidad única, solo inyección por constructor, sin lógica de infraestructura.

* Siempre trabaja con interfaces, no con la infraestructura directa.

```python
class CreateNewsSourceUseCase:
    def __init__(
        self,
        sources: INewsSourceRepository,
        feed_validator: IFeedValidator,
    ):
        self._sources = sources
        self._feed_validator = feed_validator

    async def execute(
        self,
        request: CreateNewsSourceRequest,
    ) -> NewsSourceResponse:
        # validar campos y unicidad, validar feed, crear fuente con estado resultante
        ...
```
* Captura y loguea todas las excepciones, lanzando propias excepciones del caso de uso, para lo cual se definirá una única excepción por caso de uso (ej. CreateNewsSourceException).

* Cada caso de uso se genera en un archivo .py independiente.

* Recibe y envía a la capa de APIs objetos DTO. los DTO no usan el sufijo DTO, solo XXRequest / XXResponse

* Recibe y envía a la capa de interfaces (infraestructura) entidades de dominio o Value Objects.

* Los procesos por lotes (`sync-apps`, `import-sbom`, `ingest-news`, …) son casos de uso que devuelven un resumen de ejecución (`XXSummary`) que el punto de entrada (CLI o Timer Trigger) imprime y registra en la actividad. El fallo de un elemento se registra en el resumen y no interrumpe el lote.
---

## Lógica compartida obligatoria

* **Normalización de alias** (ESP-04): una única función de dominio (minúsculas, sin espacios ni guiones) reutilizada por el catálogo, la resolución de usos y la clasificación. Nunca reimplementarla.
* **Validación de patrones de URL por tipo de fuente y de filtros regex** (ESP-06): lógica de dominio; el backend la usa al guardar y la Function al ingerir.
* **User-Agent de bot** (ESP-06): un único valor de configuración usado por la validación de feeds (back) y la ingesta (func).

---

## FastAPI

* Los objetos `XXRequest` y `XXResponse` en `application/dtos/` cumplen el rol de DTOs entre la API y los casos de uso. Se ha decidido no mantener schemas separados en `api/v1/schemas/` para evitar duplicación y conversiones sin valor añadido. El router recibe y devuelve directamente estos objetos:

  ```python
  # api/v1/routers/news_sources.py
  router = APIRouter(prefix="/news-sources", tags=["News sources"])

  @router.post("", response_model=NewsSourceResponse, status_code=201)
  async def create_news_source(
      request: CreateNewsSourceRequest,
      user: AuthenticatedUser = Depends(get_current_user),
      use_case: CreateNewsSourceUseCase = Depends(get_create_news_source_use_case),
  ) -> NewsSourceResponse:
      return await use_case.execute(request.with_user(user.email))
  ```


* Routers en `src/api/v1/routers/` — un archivo por recurso.
* Usar `Depends()` para inyección.
* Versionar siempre: `/api/v1/` (las rutas de las especificaciones, ej. `/api/news-sources`, se exponen como `/api/v1/news-sources`).
* Orden de middleware: CORS → Auth → Errors → Routes.
* `load_dotenv()` debe ser la primera línea de `src/main.py`.
* El router no contiene lógica: solo recibe el Request, delega al caso de uso y devuelve el Response.
* Todo router protegido declara `Depends(get_current_user)`; si un endpoint se restringe por rol, añade `Depends(require_role(UserRole.ADMIN))` (en el MVP ninguno). El router de Slack usa en su lugar la dependencia de verificación de firma.

* Manejo de excepciones

  * Cada endpoint captura las excepciones del caso de uso y las convierte en respuestas HTTP:

```python
  @router.delete("/{source_id}", status_code=204)
  async def delete_news_source(
      source_id: UUID,
      user: AuthenticatedUser = Depends(get_current_user),
      use_case: DeleteNewsSourceUseCase = Depends(get_delete_news_source_use_case),
  ) -> None:
      try:
          await use_case.execute(DeleteNewsSourceRequest(source_id=source_id))
      except NotFoundException as e:
          raise HTTPException(status_code=404, detail=e.message)
      except ConflictException as e:
          raise HTTPException(status_code=409, detail=e.message)   # fuente con noticias asociadas
      except DeleteNewsSourceException as e:
          raise HTTPException(status_code=502, detail=e.message)
```

* Cascada de excepciones: la infraestructura lanza las suyas (ej. `PostgreSQLBaseException`), el caso de uso las captura y lanza las propias (ej. `DeleteNewsSourceException`), y el endpoint las convierte en `HTTPException`.

* Los errores de validación de campos se devuelven con el campo afectado para que Angular los muestre junto a cada control (ESP-06, ESP-13, ESP-14).

---

## Async y paralelismo

* Usar `async/await` para toda operación I/O (BD, GitHub, feeds, Azure OpenAI, Slack, SMTP). Las llamadas independientes a servicios externos se ejecutan en paralelo con `asyncio.gather`:

  ```python
  results = await asyncio.gather(
      *[client.do_thing(item) for item in items],
      return_exceptions=True,
  )
  ```

* Nunca crear conexiones por petición; usar el pool de PostgreSQL.

---

## Logging

* Anteponer un emoji para diferenciar los logs del sistema, e incluir contexto en `extra`:

  ```python
  logger = logging.getLogger(__name__)
  logger.info("📦 SBOM importado", extra={"repository": repo, "snapshot_id": snap_id, "n_dependencies": n})
  logger.info("📰 Noticias ingeridas", extra={"source_code": code, "new": n_new, "discarded": n_disc})
  logger.info("🧠 Noticia clasificada", extra={"news_id": news_id, "model": model, "template_version": v})
  logger.info("🚨 Alerta generada", extra={"alert_id": alert_id, "application_key": app, "priority": prio})
  logger.warning("⚠️ Rate limit de GitHub, pausa hasta reset", extra={"reset_at": reset_at})
  logger.error("❌ Error en proceso", extra={"process": "ingest-news", "source_code": code, "error": str(e)})
  ```

* Nunca registrar contraseñas, tokens, secretos ni valores de variables de entorno detectadas.

  ---

## Reglas de calidad

- Funciones con una sola responsabilidad (guía: ≤ 20 líneas).
- Type hints en todas las firmas públicas.
- Docstrings en métodos públicos: `Args`, `Returns`, `Raises`.
- Sin números mágicos — usar constantes nombradas o los enums de dominio (los parámetros fijos están en la constitución §3.4).
- No duplicar código: extraer función cuando aparece por tercera vez.
- No sobre-abstraer: abstraer solo con 3+ casos de uso concretos.

---

## Gestión de recursos críticos

**Nunca** eliminar archivos de configuración en `__del__`. Solo archivos con prefijo `.temp_` o `.tmp_` pueden limpiarse automáticamente.

Los tarballs o clonados superficiales descargados por `scan-ai` se guardan en un directorio temporal con prefijo `.tmp_` y se eliminan **explícitamente** al final del escaneo de cada repositorio (en `finally`), nunca en un destructor.
