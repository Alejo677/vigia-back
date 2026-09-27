# OneWatch — Backend (API REST)

API REST de **OneWatch**, el motor de vigilancia tecnológica de IA: expone a la aplicación web el inventario de componentes por aplicación, el catálogo, las noticias clasificadas, las alertas y los maestros editables (fuentes de noticias y plantillas de prompt). También aloja el endpoint de interactividad de Slack.

Las tareas programadas (ingesta, clasificación, correlación, digest…) **no** viven aquí: están en la Function App [`func/`](../func). El frontend está en [`front/`](../front).

## Stack

- Python 3.12 · FastAPI · Clean Architecture
- Azure PostgreSQL Flexible Server
- Autenticación con Microsoft Entra ID: el backend valida los tokens de acceso (firma, emisor, audiencia, *scope*) y toma el rol (`admin` / `user`) de los *App Roles*
- Despliegue: contenedor Linux en Azure App Service, imagen en Azure Container Registry (`onewatch-api`)

## Estructura

```
back/
├── pyproject.toml            # dependencias y configuración de ruff, mypy y pytest
├── src/
│   ├── main.py               # entrada FastAPI
│   ├── api/v1/routers/       # un router por recurso
│   ├── application/          # use_cases/, services/, dtos/
│   ├── core/                 # configuration/, dependencies/, exceptions/
│   ├── domain/               # entities/, enums/, interfaces/, value_objects/
│   └── infrastructure/       # postgresql/, auth/ (validación de tokens de Entra ID), feeds/, slack/
├── tests/
│   ├── unit/                 # use cases y dominio, sin I/O
│   └── integration/          # BD y servicios reales o emulados
├── scripts/
│   ├── DB/                   # DDL (DB.sql), migrations/ y seed/ — dueño único del esquema
│   ├── Azure/
│   └── Deployment/
└── docs/
    ├── Spec/                 # especificaciones funcionales (ESP-01 … ESP-14)
    ├── plan/                 # planes de implementación por item
    ├── pr-review/            # revisiones de PR
    └── token-spend/          # consumo de tokens por issue
```

## Puesta en marcha local

Requisitos: Python 3.12 y una instancia de PostgreSQL accesible.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env          # completar los valores
uvicorn src.main:app --reload --port 8000
```

La API queda en `http://localhost:8000/api/v1` y la documentación interactiva en `http://localhost:8000/docs`.

### Base de datos

El esquema se crea con `scripts/DB/DB.sql`, se evoluciona con `scripts/DB/migrations/` y se carga el contenido inicial (fuentes semilla y plantilla `vigilancia/generico`) con `scripts/DB/seed/`. La base de datos solo contiene restricciones de integridad: toda la lógica de negocio vive en la aplicación.

## Variables de entorno

| Variable | Propósito |
|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL |
| `ENTRA_TENANT_ID` | Tenant corporativo de Entra ID (emisor y claves de firma) |
| `ENTRA_API_CLIENT_ID` | Client id de `onewatch-api` (audiencia esperada) |
| `ENTRA_API_SCOPE` | *Scope* requerido (`access_as_user`) |
| `CORS_ALLOWED_ORIGINS` | Origen(es) del frontend, separados por comas |
| `SLACK_SIGNING_SECRET` | Verificación de firma de la interactividad de Slack |
| `BOT_USER_AGENT` | User-Agent de bot para validar feeds |

Referencia completa en `.env.example`. En producción se configuran como App Settings de App Service. **Nunca** se versiona `.env` ni se escriben secretos en logs.

La aplicación no arranca si faltan `ENTRA_TENANT_ID` o `ENTRA_API_CLIENT_ID`. Los valores (no son secretos) salen de los registros `onewatch-api` y `onewatch-spa` de Entra ID, que crea el proyecto de infraestructura.

### Autenticación (ESP-14)

- Todo `/api/v1` exige un token de acceso v2.0 de Entra ID para `onewatch-api` (firma RS256, emisor del tenant, audiencia, `exp`/`nbf` y *scope* `access_as_user`). Sin token o con token inválido → 401; token válido sin rol `admin`/`user` → 403. Solo `/health` es público.
- Los routers de negocio se incluyen en `protected_router` (`src/api/v1/api_router.py`), que aplica `get_current_user` por defecto. Para restringir un endpoint por rol: `Depends(require_role(UserRole.ADMIN))`.
- `GET /api/v1/auth/me` devuelve el usuario del token (`oid`, `email`, `name`, `role`). OneWatch no guarda usuarios ni tokens.
- Para llamar a la API en local hace falta un token real del tenant: lo más sencillo es iniciar sesión en el frontend y copiar el token de la pestaña de red del navegador. Los tests no usan el tenant: firman sus tokens con una clave RSA local.

## Pruebas y calidad

```bash
pytest -m unit
pytest -m integration         # requiere BD y servicios configurados (ESP-14 no usa BD)
ruff check .
mypy src
```

## Documentación del proyecto

- [`.claude/CONSTITUCION.md`](.claude/CONSTITUCION.md) — principios inmutables, alcance y restricciones. Toda contribución debe respetarla.
- [`.claude/CLAUDE.md`](.claude/CLAUDE.md) — instrucciones de implementación.
- [`docs/Spec/`](docs/Spec) — especificaciones funcionales del MVP.
