# Análisis de Implementación — ESP-14: Autenticación y autorización

Estado: Aprobado

Fuente: File (`./docs/Spec/Especificaciones.md`) · Épica 5 Plataforma · Depende de: — · Bloquea (transversal): ESP-06, ESP-10, ESP-11 y, en la práctica, cualquier endpoint del backend.

---

## 1. Descripción funcional

**Historia de usuario**

**Como** administrador del sistema,
**Quiero** que cada usuario inicie sesión en OneWatch con su cuenta corporativa de Microsoft Entra ID y que la aplicación conozca su rol, Administrador o Usuario,
**Para** controlar quién entra a la aplicación web reutilizando la identidad corporativa (MFA, acceso condicional, altas y bajas centralizadas), sin gestionar usuarios ni contraseñas en OneWatch y sin construir todavía un motor de permisos.

**Descripción de UX**

- Prototipo: https://dimly-woven-86209062.figma.site. El prototipo no muestra todavía el inicio de sesión; esta especificación define su comportamiento.
- **Inicio de sesión:** OneWatch no tiene formulario de email y contraseña. Al abrir la aplicación sin sesión se muestra una pantalla de bienvenida con el botón **Iniciar sesión con Microsoft**, que redirige a la página de inicio de sesión de Microsoft Entra ID (con el MFA y las políticas de acceso condicional que tenga configuradas la organización). Tras autenticarse, Entra ID devuelve al usuario a OneWatch.
- **Sin acceso:** si la cuenta se autentica en Entra ID pero no tiene asignado ningún rol de OneWatch, se muestra la pantalla "No tienes acceso a OneWatch. Solicítalo a un administrador." con un botón para cerrar sesión.
- **Cabecera de la aplicación:** muestra el nombre del usuario autenticado y un botón para cerrar sesión, que cierra la sesión de OneWatch y la de Entra ID. No muestra el rol como algo accionable.
- OneWatch no tiene ninguna pantalla de usuarios, roles ni permisos: no hay alta, edición, listado ni desactivación de usuarios.

**Propósito de la funcionalidad**

Delegar la autenticación en Microsoft Entra ID y disponer en cada petición del usuario autenticado y su rol, para que el resto del sistema parta de una identidad corporativa y una futura autorización más fina pueda apoyarse en el rol, sin construir ahora un motor de permisos ni administrar usuarios.

**Flujo principal (inicio de sesión)**

El usuario abre OneWatch → Pulsa **Iniciar sesión con Microsoft** → Angular (MSAL) lo redirige a Entra ID (flujo de código de autorización con PKCE) → El usuario se autentica en Entra ID → Entra ID devuelve a Angular un token de acceso para la API de OneWatch con los roles asignados → Angular llama a `GET /api/v1/auth/me` con ese token → El backend valida el token y devuelve el usuario y su rol → Angular muestra la pantalla principal.

**Reglas de negocio**

- Regla 1: Dos roles en el MVP: Administrador (`admin`) y Usuario (`user`), definidos como *App Roles* en el registro de aplicación de la API de OneWatch en Entra ID. Todo usuario con acceso tiene al menos uno; si tiene los dos (por ejemplo, por pertenecer a dos grupos), prevalece Administrador.
- Regla 2: Solo pueden iniciar sesión las cuentas del tenant corporativo que tengan asignado un rol de OneWatch (la aplicación empresarial exige asignación). Una cuenta deshabilitada en Entra ID, o sin rol asignado, no puede acceder.
- Regla 3: En el MVP, Administrador y Usuario ven las mismas pantallas y los mismos datos. El rol queda disponible en backend y frontend como base para restricciones futuras.
- Regla 4: Qué puede ver o hacer cada rol no se gestiona desde ninguna pantalla de permisos. Se define en el código: guards de ruta y directivas de rol en Angular y dependencias de rol en el backend. Cambiarlo implica modificar y desplegar de nuevo, no una configuración en caliente.
- Regla 5: El backend no delega en el frontend la protección de sus endpoints: toda API exige un token de acceso de Entra ID válido para la API de OneWatch, y cualquier restricción por rol que se añada en el futuro se aplica también en el backend, aunque el frontend ya oculte la pantalla.
- Regla 6: OneWatch no almacena usuarios, contraseñas ni tokens. Los tokens de acceso nunca se guardan en la base de datos ni se escriben en logs.
- Regla 7: El token expira según la política de Entra ID; MSAL lo renueva de forma silenciosa mientras la sesión de Entra ID siga activa. Una llamada con un token expirado o inválido responde 401 y hay que volver a iniciar sesión.
- Regla 8: Altas, cambios de rol y bajas de usuarios se hacen exclusivamente en Entra ID (aplicación empresarial de OneWatch → **Usuarios y grupos**). OneWatch no ofrece ninguna función de administración de usuarios.
- Regla 9: El usuario se identifica por su identificador de objeto de Entra ID (`oid`). La auditoría del resto de especificaciones (usuario de alta y de última modificación) guarda el email del token.

**Flujos alternativos o de excepción**

- Caso 1: Credenciales inválidas, MFA fallido o bloqueo por acceso condicional. Lo gestiona Entra ID en su propia página; el usuario no llega a OneWatch.
- Caso 2: Cuenta deshabilitada en Entra ID o sin rol de OneWatch asignado. Entra ID no emite el token para OneWatch y Angular muestra la pantalla "No tienes acceso a OneWatch". Si, por configuración, llegara un token sin el claim `roles`, la API responde 403 y Angular muestra la misma pantalla.
- Caso 3: Token expirado o inválido en una llamada a la API. La API responde 401; Angular intenta renovar el token de forma silenciosa y, si no puede, redirige a la pantalla de inicio de sesión.
- Caso 4: Se retira el rol a un usuario en Entra ID con una sesión abierta. El cambio se aplica cuando su token caduca y se renueva (como máximo, el tiempo de vida del token configurado en Entra ID).

**Punto de entrada:** pantalla de bienvenida con el botón **Iniciar sesión con Microsoft**. Toda la aplicación exige sesión iniciada, salvo esa pantalla.

**Sistemas / Servicios afectados:** Microsoft Entra ID: dos registros de aplicación (SPA de Angular y API del backend) y la aplicación empresarial de la API con asignación obligatoria. Su creación es responsabilidad del proyecto de infraestructura (fuera de alcance, constitución §5); la asignación de usuarios y grupos a los roles la hacen los administradores de Entra ID.

**Persistencia de datos:** ninguna. OneWatch no guarda usuarios: la identidad y el rol salen del token en cada petición.

**Fuera de alcance:** administración de usuarios en OneWatch; pantalla de permisos por pantalla, acción o dato; contraseñas propias, registro autoservicio y recuperación de contraseña; proveedores de identidad distintos del tenant corporativo y multi-tenant; revocación inmediata de sesiones (CAE); roles adicionales o permisos por aplicación, componente o fuente; registro de accesos o auditoría detallada por usuario.

**Descripción técnica (resumen de la especificación)**

- Registros en Entra ID (los crea infraestructura): `onewatch-api` (*Application ID URI* `api://<client-id>`, *scope* `access_as_user`, *App Roles* `admin`/`user`, `accessTokenAcceptedVersion = 2`), `onewatch-spa` (SPA, cliente público, permiso delegado sobre `access_as_user`) y aplicación empresarial de `onewatch-api` con asignación obligatoria.
- Backend: valida tokens v2.0 (RS256 contra el JWKS del tenant en caché, refresco ante `kid` desconocido; emisor `https://login.microsoftonline.com/<tenant-id>/v2.0`; audiencia = client id de `onewatch-api`; `exp`/`nbf`; `access_as_user` en `scp`). Claims: `oid`, `preferred_username` o `email`, `name`, `roles`. Sin `roles` reconocidos → 403; resto de fallos → 401. `require_role(UserRole.ADMIN)` disponible, sin uso en el MVP.
- Angular: `@azure/msal-angular` + `@azure/msal-browser`, código de autorización + PKCE, `sessionStorage`; `MsalInterceptor` sobre `apiUrl`; guard para toda la app salvo bienvenida; `roleGuard` y directiva de rol disponibles pero sin aplicar; rol desde `GET /api/v1/auth/me` expuesto en `AuthService.role()`.
- API: `GET /api/v1/auth/me` (la especificación la lista como `/api/auth/me`; se versiona según la guía de Python). Sin endpoints de login, logout ni usuarios.
- Configuración: `ENTRA_TENANT_ID`, `ENTRA_API_CLIENT_ID`, `ENTRA_API_SCOPE` (back); `entra.tenantId`, `entra.spaClientId`, `entra.apiScope`, `entra.redirectUri` (front, `environment.ts`).

## 2. Criterios de aceptación

1. **Inicio de sesión correcto** — Dado un usuario del tenant con el rol "Usuario" asignado en la aplicación empresarial de OneWatch, cuando inicia sesión con Microsoft, entonces accede a la aplicación, ve las mismas pantallas de datos que un Administrador y la cabecera muestra su nombre.
2. **Usuario sin rol asignado** — Dado un usuario del tenant sin ningún rol de OneWatch asignado, cuando intenta iniciar sesión con Microsoft, entonces no obtiene un token para la API de OneWatch y el sistema muestra "No tienes acceso a OneWatch".
3. **Token sin rol** — Dado un token de acceso válido para la API de OneWatch sin el claim "roles", cuando se llama a cualquier API protegida, entonces responde 403.
4. **Token de otra audiencia o de otro tenant** — Dado un token firmado por Entra ID pero emitido para otra aplicación o por otro tenant, cuando se llama a cualquier API protegida, entonces responde 401.
5. **Petición sin token** — Dado un cliente sin sesión iniciada, cuando llama a cualquier API protegida sin cabecera Authorization, entonces responde 401.
6. **Token expirado** — Dado un usuario con sesión iniciada cuyo token ha expirado y no se puede renovar, cuando llama a cualquier API protegida, entonces recibe 401 y Angular lo redirige a la pantalla de inicio de sesión.
7. **Rol recibido desde Entra ID** — Dado un usuario con los roles "Usuario" y "Administrador" asignados en Entra ID, cuando inicia sesión y la aplicación consulta su perfil, entonces el rol devuelto es "Administrador".
8. **Cambiar qué ve un rol es un cambio de código** — Dado que se quiere que el rol "Usuario" deje de ver el listado de alertas, cuando se implementa ese cambio, entonces se hace añadiendo el guard de ruta en Angular y la dependencia de rol en el endpoint del backend, y no existe ninguna pantalla del sistema para configurarlo.
9. **Cierre de sesión** — Dado un usuario con sesión iniciada, cuando pulsa "Cerrar sesión", entonces se cierra su sesión en OneWatch y en Entra ID y vuelve a la pantalla de bienvenida.

## 3. Análisis de impacto

### 3.1 Riesgos de regresión

Ninguno sobre código existente: `back/`, `front/` y `func/` solo contienen carpetas vacías y README; no hay ninguna especificación implementada.

Riesgos hacia especificaciones **futuras** que se apoyarán en esta:

| Issue | Fichero | Motivo |
|---|---|---|
| ESP-11 | `back/src/main.py` · `back/src/api/v1/routers/slack.py` (futuro) | La protección con token se aplica por defecto a todo `/api/v1` (ver §7, D1). El router de Slack debe registrarse **fuera** de ese grupo protegido y usar su verificación de firma; si se incluye dentro, Slack recibirá 401. |
| ESP-06, ESP-13 | `back/src/core/dependencies/auth.py` | La auditoría (`created_by`/`updated_by`, `VARCHAR(100)`) tomará `AuthenticatedUser.email`. Si se cambia la forma de obtener el email, cambia lo que se audita. |
| Todas las pantallas (ESP-01…ESP-13) | `front/src/app/app.routes.ts` · `front/src/app/core/layout/` | Las features se cuelgan como rutas hijas del shell protegido por `authGuard`; una ruta añadida fuera del shell quedaría sin sesión exigida (solo cosmético, el backend sigue protegiendo). |

### 3.2 TODOs a resolver

Ninguno. No existe ningún `# TODO: ... ESP-14` en `back/`, `front/` ni `func/` (repositorios sin código).

### 3.3 Cambios transversales

- **Base de datos:** ninguno. ESP-14 no persiste nada (Regla 6, constitución §2.10). No se crea tabla de usuarios.
- **Variables de entorno (back, `.env.example` nuevo):**
  - `ENTRA_TENANT_ID` — tenant corporativo (emisor esperado y URL del JWKS).
  - `ENTRA_API_CLIENT_ID` — client id de `onewatch-api` (audiencia esperada).
  - `ENTRA_API_SCOPE` — *scope* requerido en `scp` (por defecto `access_as_user`).
  - `CORS_ALLOWED_ORIGINS` — origen(es) del frontend (la SPA llama a la API con cabecera `Authorization`).
- **Variables de configuración (front, `environment.ts` / `environment.prod.ts` nuevos):** `apiUrl`, `entra.tenantId`, `entra.spaClientId`, `entra.apiScope` (`api://<client-id>/access_as_user`), `entra.redirectUri`. No son secretos (cliente público).
- **`func/`:** sin cambios. La Function no expone HTTP ni recibe tokens de usuario.
- **Dependencias back (`pyproject.toml` nuevo):**
  - Runtime: `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `python-dotenv`, `PyJWT[crypto]`.
  - Dev: `pytest`, `pytest-asyncio`, `httpx` (cliente de pruebas de FastAPI), `ruff`, `mypy`. Marcadores `unit`, `integration`, `slow`.
  - PostgreSQL (`psycopg`/pool) **no** entra en ESP-14: lo introduce la primera especificación que persiste (ESP-06/ESP-13).
- **Dependencias front (`package.json` nuevo):** workspace Angular 21 (standalone, strict, SCSS) + `@azure/msal-browser` y `@azure/msal-angular`.
- **Andamiaje:** al ser la primera especificación, crea el esqueleto mínimo de ambos repositorios (`pyproject.toml`, `src/main.py`, `Settings`, manejadores de excepciones, `/health`; workspace Angular, `app.config.ts`, `app.routes.ts`, shell). Solo lo que ESP-14 necesita, sin anticipar otras features.

## 4. Plan de implementación — Backend

Repositorio `back/`. Orden Inside-Out. Todas las rutas son relativas a `back/`.

| Capa | Archivo | Acción | Descripción |
|---|---|---|---|
| Proyecto | `pyproject.toml` | Crear | Build system, dependencias runtime/dev de §3.3, configuración de ruff, mypy (strict en `src/`) y pytest (`asyncio_mode`, marcadores `unit`/`integration`/`slow`, `pythonpath = ["."]`). |
| Proyecto | `.env.example` | Crear | `ENTRA_TENANT_ID`, `ENTRA_API_CLIENT_ID`, `ENTRA_API_SCOPE=access_as_user`, `CORS_ALLOWED_ORIGINS=http://localhost:4200`, con comentarios. Sin valores reales. |
| Enums | `src/domain/enums/user_role.py` | Crear | `UserRole(str, Enum)`: `ADMIN = "admin"`, `USER = "user"`. |
| Enums | `src/domain/enums/token_rejection_reason.py` | Crear | `TokenRejectionReason`: `MISSING`, `MALFORMED`, `INVALID_SIGNATURE`, `EXPIRED`, `NOT_YET_VALID`, `INVALID_ISSUER`, `INVALID_AUDIENCE`, `MISSING_SCOPE`, `MISSING_IDENTITY`, `KEYS_UNAVAILABLE`. Se usa en logs y para decidir 401 vs 503; nunca se devuelve el detalle al cliente. |
| Excepciones | `src/core/exceptions/unauthorized_exception.py` | Crear | `UnauthorizedException(message, reason: TokenRejectionReason)` → 401. |
| Excepciones | `src/core/exceptions/forbidden_exception.py` | Crear | `ForbiddenException(message)` → 403 (sin rol reconocido o rol insuficiente). |
| Excepciones | `src/core/exceptions/authenticate_user_exception.py` | Crear | Excepción propia del caso de uso para errores no esperados (p. ej. JWKS inaccesible) → 503. |
| Excepciones | `src/core/exceptions/handlers.py` | Crear | Registro de handlers globales: 401 con cabecera `WWW-Authenticate: Bearer` y cuerpo genérico `{"detail": "No autenticado"}`; 403 `{"detail": "No tienes acceso a OneWatch"}`; 503; 500 genérico sin trazas. |
| Value objects | `src/domain/value_objects/access_token_claims.py` | Crear | `AccessTokenClaims` (frozen, slots): `oid`, `email`, `name`, `roles: tuple[str, ...]`. Resultado de un token ya validado; no contiene el token. |
| Value objects | `src/domain/value_objects/access_token_policy.py` | Crear | `AccessTokenPolicy` (frozen): `issuer`, `audience`, `required_scope`, `jwks_uri`, `clock_skew_seconds`. Se construye desde `Settings` (`from_tenant(...)`) o, en tests, con emisor/audiencia de pruebas. |
| Entidades | `src/domain/entities/authenticated_user.py` | Crear | `AuthenticatedUser` (frozen): `oid`, `email`, `name`, `role: UserRole`. Método de clase `from_claims(claims)` que resuelve el rol: si `roles` contiene `admin` → `ADMIN`; si contiene `user` → `USER`; si no, lanza `ValueError` (sin rol reconocido). Método `has_role(*roles)`. |
| Interfaces | `src/domain/interfaces/i_access_token_validator.py` | Crear | `IAccessTokenValidator(ABC)` con `@abstractmethod async def validate(self, raw_token: str) -> AccessTokenClaims`. Contrato: lanza la excepción de su infraestructura con un `TokenRejectionReason`. (El primitivo `str` se acepta como excepción documentada: el token es un valor opaco sin entidad de dominio.) |
| DTOs | `src/application/dtos/authenticate_user_request.py` | Crear | `AuthenticateUserRequest(bearer_token: str \| None)`. `__repr__` enmascarado para que el token nunca aparezca en logs ni trazas. |
| DTOs | `src/application/dtos/current_user_response.py` | Crear | `CurrentUserResponse` (Pydantic): `oid`, `email`, `name`, `role: UserRole`; factoría `from_user(AuthenticatedUser)`. Es el cuerpo de `GET /api/v1/auth/me`. |
| Casos de uso | `src/application/use_cases/authenticate_user_use_case.py` | Crear | `AuthenticateUserUseCase(validator: IAccessTokenValidator)`. `execute(request) -> AuthenticatedUser`: sin token → `UnauthorizedException(MISSING)`; valida con el validador; mapea la excepción de infraestructura a `UnauthorizedException` (motivo de rechazo) o `AuthenticateUserException` (`KEYS_UNAVAILABLE`); construye `AuthenticatedUser.from_claims` y, si no hay rol reconocido, `ForbiddenException`. Log `🔐` con `extra={"reason": ..., "oid": ...}`; nunca token, cabecera ni claims completos. |
| Prompts IA | — | No aplica | ESP-14 no usa LLM. |
| Configuración | `src/core/configuration/settings.py` | Crear | `Settings(BaseSettings)`: `entra_tenant_id`, `entra_api_client_id`, `entra_api_scope` (por defecto `access_as_user`), `cors_allowed_origins: list[str]`. Método `access_token_policy()` que construye `AccessTokenPolicy` con emisor `https://login.microsoftonline.com/{tenant}/v2.0` y JWKS `https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys`. `get_settings()` con `lru_cache`. Falla al arrancar si faltan las variables de Entra ID. |
| Infraestructura | `src/infrastructure/auth/entra_id_token_validator_exception.py` | Crear | `EntraIdTokenValidatorException(reason: TokenRejectionReason)`: única excepción de esta infraestructura. |
| Infraestructura | `src/infrastructure/auth/entra_id_access_token_validator.py` | Crear | `EntraIdAccessTokenValidator(IAccessTokenValidator)`. Recibe `AccessTokenPolicy` y un `PyJWKClient` (inyectable para tests). `validate`: lee la cabecera sin verificar solo para el `kid`; obtiene la clave con `asyncio.to_thread` (PyJWKClient es síncrono); `jwt.decode` con `algorithms=["RS256"]` **fijo**, `audience`, `issuer`, `leeway`, `options={"require": ["exp", "nbf", "iss", "aud", "oid"]}`; comprueba `required_scope` en `scp` (separado por espacios); extrae `oid`, email (`preferred_username` → `email`; si falta → `MISSING_IDENTITY`), `name` y `roles`. Traduce cada excepción de PyJWT a su `TokenRejectionReason`. Caché del JWKS (`cache_jwk_set=True`, vida 1 h) y refresco ante `kid` desconocido limitado a uno cada `JWKS_MIN_REFRESH_SECONDS` (60 s) para que tokens con `kid` aleatorios no fuercen descargas. |
| Dependencias | `src/core/dependencies/auth.py` | Crear | `get_access_token_validator()` (singleton por proceso con `lru_cache`: comparte la caché del JWKS); `get_authenticate_user_use_case()`; `get_current_user(credentials = Depends(HTTPBearer(auto_error=False)), use_case = Depends(...)) -> AuthenticatedUser`; `require_role(*roles: UserRole)` → dependencia que devuelve el usuario o lanza `ForbiddenException`. En el MVP `require_role` no se usa en ningún endpoint. |
| Entrega | `src/api/v1/routers/auth.py` | Crear | `router = APIRouter(prefix="/auth", tags=["Auth"])`; `GET /me` → `CurrentUserResponse.from_user(user)`. No persiste nada. Sin endpoints de login, logout ni usuarios. |
| Entrega | `src/api/v1/routers/health.py` | Crear | `GET /health` → `{"status": "ok"}` sin autenticación (Health Check de App Service, guía Azure). Montado fuera de `/api/v1`. |
| Entrega | `src/api/v1/api_router.py` | Crear | `protected_router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_current_user)])` que incluye `auth.router`. **Todo router de negocio futuro se incluye aquí**, de modo que la protección es la opción por defecto (§7, D1). El de Slack (ESP-11) se registrará aparte. |
| Entrega | `src/main.py` | Crear | `load_dotenv()` como primera línea; crea `FastAPI(title="OneWatch API")`; middleware CORS (`CORS_ALLOWED_ORIGINS`, `allow_headers=["Authorization", "Content-Type"]`, sin credenciales de cookie); handlers de `handlers.py`; incluye `health.router` y `protected_router`. Configura logging. |
| Paquetes | `src/**/__init__.py`, `tests/**/__init__.py` | Crear | Marcadores de paquete para las carpetas utilizadas. |
| Tests | `tests/conftest.py` | Crear | Fixtures: par de claves RSA de pruebas y JWKS local; `LocalJwksClient` (subclase de `PyJWKClient` que sobrescribe `fetch_data` para devolver el JWKS local, sin red); `AccessTokenPolicy` de pruebas (emisor y audiencia de pruebas); factoría `make_token(**overrides)` firmada con RS256; `app` con `dependency_overrides[get_access_token_validator]` apuntando al validador real con JWKS local; `client` (`TestClient`). La validación de firma nunca se desactiva. |
| Tests | `tests/unit/test_authenticated_user.py` | Crear | Resolución de rol (ver §6). |
| Tests | `tests/unit/test_authenticate_user_use_case.py` | Crear | Caso de uso con `AsyncMock(spec=IAccessTokenValidator)`. |
| Tests | `tests/unit/test_entra_id_access_token_validator.py` | Crear | Validador real con JWKS local: motivos de rechazo y refresco limitado del JWKS. |
| Tests | `tests/integration/test_auth_router.py` | Crear | Endpoints con `TestClient` y tokens firmados con la clave de pruebas. |
| Documentación | `README.md` | Modificar | Sección "Variables de entorno" con las de §3.3 y cómo obtener un token de pruebas en local. |

## 5. Plan de implementación — Frontend

Repositorio `front/`. Orden Domain-First. Todas las rutas son relativas a `front/`.

| Capa | Archivo | Acción | Descripción |
|---|---|---|---|
| Proyecto | `package.json`, `angular.json`, `tsconfig*.json`, `src/main.ts`, `src/index.html`, `src/styles.scss` | Crear | Workspace Angular 21 generado con el CLI (standalone, `strict`, SCSS, sin SSR) conservando las carpetas existentes. `index.html` carga Inter. Añade `@azure/msal-browser` y `@azure/msal-angular`. |
| Configuración | `src/environments/environment.ts` · `src/environments/environment.prod.ts` | Crear | `apiUrl` (`http://localhost:8000/api/v1` en dev) y `entra: { tenantId, spaClientId, apiScope, redirectUri, postLogoutRedirectUri }`. `fileReplacements` en `angular.json` para prod. |
| Modelos | `src/app/core/auth/models/user-role.ts` | Crear | `export type UserRole = 'admin' \| 'user'` y constante `USER_ROLES`. |
| Modelos | `src/app/core/auth/models/current-user.ts` | Crear | `interface CurrentUser { oid; email; name; role: UserRole }` (espejo de `CurrentUserResponse`). |
| Modelos | `src/app/core/auth/models/auth-status.ts` | Crear | `type AuthStatus = 'anonymous' \| 'loading' \| 'authenticated' \| 'no-access'`. |
| Contratos | `src/app/core/auth/auth.repository.ts` | Crear | `abstract class AuthRepository { abstract getCurrentUser(): Observable<CurrentUser> }` usada como token de inyección. |
| Servicios | `src/app/core/auth/auth.service.ts` | Crear | `AuthService` (`providedIn: 'root'`, `inject()`): signals `currentUser`, `status`, computed `role()`, `isAuthenticated()`, `hasRole(...roles)`. `login()` → `MsalService.loginRedirect({ scopes: [apiScope] })`; `logout()` → `logoutRedirect({ postLogoutRedirectUri })` (cierra también Entra ID); `loadCurrentUser()` → llama al repositorio; 200 → `authenticated`; 403 → `no-access`. Marca `no-access` si el redirect de MSAL vuelve con `AADSTS50105` (usuario sin asignación en la aplicación empresarial). No copia tokens a signals ni a `localStorage`. |
| Infraestructura | `src/app/core/auth/http-auth.repository.ts` | Crear | Implementación HTTP: `GET {apiUrl}/auth/me`. |
| Infraestructura | `src/app/core/auth/msal.config.ts` | Crear | Factorías `msalInstanceFactory` (`PublicClientApplication`, authority `https://login.microsoftonline.com/<tenantId>`, `cacheLocation: BrowserCacheLocation.SessionStorage`, logger sin PII), `msalInterceptorConfigFactory` (`InteractionType.Redirect`, `protectedResourceMap` = `apiUrl` → `[apiScope]`) y `msalGuardConfigFactory`. |
| Infraestructura | `src/app/core/interceptors/auth-error.interceptor.ts` | Crear | Interceptor funcional: ante 401 reintenta **una vez** con `acquireTokenSilent({ forceRefresh: true })`; si falla, `loginRedirect`. Ante 403 de `/auth/me` → `AuthService` a `no-access` y navega a `/no-access`. |
| Guards | `src/app/core/guards/auth.guard.ts` | Crear | `authGuard`: espera a que MSAL termine la interacción (`inProgress$ === None`); sin cuenta → `/welcome`; con cuenta, asegura `loadCurrentUser()`; `no-access` → `/no-access`. |
| Guards | `src/app/core/guards/role.guard.ts` | Crear | `roleGuard(...roles: UserRole[])`: `CanActivateFn` que consulta `AuthService.hasRole`; si no, `/no-access`. **Sin uso en el MVP.** |
| Directivas | `src/app/shared/directives/has-role.directive.ts` | Crear | Directiva estructural `*owHasRole="['admin']"` basada en `AuthService.role()` (signal). **Sin uso en el MVP.** Cosmética: el backend es vinculante. |
| Arranque | `src/app/app.config.ts` | Crear | `provideRouter(routes)`, `provideHttpClient(withInterceptorsFromDi(), withInterceptors([authErrorInterceptor]))`, `provideAnimationsAsync()`, proveedores MSAL (`MSAL_INSTANCE`, `MSAL_GUARD_CONFIG`, `MSAL_INTERCEPTOR_CONFIG`, `MsalService`, `MsalBroadcastService`, `MsalGuard`, `HTTP_INTERCEPTORS` → `MsalInterceptor`), `{ provide: AuthRepository, useClass: HttpAuthRepository }` y `provideAppInitializer` que inicializa MSAL y procesa `handleRedirectPromise`. |
| Rutas | `src/app/app.routes.ts` | Crear | `welcome` y `no-access` públicas (lazy `loadComponent`); `''` → `ShellComponent` con `canActivate: [authGuard]` y `children: []` donde se colgarán las features; `**` → `''`. Comentario de ejemplo de cómo aplicar `roleGuard('admin')` (Regla 4). |
| Presentación | `src/app/app.component.ts` | Crear | Raíz con `<router-outlet />`; OnPush. |
| Presentación | `src/app/core/auth/pages/welcome/welcome.component.ts` (+ `.html`) | Crear | Pantalla de bienvenida con el logo/nombre OneWatch y el botón **Iniciar sesión con Microsoft** (`AuthService.login()`). Si ya hay sesión, redirige a `''`. Sin formulario de email y contraseña. |
| Presentación | `src/app/core/auth/pages/no-access/no-access.component.ts` (+ `.html`) | Crear | Mensaje "No tienes acceso a OneWatch. Solicítalo a un administrador." y botón **Cerrar sesión**. |
| Presentación | `src/app/core/layout/shell/shell.component.ts` (+ `.html`) | Crear | Shell con cabecera, zona lateral para el menú (vacía hasta que las features añadan sus entradas) y `<router-outlet />`. |
| Presentación | `src/app/core/layout/header/header.component.ts` (+ `.html`) | Crear | Componente dumb: input `userName`, output `logout`. Muestra el nombre y el botón **Cerrar sesión**; no muestra el rol como algo accionable. |
| Estilos | `src/styles.scss` | Crear | Reset, `font-family: Inter`, fondo y estilos mínimos de bienvenida, sin acceso y cabecera. |
| Tests | `src/app/core/auth/auth.service.spec.ts`, `src/app/core/guards/*.spec.ts`, `src/app/core/interceptors/auth-error.interceptor.spec.ts`, `src/app/core/layout/header/header.component.spec.ts` | Crear | Ver §6 (runner por defecto de Angular 21). |
| Documentación | `README.md` | Modificar | Valores de `entra.*` por entorno y *redirect URI* de `http://localhost:4200`. |

## 6. Plan de pruebas

**Backend — unitarias** (`pytest -m unit`)

| Test | Tipo | Escenario | Resultado esperado |
|---|---|---|---|
| `test_from_claims_with_admin_and_user_roles_returns_admin` | Unitario | Claims con `roles = ["user", "admin"]` | `role == UserRole.ADMIN` (criterio 7) |
| `test_from_claims_with_only_user_role_returns_user` | Unitario | `roles = ["user"]` | `role == UserRole.USER` |
| `test_from_claims_with_unrecognized_roles_raises_value_error` | Unitario | `roles = ["reader"]` | `ValueError` (sin rol reconocido) |
| `test_authenticate_user_without_token_raises_unauthorized_exception` | Unitario | `bearer_token=None` | `UnauthorizedException(MISSING)`; el validador no se llama |
| `test_authenticate_user_when_validator_rejects_token_raises_unauthorized_exception` | Unitario | Validador lanza `EntraIdTokenValidatorException(EXPIRED)` | `UnauthorizedException` con motivo `EXPIRED` |
| `test_authenticate_user_without_roles_raises_forbidden_exception` | Unitario | Claims válidos con `roles = ()` | `ForbiddenException` (criterio 3) |
| `test_authenticate_user_when_keys_unavailable_raises_authenticate_user_exception` | Unitario | Validador lanza `KEYS_UNAVAILABLE` | `AuthenticateUserException` (→ 503) |
| `test_authenticate_user_rejected_token_never_logs_token` | Unitario | Token rechazado, `caplog` activo | Ningún registro contiene el token ni `Bearer` (Regla 6) |
| `test_validate_with_valid_token_returns_claims` | Unitario | Token RS256 correcto firmado con la clave de pruebas | `AccessTokenClaims` con `oid`, email de `preferred_username`, `name`, `roles` |
| `test_validate_without_preferred_username_uses_email_claim` | Unitario | Token sin `preferred_username` y con `email` | Email tomado de `email` |
| `test_validate_without_email_claims_raises_missing_identity` | Unitario | Sin `preferred_username` ni `email` | `MISSING_IDENTITY` |
| `test_validate_with_hs256_token_raises_invalid_signature` | Unitario | Token HS256 firmado con la clave pública como secreto (confusión de algoritmo) | Rechazado (`INVALID_SIGNATURE`) |
| `test_validate_with_scope_list_without_required_scope_raises_missing_scope` | Unitario | `scp = "User.Read openid"` | `MISSING_SCOPE` |
| `test_validate_with_unknown_kid_refreshes_jwks_at_most_once_per_interval` | Unitario | Dos tokens con `kid` desconocidos seguidos | Una sola descarga del JWKS; ambos rechazados |
| `test_validate_when_jwks_unreachable_raises_keys_unavailable` | Unitario | `fetch_data` lanza error de red | `KEYS_UNAVAILABLE` |

**Backend — integración** (`pytest -m integration`, `TestClient` + validador real con JWKS local; ESP-14 no toca la BD)

| Test | Tipo | Escenario | Resultado esperado |
|---|---|---|---|
| `test_get_me_with_valid_user_token_returns_200_with_user_role` | Integración | Token válido con `roles = ["user"]` | 200 con `oid`, `email`, `name`, `role = "user"` (criterio 1) |
| `test_get_me_with_admin_and_user_roles_returns_admin_role` | Integración | `roles = ["user", "admin"]` | 200 con `role = "admin"` (criterio 7) |
| `test_get_me_without_authorization_header_returns_401` | Integración | Sin cabecera | 401 con `WWW-Authenticate: Bearer` (criterio 5) |
| `test_get_me_with_expired_token_returns_401` | Integración | `exp` en el pasado (más allá del margen de reloj) | 401 (criterio 6) |
| `test_get_me_with_not_yet_valid_token_returns_401` | Integración | `nbf` en el futuro | 401 |
| `test_get_me_with_other_audience_token_returns_401` | Integración | `aud` de otra aplicación, firma válida | 401 (criterio 4) |
| `test_get_me_with_other_tenant_issuer_returns_401` | Integración | `iss` de otro tenant, firma válida | 401 (criterio 4) |
| `test_get_me_with_token_signed_by_unknown_key_returns_401` | Integración | Firmado con otra clave RSA | 401 |
| `test_get_me_without_access_as_user_scope_returns_401` | Integración | `scp` sin `access_as_user` | 401 |
| `test_get_me_with_malformed_token_returns_401` | Integración | `Bearer abc.def` | 401 |
| `test_get_me_without_roles_claim_returns_403` | Integración | Token válido sin `roles` | 403 (criterio 3) |
| `test_get_me_with_unrecognized_role_returns_403` | Integración | `roles = ["reader"]` | 403 |
| `test_require_role_admin_with_user_role_returns_403` | Integración | Ruta de prueba registrada solo en el test con `require_role(UserRole.ADMIN)`, token `user` | 403 (criterio 8, parte backend) |
| `test_require_role_admin_with_admin_role_returns_200` | Integración | Misma ruta, token `admin` | 200 |
| `test_all_api_v1_routes_without_token_return_401` | Integración | Recorre `app.routes` bajo `/api/v1` sin token | Todas 401: la protección es por defecto (Regla 5) |
| `test_health_without_token_returns_200` | Integración | `GET /health` sin token | 200 |
| `test_cors_preflight_from_allowed_origin_allows_authorization_header` | Integración | `OPTIONS /api/v1/auth/me` desde el origen configurado | `Access-Control-Allow-Headers` incluye `Authorization` |

**Frontend** (runner de Angular 21; MSAL mockeado)

| Test | Tipo | Escenario | Resultado esperado |
|---|---|---|---|
| `test_loadCurrentUser_with_200_sets_authenticated_and_role` (`auth.service.spec.ts`) | Unitario | `/auth/me` devuelve `role: 'user'` | `status() === 'authenticated'`, `role() === 'user'` |
| `test_loadCurrentUser_with_403_sets_no_access` | Unitario | `/auth/me` responde 403 | `status() === 'no-access'` (criterio 2, caso 2) |
| `test_handleRedirect_with_AADSTS50105_sets_no_access` | Unitario | El redirect de MSAL vuelve con error `AADSTS50105` | `status() === 'no-access'` y navegación a `/no-access` (criterio 2) |
| `test_logout_calls_logoutRedirect_with_welcome_uri` | Unitario | `logout()` | `MsalService.logoutRedirect` con `postLogoutRedirectUri` de bienvenida (criterio 9) |
| `test_authGuard_without_account_redirects_to_welcome` | Unitario | Sin cuenta MSAL | `UrlTree` a `/welcome` |
| `test_authGuard_with_no_access_status_redirects_to_no_access` | Unitario | Cuenta sin rol | `UrlTree` a `/no-access` |
| `test_roleGuard_admin_with_user_role_redirects_to_no_access` | Unitario | `roleGuard('admin')`, rol `user` | `UrlTree` a `/no-access` (criterio 8, parte frontend) |
| `test_authErrorInterceptor_on_401_retries_silently_once_then_redirects_to_login` | Unitario | API responde 401 dos veces | Un `acquireTokenSilent({ forceRefresh: true })` y después `loginRedirect` (criterio 6) |
| `test_header_shows_user_name_and_emits_logout` | Unitario | `userName = 'Ana Pérez'` | Se muestra el nombre; el clic en **Cerrar sesión** emite `logout` (criterios 1 y 9) |

**Verificación manual** (requiere los registros de Entra ID del proyecto de infraestructura): criterio 1 (usuario `user` entra y ve su nombre), criterio 2 (usuario sin asignación ve "No tienes acceso a OneWatch") y criterio 9 (cierre de sesión en Entra ID). Se documentan en la PR.

## 7. Notas y decisiones de diseño

- **D1 — Protección por defecto en el router.** En vez de confiar en que cada router declare `Depends(get_current_user)`, `api_router.py` agrupa todo `/api/v1` bajo un `APIRouter` con esa dependencia, y un test recorre todas las rutas y exige 401 sin token. Olvidar la protección en un endpoint nuevo pasa a ser imposible por construcción (Regla 5, constitución §2.8). Los routers siguen pudiendo declarar `user: AuthenticatedUser = Depends(get_current_user)` para recibir el usuario (FastAPI cachea la dependencia por petición, así que no se valida dos veces). Solo `/health` y el futuro router de Slack (ESP-11) quedan fuera. "Auth" en el orden de middleware de la guía se cumple con esta dependencia; no hace falta un middleware de autenticación.
- **D2 — 401 frente a 403.** Todo lo que invalida el token (ausente, malformado, firma, `alg`, emisor, audiencia, `exp`/`nbf`, *scope*, sin `oid`/email) → 401. Token válido sin rol reconocido (`admin`/`user`) o `require_role` insatisfecho → 403. Así lo fija la especificación: la falta del *scope* es 401 aunque podría verse como un problema de autorización. El cuerpo de la respuesta es genérico; el motivo concreto solo va al log.
- **D3 — JWKS inaccesible → 503**, no 401: si no se pueden obtener las claves del tenant no es culpa del cliente, y un 401 haría que Angular lanzase un `loginRedirect` en bucle. Se registra como error.
- **D4 — Algoritmo fijo RS256** en `jwt.decode` para evitar confusión de algoritmos (`none`, HS256 con la clave pública). Hay un test explícito.
- **D5 — Caché y refresco del JWKS.** `PyJWKClient` con caché del conjunto de claves (1 h) y refresco ante `kid` desconocido limitado a una vez cada 60 s. Sin el límite, tokens con `kid` aleatorios forzarían una descarga del JWKS por petición. El validador es un singleton por proceso (`lru_cache`) para compartir la caché. Como `PyJWKClient` es síncrono, se llama con `asyncio.to_thread`. Alternativa descartada: cliente JWKS propio con `httpx` async (más código propio en una zona sensible, sin beneficio real con la caché).
- **D6 — Margen de reloj** de 60 s (`TOKEN_CLOCK_SKEW_SECONDS`) para `exp`/`nbf`. Los tokens "expirados" de los tests caducan con holgura (p. ej. hace 10 min) para no depender de ese margen.
- **D7 — Email obligatorio.** La auditoría de ESP-06 y ESP-13 guarda el email (Regla 9); un token sin `preferred_username` ni `email` se rechaza con 401 (`MISSING_IDENTITY`) en vez de auditar con otro dato. En tokens v2.0 de cuentas del tenant `preferred_username` viene siempre, así que no debería ocurrir. Aviso: las columnas de auditoría son `VARCHAR(100)`; un UPN más largo fallaría al guardar. Es un riesgo teórico, pero conviene tenerlo en cuenta en ESP-06/ESP-13.
- **D8 — Excepciones.** Se sigue la cascada de la guía: la infraestructura lanza `EntraIdTokenValidatorException` (única por fichero, con `TokenRejectionReason`), el caso de uso la traduce a `UnauthorizedException` / `ForbiddenException` / `AuthenticateUserException` y los handlers globales las convierten en 401/403/503. `get_current_user` es una dependencia y no un endpoint, así que la conversión a HTTP se hace en handlers globales en lugar de `try/except` en cada router.
- **D9 — `/auth/me` sin caso de uso propio.** Devolver el usuario ya autenticado es una conversión de `AuthenticatedUser` a DTO (`CurrentUserResponse.from_user`), sin lógica. Crear `GetCurrentUserUseCase` sería una abstracción vacía (guía: "no sobre-abstraer").
- **D10 — Carpeta `infrastructure/entra_id/`.** Existe vacía en `back/src/`, pero la guía y el `CLAUDE.md` fijan `infrastructure/auth/`. Se usa `auth/` y se elimina `entra_id/` para no dejar dos ubicaciones posibles.
- **D11 — Usuario sin asignación (criterio 2).** Con "asignación obligatoria", Entra ID no emite el token y el redirect vuelve a la SPA con el error `AADSTS50105`. Angular lo detecta en `handleRedirectPromise` y muestra "No tienes acceso a OneWatch". El 403 de `/auth/me` cubre el caso de un token que llegue sin `roles`. Los dos caminos llevan a la misma pantalla.
- **D12 — Reintento ante 401 en Angular.** `MsalInterceptor` ya obtiene el token en silencio antes de cada llamada; si aun así la API responde 401, el interceptor propio reintenta una sola vez con `forceRefresh: true` y, si vuelve a fallar, hace `loginRedirect`. El reintento único evita bucles.
- **D13 — Shell mínimo.** El shell se entrega con cabecera y la zona del menú lateral vacía; cada feature añadirá su entrada y su ruta hija. No se crea ninguna pantalla de datos provisional. Criterio 1 ("ve las mismas pantallas que un Administrador") queda garantizado porque no se aplica `roleGuard` ni `require_role` a nada.
- **D14 — Criterio 8** es de proceso, no de ejecución: se cubre con que existan `require_role` y `roleGuard`/`*owHasRole` (con sus tests), un comentario de ejemplo en `app.routes.ts` y la ausencia de cualquier pantalla o tabla de permisos.
- **Advertencia — compatibilidad de MSAL con Angular 21.** Comprobar al instalar que la versión vigente de `@azure/msal-angular` declara compatibilidad con Angular 21. Si no la declara, fijar la última versión compatible y documentarlo en la PR. No se sustituye MSAL por otra librería (stack fijo, constitución §3.1).
- **Advertencia — dependencia de infraestructura.** Las pruebas manuales end-to-end necesitan los registros `onewatch-api`/`onewatch-spa` y la aplicación empresarial, que crea el proyecto de infraestructura (fuera de alcance). Las pruebas automáticas no dependen de ellos: el backend se prueba con una clave RSA local y el front con MSAL mockeado. Nunca se piden tokens al tenant real en los tests.
- **Advertencia — la especificación usa la ruta `/api/auth/me`.** Se implementa como `/api/v1/auth/me` según la regla de versionado de la guía de Python y la constitución §4.5. Conviene alinear la tabla de la API de ESP-14 con `/ajustar-spec`.
- **Fuera de este plan:** tablas de usuarios, endpoints de login/logout, registro de accesos y cualquier pantalla de roles o permisos (constitución §2.10 y §5).
