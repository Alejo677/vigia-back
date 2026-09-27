# Constitución del Proyecto: OneWatch

> Este archivo define los principios inmutables, restricciones funcionales y el alcance del proyecto.
> Toda decisión técnica, propuesta de cambio o generación de código debe respetar estas reglas
> sin excepción. Solo puede modificarse mediante decisión explícita y consensuada del equipo
> técnico responsable del proyecto.
>
> Las especificaciones funcionales del MVP están en `docs/Spec/Especificaciones.md` (ESP-01 … ESP-14).
> Cualquier desviación respecto a este documento o al de especificaciones requiere
> la actualización conjunta de ambos.

---

## 1. Identidad del Proyecto

| Campo | Valor |
|---|---|
| **Nombre** | OneWatch |
| **Objetivo** | Motor de vigilancia tecnológica de IA: saber qué componentes usa cada aplicación, detectar qué cambia fuera (noticias, versiones, deprecaciones) y alertar a los responsables cuando un cambio afecta a sus aplicaciones |
| **Plataforma base** | Microsoft Azure |
| **Servicios núcleo** | Azure PostgreSQL Flexible Server · Azure OpenAI (clasificación de noticias) · Azure Functions · Azure App Service · Azure Container Registry · Azure Storage Account · Microsoft Entra ID (identidad de los usuarios) |
| **Compute del backend (API REST)** | Azure App Service (contenedor Linux, imagen en Azure Container Registry) |
| **Procesador de tareas programadas** | Una única Azure Function App (Timer Triggers) para la revisión de fuentes externas y la validación de impacto sobre las aplicaciones |
| **Integraciones externas** | API de GitHub (repositorios, SBOM, contenido) · feeds RSS/Atom de las fuentes · Slack (webhook e interactividad) · SMTP |
| **Alcance** | MVP de 5 épicas: Inventario, Catálogo, Vigilancia, Correlación y Plataforma (ESP-01 … ESP-14). Foco en temas de IA, ecosistemas Python (PyPI) y JavaScript (npm) y repositorios alojados en GitHub |
| **Repositorio de GitHub Back** | https://github.com/Alejo677/vigia-back.git |
| **Repositorio de GitHub Function** | https://github.com/Alejo677/vigia-func.git |
| **Repositorio de GitHub Front** | https://github.com/Alejo677/vigia-front.git |
| **Fuente Especificaciones** | File |
| **ProyectoJira** | TODO |
| **Archivo Especificaciones** | ./docs/Spec/Especificaciones.md |

---

## 2. Principios Inmutables

### 2.1 El catálogo es el vocabulario único del sistema
Inventario y noticias solo se cruzan a través de los identificadores canónicos del catálogo (ESP-04). El LLM elige componentes de una **lista cerrada** (los identificadores del catálogo); cualquier componente devuelto que no exista en el catálogo se descarta y se registra. Está **prohibido** crear componentes, alias o usos implícitamente desde la clasificación o la correlación. Una alerta sobre un componente fuera del catálogo es un defecto bloqueante.

### 2.2 Trazabilidad obligatoria de cada hallazgo y cada alerta
- Todo hallazgo de IA guarda su evidencia (ruta, línea y fragmento).
- Toda clasificación guarda la plantilla de prompt usada (categoría, identificador, versión), el modelo (nombre del LLM o `regla-adaptador`) y la respuesta cruda.
- Toda alerta referencia la noticia, la aplicación, los repositorios implicados, el componente, la versión usada y la evidencia.

Una alerta o clasificación sin trazabilidad no es válida y debe rechazarse en QA.

### 2.3 Nunca se almacenan secretos
El escaneo de código (ESP-03) nunca persiste valores de secretos: de una variable de entorno solo se guarda su nombre. OneWatch no almacena ni gestiona contraseñas de usuario: la autenticación se delega en Microsoft Entra ID (ESP-14). Tokens, claves y secretos nunca aparecen en logs, en BD, en respuestas crudas ni en variables de cliente; en el navegador solo existen los tokens que gestiona MSAL en `sessionStorage`.

### 2.4 Nada se borra si tiene histórico
Aplicaciones, repositorios y componentes retirados se marcan **inactivos**; las instantáneas de SBOM se conservan; las valoraciones de alertas conservan su histórico; las plantillas de prompt conservan sus versiones anteriores. Solo se permite el borrado físico donde la especificación lo autoriza explícitamente (fuente sin noticias asociadas, plantilla que no es la última `generico` activa de su categoría).

### 2.5 Todos los procesos son idempotentes
Ejecutar dos veces un proceso (`sync-apps`, `sync-catalog`, `import-sbom`, `scan-ai`, `resolve-usages`, `ingest-news`, `classify-news`, `correlate`, `send-digest`) sin cambios en la entrada no genera modificaciones, duplicados de noticias ni alertas repetidas para el mismo par noticia–aplicación.

### 2.6 La configuración funcional vive fuera del código
- Aplicaciones y repositorios: `applications.yaml` (ESP-01).
- Catálogo: `catalog.yaml` (ESP-04).
- Reglas de detección de IA: `ai-detectors.yaml` (ESP-03).
- Fuentes de noticias: maestro web (ESP-06).
- Prompts del LLM: maestro de plantillas de prompt (ESP-13).

Está **prohibido** hardcodear prompts, reglas de detección, fuentes o entradas de catálogo en el código. Un cambio de prompt o de regla no requiere redeploy.

### 2.7 La lógica vive en la aplicación, no en la base de datos
Todas las validaciones de negocio se realizan en la aplicación (Python). La base de datos no contiene lógica (sin triggers, procedimientos ni funciones de negocio); solo restricciones de integridad (PK, FK, `UNIQUE`, `NOT NULL`).

### 2.8 Autorización vinculante en el backend
Toda API exige un token de acceso de Microsoft Entra ID válido para la API de OneWatch (firma, emisor del tenant corporativo, audiencia, expiración y *scope*). Toda restricción por rol (*App Roles* `admin` / `user`) se aplica en el backend; los guards y directivas de Angular son solo cosméticos: nunca sustituyen la validación del backend (ESP-14, Regla 5).

### 2.9 Recolección respetuosa de fuentes externas
Toda petición a fuentes externas (feeds y páginas) usa el User-Agent de bot identificable definido en ESP-06 y respeta `robots.txt`. Está **prohibido** sustituirlo por un User-Agent de navegador. Las llamadas a la API de GitHub respetan su rate limit (`x-ratelimit-remaining`, `x-ratelimit-reset`).

### 2.10 OneWatch no administra usuarios
La aplicación solo autentica (delegando en Microsoft Entra ID) y autoriza (según el *App Role* del token). Altas, cambios de rol y bajas se hacen exclusivamente en Entra ID. OneWatch no tiene pantallas, endpoints ni tablas de usuarios: la identidad y el rol salen del token en cada petición.

---

## 3. Restricciones Funcionales y Arquitectónicas

### 3.1 Stack tecnológico fijo

Los siguientes servicios constituyen el stack del proyecto y **no pueden sustituirse** sin aprobación del equipo técnico:

| Capacidad | Servicio / Tecnología |
|---|---|
| Frontend | Angular 21 (standalone components, signals) |
| Backend (API REST y endpoint de interactividad de Slack) | Python 3.12 · FastAPI · Clean Architecture |
| Compute del backend | Azure App Service (contenedor Linux) |
| Registro de imágenes del backend | Azure Container Registry |
| Tareas programadas (revisión de fuentes externas y validación de impacto) | **Una única** Azure Function App (Python 3.12, Timer Triggers) |
| Persistencia operacional | Azure PostgreSQL Flexible Server |
| Clasificación de noticias | Azure OpenAI (salida estructurada en JSON validada con Pydantic) |
| Almacenamiento del runtime de la Function | Azure Storage Account (`AzureWebJobsStorage`) |
| Autenticación y autorización de usuarios | Microsoft Entra ID (tenant corporativo): MSAL Angular en el frontend (código de autorización + PKCE), validación de tokens de acceso v2.0 en el backend y *App Roles* `admin` / `user` (ESP-14) |
| Notificaciones | Slack (webhook entrante + interactividad) y SMTP |
| Secretos y configuración en producción | App Settings de App Service / Function App (no se usa Key Vault) |

### 3.2 Una única Function para las tareas de fondo
Todas las tareas de revisión de fuentes externas (GitHub, feeds, LLM) y de validación de impacto sobre las aplicaciones (resolución de usos, correlación, notificación) se ejecutan en **una sola Function App** (`func/`). Está **prohibido** crear Function Apps, workers o contenedores adicionales para estas tareas sin decisión explícita del equipo técnico. Los comandos CLI de las especificaciones y los Timer Triggers invocan los **mismos casos de uso**: no hay dos implementaciones del mismo proceso.

### 3.3 Formatos y ecosistemas admitidos

| Ámbito | Admitido en el MVP |
|---|---|
| Repositorios | Solo GitHub (`owner/nombre`) |
| SBOM de entrada | SPDX JSON del dependency graph de GitHub (`GET /repos/{owner}/{repo}/dependency-graph/sbom`) |
| Ecosistemas procesados | PyPI y npm; el resto se guarda marcado como "no soportado" |
| Archivos escaneados por `scan-ai` | `.py`, `.js`, `.ts`, `.json`, `.yaml`, `.yml`, `.env.example`, `.toml` (excluidos `node_modules`, `venv`, `dist`, `build`) |
| Tipos de fuente de noticias | `rss_atom`, `github_releases` (`https://github.com/{owner}/{repo}/releases.atom`), `pypi_releases` (`https://pypi.org/rss/project/{paquete}/releases.xml`) |
| Exportación de inventario | CycloneDX 1.6 en JSON |

### 3.4 Parámetros de procesamiento fijos

| Parámetro | Valor | Especificación |
|---|---|---|
| Fragmento máximo de evidencia | 200 caracteres | ESP-03 |
| Tamaño máximo de repositorio escaneado | 500 MB | ESP-03 |
| Timeout / redirecciones al validar un feed | 10 s / 5 | ESP-06 |
| Frecuencia de consulta de una fuente | 1–720 h (por defecto 24) | ESP-06 |
| Longitud máxima de filtros de inclusión/exclusión | 500 caracteres | ESP-06 |
| Umbral de enriquecimiento (descarga de la página) | contenido < 500 caracteres | ESP-07 |
| Texto máximo guardado por noticia | 20.000 caracteres | ESP-07 |
| Ventana de la primera ingesta de una fuente | últimos 30 días | ESP-07 |
| Fallos consecutivos para destacar una fuente | 5 | ESP-07 |
| Reintentos ante JSON inválido del LLM | 1 | ESP-08 |
| Confianza mínima sin marca "revisar" | 0,5 | ESP-08 |
| Resumen de clasificación | máx. 300 caracteres, en español | ESP-08 |
| Subida de prioridad por fecha efectiva cercana | < 30 días (retirada o deprecación) | ESP-09 |
| Reintentos de envío de digest | 3 | ESP-10 |

### 3.5 Clasificación con LLM acotada
- El prompt se resuelve siempre en el maestro de plantillas (ESP-13) con categoría `vigilancia` e identificador igual al código de la fuente, con respaldo en la plantilla `generico` de la categoría.
- La respuesta del LLM se valida contra el esquema JSON de ESP-08 (tipos de evento, severidades y componentes admitidos) antes de guardarse.
- Las noticias con datos estructurados del adaptador (Versiones de PyPI) y sin palabras de alerta se clasifican **sin llamar al LLM** (modelo `regla-adaptador`).
- No se usa LLM para detectar componentes en el código (ESP-03) ni para resolver usos (ESP-05).

### 3.6 Correlación determinista
La generación de alertas (ESP-09) es determinista: cruza componentes afectados con usos vigentes (consulta `component_usage_current`), compara versiones con `packaging` (PyPI) y semver (npm) y calcula la prioridad con la matriz severidad × criticidad. Índice único sobre (noticia, aplicación). No interviene el LLM.

### 3.7 Registro de actividad obligatorio
Toda ejecución de un proceso programado o CLI (`sync-apps`, `import-sbom`, `scan-ai`, `ingest-news`, `classify-news`, `correlate`, …) queda registrada (proceso, resultado, duración) para la pantalla **Sistema › Actividad** (ESP-02), además del resumen que cada comando imprime en consola.

### 3.8 La interfaz web no sustituye a la configuración por archivo
Aplicaciones, repositorios y catálogo se mantienen por archivo YAML y CLI. Las pantallas Inventario, Catálogo, Alertas y Actividad son de **consulta**; solo Fuentes de noticias y Plantillas de prompt son maestros editables desde la web. El botón **Nuevo componente** del prototipo queda sin implementar en el MVP.

### 3.9 Prohibiciones explícitas de implementación
- Implementar autenticación propia (contraseñas, emisión de tokens), cualquier función de administración de usuarios, o aceptar un token sin validar firma, emisor, audiencia, expiración y *scope*.
- Hardcodear prompts, reglas de detección o entradas de catálogo.
- Persistir valores de secretos detectados en el código escaneado.
- Duplicar la lógica de un proceso entre CLI y Timer Trigger.
- Implementar validaciones de negocio en la base de datos.
- Delegar en el frontend la autorización de un endpoint.
- Usar un User-Agent de navegador para recolectar fuentes.

---

## 4. Flujos críticos por especificación

### 4.1 Inventario (ESP-01, ESP-02, ESP-03, ESP-12)
1. `sync-apps` valida `applications.yaml` (Pydantic); ante formato inválido o `key` duplicada no aplica ningún cambio. Comprueba acceso a cada repositorio; los inaccesibles quedan "sin acceso" y el resto continúa. Lo retirado del archivo se inactiva.
2. `import-sbom` (diario) procesa solo repositorios activos con acceso, crea una instantánea fechada por repositorio, guarda purl, versión, ecosistema y el SBOM crudo. Ante error en un repositorio conserva la instantánea anterior como vigente; ante rate limit se pausa y reanuda sin duplicar.
3. `scan-ai` (diario, tras `import-sbom`) aplica las reglas de `ai-detectors.yaml`; un patrón inválido impide iniciar el escaneo. Un mismo valor en un repositorio genera un hallazgo con varias evidencias.
4. `export-bom` exporta solo usos resueltos, valida contra el esquema CycloneDX 1.6 y no guarda un documento inválido.

### 4.2 Catálogo (ESP-04, ESP-05)
1. `sync-catalog` valida `catalog.yaml`; alias duplicados, modelos con proveedor inexistente o identificadores con formato inválido impiden aplicar cualquier cambio.
2. La normalización de alias (minúsculas, sin espacios ni guiones) es una única función compartida por ESP-04, ESP-05 y ESP-08.
3. `resolve-usages` (al final de `import-sbom` y `scan-ai`) resuelve por purl sin versión y, si no, por alias; lo no resuelto va a pendientes sin generar uso. Solo son vigentes los usos de la última instantánea correcta.

### 4.3 Vigilancia (ESP-06, ESP-07, ESP-08, ESP-13)
1. Maestro de fuentes: valida campos, patrón de URL por tipo y filtros regex; valida el feed con `feedparser` en el backend. No se elimina una fuente con noticias (409; se propone desactivarla).
2. `ingest-news` (horaria): fuentes activas vencidas → descarga condicional (`ETag` / `If-Modified-Since`) → normalización al modelo común → adaptador por tipo → filtros → deduplicación por URL canónica (y `guid`/`id` si existe) → enriquecimiento con `trafilatura` si procede → noticia en "pendiente de clasificar". El estado de consulta de la ingesta no modifica el estado de validación del maestro.
3. `classify-news` (tras cada ingesta): resuelve la plantilla en ESP-13 → regla de adaptador sin LLM si aplica → si no, LLM con lista cerrada del catálogo → validación → guarda clasificación con plantilla, modelo y respuesta cruda. Error del LLM: la noticia sigue pendiente; JSON inválido dos veces: "error de clasificación".
4. Resolución de plantillas: plantilla activa con categoría + identificador exacto; si no existe, la `generico` activa de la categoría; si ninguna existe, error de configuración.

### 4.4 Correlación (ESP-09, ESP-10, ESP-11)
1. `correlate` (tras `classify-news` y `resolve-usages`): noticia clasificada relevante → componentes afectados → usos vigentes → agrupación por aplicación → una alerta por par noticia–aplicación, sin duplicados, con prioridad P1/P2/P3. Las noticias de severidad "informativa" no generan alerta.
2. `send-digest` (semanal, lunes 08:00 configurable; `--dry-run` sin envío): alertas "nueva" desde el último digest → Slack (todas las aplicaciones) y email por responsable → marca "notificada" solo si el envío tiene éxito. Las alertas P1 se publican de inmediato en Slack.
3. Valoración (Slack o `rate-alert`): útil, ruido (con motivo de lista cerrada) o resuelta; se conserva el histórico y prevalece la última. El endpoint de Slack verifica la firma de la petición.

### 4.5 Plataforma (ESP-14)
1. Inicio de sesión con Microsoft → MSAL redirige a Entra ID (código de autorización + PKCE) → Entra ID emite un token de acceso para la API de OneWatch con el claim `roles` → Angular llama a `GET /api/v1/auth/me` → el backend valida el token y devuelve el usuario y su rol, sin persistir nada.
2. Solo acceden las cuentas del tenant con un *App Role* de OneWatch asignado (aplicación empresarial con asignación obligatoria). Cuenta sin rol → pantalla "No tienes acceso a OneWatch"; token válido sin `roles` → 403.
3. Token ausente, expirado o inválido (firma, emisor, audiencia o *scope*) → 401; Angular intenta renovarlo en silencio y, si no puede, redirige al inicio de sesión.
4. Roles del MVP: `admin` y `user` (si llegan ambos, prevalece `admin`). En el MVP ambos ven las mismas pantallas y datos; el rol queda disponible para restricciones futuras, que se implementan en código (guard en Angular + dependencia de rol en el backend).

---

## 5. Fuera de Alcance (Non-Goals)

Las siguientes actividades están **explícitamente excluidas** del alcance actual y no deben ser propuestas ni implementadas:

- Repositorios fuera de GitHub y descubrimiento automático de repositorios de una organización.
- Alta, edición o baja de aplicaciones, repositorios o componentes del catálogo desde la interfaz gráfica.
- Lanzamiento manual de `import-sbom` o `scan-ai` desde la interfaz gráfica.
- Análisis de vulnerabilidades, VEX, formato SPDX de salida, publicación automática en Dependency-Track y firma del documento CycloneDX.
- Análisis semántico del código, detección de prompts, modelos locales en binarios y uso de LLM para detectar componentes en el código.
- Versionado del catálogo, sugerencia automática de componentes o alias, resolución de usos asistida por LLM.
- Scraping de páginas HTML sin feed, fuentes con autenticación, redes sociales, newsletters por email e importación/exportación masiva de fuentes.
- Traducción de noticias y detección de noticias duplicadas entre fuentes distintas.
- Ajuste fino (fine-tuning) de modelos, clasificación manual desde la interfaz, comparación A/B de plantillas de prompt y generación automática de plantillas.
- Creación automática de tickets en Jira desde alertas y sugerencias de remediación.
- Preferencias de suscripción por usuario, Microsoft Teams y dashboard web de notificaciones.
- Ajuste automático de reglas o prompts a partir de las valoraciones.
- Pantalla de asignación de permisos, roles adicionales o permisos por aplicación/componente/fuente.
- Cualquier función de administración de usuarios en OneWatch (alta, edición, listado, cambio de rol o desactivación): se hace en Entra ID. Tampoco se guarda un registro de usuarios o accesos.
- Contraseñas propias, registro autoservicio y recuperación de contraseña.
- Proveedores de identidad distintos del tenant corporativo de Microsoft Entra ID (cuentas personales, Google, Entra External ID), acceso multi-tenant y revocación inmediata de sesiones (Continuous Access Evaluation).
- Creación de los registros de aplicación y de la aplicación empresarial en Entra ID: la hace el proyecto de infraestructura, igual que el resto de recursos.
- Function Apps, workers o servicios de cómputo adicionales para tareas de fondo (ver 3.2).
- Despliegue en plataformas distintas de Microsoft Azure.
- Aprovisionamiento de infraestructura Azure mediante IaC (Bicep/Terraform): la creación y configuración de los recursos es responsabilidad de otro proyecto.

---

## 6. Glosario del Proyecto

| Término | Definición |
|---|---|
| **Aplicación** | Unidad de negocio declarada en `applications.yaml`, identificada por `key`, con responsable y criticidad (alta, media, baja). Agrupa uno o varios repositorios. |
| **Repositorio** | Repositorio de GitHub (`owner/nombre`, rama opcional) asociado a una o varias aplicaciones. |
| **SBOM** | Software Bill of Materials. Lista de dependencias de un repositorio; en OneWatch se obtiene del dependency graph de GitHub en formato SPDX. |
| **Instantánea** | Registro fechado del inventario de un repositorio en una importación. Las anteriores se conservan. |
| **purl** | Package URL. Identificador estándar de un paquete (`pkg:pypi/langchain@0.1.20`). |
| **Hallazgo de IA** | Modelo, proveedor, endpoint o variable de entorno de IA detectado en el código por `scan-ai`, con sus evidencias. |
| **Evidencia** | Ruta, línea y fragmento (≤ 200 caracteres) que justifican un hallazgo. |
| **Catálogo** | Vocabulario común de componentes (librería, modelo, proveedor) con identificador canónico y alias. |
| **Identificador canónico** | Clave única de un componente: `pkg:<ecosistema>/<nombre>`, `model:<proveedor>/<modelo>` o `provider:<nombre>`. |
| **Alias** | Texto alternativo que resuelve a un componente; se compara normalizado (sin mayúsculas, espacios ni guiones). |
| **Uso** | Vínculo repositorio–componente–versión–origen (SBOM o escaneo) resultante de resolver contra el catálogo. |
| **Pendiente** | Dependencia o hallazgo que no se ha podido resolver contra el catálogo. |
| **Fuente** | Feed vigilado (RSS/Atom, Releases de GitHub o Versiones de PyPI) mantenido en el maestro de fuentes. |
| **Adaptador** | Lógica por tipo de fuente que extrae datos estructurados (versión, componente sugerido, prerelease) sin interpretar el texto. |
| **Noticia** | Entrada ingerida de una fuente, deduplicada por URL canónica, con su texto y estado de clasificación. |
| **Clasificación** | Resultado estructurado de una noticia: componentes afectados, tipo de evento, severidad, fecha efectiva, versión afectada, resumen y confianza. |
| **Plantilla de prompt** | Texto de prompt versionado, identificado por categoría + identificador, con plantilla `generico` de respaldo por categoría (ESP-13). |
| **Palabras de alerta** | Términos que fuerzan el envío de una noticia al LLM aunque tenga datos estructurados del adaptador. |
| **Alerta** | Resultado de cruzar una noticia clasificada con los usos vigentes de una aplicación; una por par noticia–aplicación, con prioridad P1/P2/P3. |
| **Digest** | Resumen semanal de alertas nuevas enviado por Slack y email. |
| **Valoración** | Opinión del responsable sobre una alerta: útil, ruido (con motivo) o resuelta. |
| **Timer Trigger** | Disparador programado (CRON) de Azure Functions con el que la Function App ejecuta los procesos periódicos. |
| **App Service** | Servicio PaaS de Azure (Web App for Containers) que aloja el backend FastAPI desde una imagen de Azure Container Registry. |
| **Microsoft Entra ID** | Servicio de identidad corporativo de Microsoft. Autentica a los usuarios de OneWatch y emite los tokens de acceso con su rol. |
| **App Role** | Rol definido en el registro de aplicación de la API de OneWatch en Entra ID (`admin`, `user`) y asignado a usuarios o grupos; llega al backend en el claim `roles` del token. |
| **MSAL** | Microsoft Authentication Library. Librería del frontend Angular que inicia sesión contra Entra ID y obtiene y renueva los tokens de acceso. |
| **Azure Container Registry (ACR)** | Registro privado de imágenes de contenedor del backend; App Service hace `pull` con Managed Identity. |

---

*Última actualización: 2026-09-27 — Autenticación con Microsoft Entra ID sin administración de usuarios (ESP-14); sin restricción de llamadas externas desde el frontend*
