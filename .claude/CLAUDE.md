# Instrucciones de Implementación para Claude Code — OneWatch

> **Mandato principal:** Antes de generar o modificar cualquier código, leer y respetar
> [`.claude/CONSTITUCION.md`](CONSTITUCION.md). La constitución define los principios inmutables,
> el alcance y las restricciones funcionales del proyecto. Estas instrucciones son su complemento
> técnico: indican **cómo** implementar dentro de ese marco.

---

## 1. Contexto del Proyecto

- **Aplicación:** OneWatch, motor de vigilancia tecnológica de IA. Inventaría qué componentes usa cada aplicación (SBOM de GitHub + detección de IA en el código), vigila fuentes de noticias externas, clasifica las noticias con LLM contra un catálogo cerrado y genera alertas por aplicación cuando un cambio les afecta.
- **Especificaciones:** `docs/Spec/Especificaciones.md` (ESP-01 … ESP-14, 5 épicas: Inventario, Catálogo, Vigilancia, Correlación, Plataforma).
- **Prototipo UX:** https://dimly-woven-86209062.figma.site (una sola aplicación sin rutas por pantalla; se navega por el menú lateral).
- **Stack frontend:** Angular 21 (standalone components, signals).
- **Stack backend:** Python 3.12 · FastAPI · Clean Architecture. Expone la API REST de la aplicación web y el endpoint de interactividad de Slack.
- **Procesador de tareas programadas:** **una única** Azure Function App (`func/`, Python 3.12, Timer Triggers) para la revisión de fuentes externas (GitHub, feeds, LLM) y la validación de impacto sobre las aplicaciones (resolución de usos, correlación, notificación). Los comandos CLI de las especificaciones invocan los mismos casos de uso.
- **Servicios Azure núcleo:** PostgreSQL Flexible Server · Azure OpenAI · Azure Functions · App Service · Container Registry · Storage Account.
- **Integraciones externas:** API de GitHub · feeds RSS/Atom · Slack · SMTP.
- **Persistencia operacional:** Azure PostgreSQL Flexible Server (aplicaciones, repositorios, instantáneas, dependencias, hallazgos, catálogo, usos, pendientes, fuentes, noticias, clasificaciones, plantillas de prompt, alertas, digests, valoraciones, usuarios, registro de actividad).
- **Autenticación:** propia del sistema (JWT + `bcrypt`), roles `admin` y `user` (ESP-14). No se usa Entra ID para usuarios.

---

## 2. Estructura del proyecto

El proyecto se consolida en un workspace con varios repositorios GitHub independientes:

```
.
├── front/   ← Angular 21 · estructura detallada en `.claude/instructions/_angular.md` - repositorio GitHub TODO
├── func/    ← Python 3.12 · Azure Function App (Timer Triggers + CLI) · estructura detallada en `.claude/instructions/_azure.md` - repositorio GitHub TODO
└── back/    ← Python 3.12 · FastAPI · estructura detallada en `.claude/instructions/_python.md` - repositorio GitHub TODO
    ├── docs/
    │   ├── Spec/                        ← especificaciones funcionales (Especificaciones.md)
    │   ├── plan/                        ← planes de implementación por item
    │   ├── pr-review/                   ← revisiones de PR
    │   └── token-spend/                 ← consumo de tokens por issue
    ├── .claude/
    │   ├── CONSTITUCION.md              ← principios y restricciones inmutables
    │   ├── CLAUDE.md                    ← este archivo
    │   ├── commands/                    ← skills invocables como /nombre-del-skill
    │   ├── _shared/
    │   │   ├── estados-jira.md          ← estados del tablero y sus transiciones
    │   │   └── fuente-especificaciones.md ← fuente de requisitos (Jira o File) y formato del archivo
    │   └── instructions/
    │       ├── _angular.md
    │       ├── _azure.md
    │       ├── _python.md
    │       └── _testing.md
    └── .github/                         ← mismas instrucciones para GitHub Copilot
```

---

## 3. Reglas Transversales de Generación de Código

### 3.1 Respeto absoluto a la constitución

Antes de proponer cualquier cambio, validar que respeta los principios inmutables (sección 2 de la constitución) y las restricciones arquitectónicas (sección 3). Las siguientes violaciones **no deben ser propuestas nunca**:

- Aceptar componentes devueltos por el LLM que no existan en el catálogo, o crear componentes/alias implícitamente.
- Persistir valores de secretos detectados en el código escaneado (solo el nombre de la variable).
- Hardcodear prompts, reglas de detección, fuentes o entradas de catálogo en el código.
- Borrar físicamente aplicaciones, repositorios, instantáneas, usuarios o valoraciones (se inactivan/desactivan).
- Poner lógica de negocio en la base de datos (triggers, procedimientos, funciones).
- Crear Function Apps, workers o contenedores adicionales para tareas de fondo.
- Llamar a servicios externos (GitHub, Azure OpenAI, Slack, SMTP, feeds) desde el frontend.
- Persistir tokens, contraseñas, secretos o claves en logs, BD en texto plano o variables de cliente.

### 3.2 Separación frontend / backend / function

- El frontend solo hace llamadas HTTP al backend; nunca invoca servicios externos ni Azure.
- El backend atiende la aplicación web (maestros y pantallas de consulta), el login y la interactividad de Slack. Es el único componente expuesto por HTTP.
- La Function (`func/`) ejecuta los procesos programados y los comandos CLI. No expone API para el frontend.
- Backend y Function comparten la base de datos PostgreSQL. El DDL tiene un único dueño: `back/scripts/DB/`.
- Cuando el backend necesite disparar un proceso de la Function (botón **Sincronizar** de Inventario → `sync-apps`), no reimplementa el proceso: solicita su ejecución a la Function (mecanismo a definir en el análisis de ESP-01).

### 3.3 Un proceso, una implementación

Cada proceso (`sync-apps`, `sync-catalog`, `import-sbom`, `scan-ai`, `resolve-usages`, `ingest-news`, `classify-news`, `correlate`, `send-digest`, …) es **un caso de uso**. El Timer Trigger y el comando CLI son solo puntos de entrada que lo invocan. Está prohibido duplicar lógica entre ambos.

### 3.4 Trazabilidad

- Hallazgos de IA con evidencia (ruta, línea, fragmento ≤ 200 caracteres).
- Clasificaciones con plantilla (categoría, identificador, versión), modelo y respuesta cruda.
- Alertas con noticia, aplicación, repositorios, componente, versión usada y evidencia.
- Maestros (fuentes, plantillas) con auditoría: fecha y usuario de alta y de última modificación.

### 3.5 Idempotencia

Todo proceso es idempotente: sin cambios en la entrada no hay modificaciones. Se garantiza con claves de negocio únicas (`key` de aplicación, `owner/nombre` de repositorio, identificador canónico, alias normalizado, URL canónica / `guid` de noticia, par noticia–aplicación de alerta) y operaciones de upsert.

### 3.6 Validaciones de archivos de configuración todo-o-nada

`applications.yaml`, `catalog.yaml` y `ai-detectors.yaml` se validan completos con Pydantic antes de aplicar nada. Ante cualquier error (formato, clave duplicada, referencia inexistente, patrón inválido) no se aplica **ningún** cambio y se indica la línea/campo/regla con error.

### 3.7 Tolerancia a fallos por elemento

En los procesos por lotes, el fallo de un elemento (repositorio sin acceso, SBOM no disponible, feed caído, página no accesible, error del LLM) se registra y el proceso continúa con el resto. El resumen final informa de los elementos fallidos.

### 3.8 Registro de actividad y resumen en consola

Cada ejecución de un proceso (programada o CLI) registra proceso, resultado y duración para **Sistema › Actividad** y muestra en consola el resumen que indica su especificación.

### 3.9 Logging con contexto

Los logs relevantes incluyen en `extra` los identificadores de negocio que correspondan (`application_key`, `repository`, `snapshot_id`, `source_code`, `news_id`, `alert_id`, `process`). Nunca se registran secretos, contraseñas ni tokens.

### 3.10 Recolección respetuosa

Toda petición a feeds y páginas usa el User-Agent de bot configurado y respeta `robots.txt`. Las llamadas a GitHub controlan el rate limit con `x-ratelimit-remaining` / `x-ratelimit-reset`.

### 3.11 Permisos en cada endpoint

Cada endpoint del backend valida:

**(a) Token válido:** JWT firmado por el propio backend (HS256 o RS256) con claims `sub`, `email`, `role` y `exp`. Responder 401 si falta, es inválido o ha expirado.

**(b) Rol:** las rutas del maestro de usuarios (`/api/v1/users`) exigen además `role = admin`. Responder 403 si no.

**Excepciones:** `POST /api/v1/auth/login` (público) y el endpoint de interactividad de Slack, que no usa JWT sino la **verificación de la firma de Slack** (`X-Slack-Signature` + `X-Slack-Request-Timestamp` con el signing secret).

**Reglas de implementación:**
- Una dependencia común de FastAPI valida el token; otra adicional exige `admin`.
- La autorización nunca se delega al frontend; los guards de Angular son solo cosméticos.
- Un usuario desactivado no puede autenticarse aunque su contraseña sea correcta.

---

## 4. Guías de implementación por área

Las guías técnicas detalladas por dominio están en `.claude/instructions/`. **Antes de generar código en una de estas áreas, leer la guía correspondiente**. Las guías son normativas, no orientativas.

| Área | Archivo |
|---|---|
| Frontend Angular | [`.claude/instructions/_angular.md`](instructions/_angular.md) |
| Backend Python y arquitectura limpia | [`.claude/instructions/_python.md`](instructions/_python.md) |
| Servicios Azure (Functions, App Service, Container Registry, PostgreSQL, OpenAI, Storage) e integraciones externas | [`.claude/instructions/_azure.md`](instructions/_azure.md) |
| Testing (unitario e integración) | [`.claude/instructions/_testing.md`](instructions/_testing.md) |

> **Autenticación y autorización (ESP-14 — Épica Plataforma):** autenticación propia con email y contraseña (`bcrypt`) y JWT emitido por el backend con los claims `sub`, `email`, `role` y `exp`. Roles: `admin` y `user`. Ambos ven los mismos datos del dominio; solo `admin` accede al maestro de usuarios. El backend valida el token en cada request (ver sección 3.11). El frontend restringe rutas con `roleGuard` en `app.routes.ts`, pero la autorización vinculante siempre la ejerce el backend.

---

*Última actualización: 2026-09-27 — Versión inicial adaptada a las especificaciones del MVP*
*Mandato principal: [`.claude/CONSTITUCION.md`](CONSTITUCION.md)*
