# Revisión de PR #1 — Feature/esp 14

**Repositorio:** Alejo677/vigia-front
**Autor:** Alejo677
**Rama:** `feature/ESP-14` → `develop`
**Fecha de revisión:** 2026-09-27T19:40:32Z
**Archivos revisados:** 42 (excluido `package-lock.json`, generado mecánicamente por npm)

---

## Resumen ejecutivo

El PR implementa la autenticación con Microsoft Entra ID en el frontend (ESP-14): AuthService con signals, MSAL (código de autorización + PKCE), guards, interceptor de renovación de token y el shell básico. La estructura es limpia y sigue las convenciones de Angular 21 standalone/signals del proyecto, con buena cobertura de tests en la mayoría de piezas. Se encontró un **defecto de correctitud en `authGuard`**: cualquier fallo de `GET /auth/me` que no sea un 403 deja pasar al usuario a la zona protegida sin usuario cargado, en vez de negarle el acceso — contradice el propósito mismo del guard y no tiene ningún test que lo cubra. Recomendación: **solicitar cambios** hasta corregir ese punto; el resto son mejoras de bajo riesgo.

---

## Comentarios de revisión

🔴 **BLOQUEANTE — `authGuard` permite el acceso si `loadCurrentUser()` falla por un motivo distinto de 403**

- **Archivo:** `src/app/core/guards/auth.guard.ts` (líneas 15–21), en combinación con `src/app/core/auth/auth.service.ts` (líneas 91–105, método `loadCurrentUser`)
- **Problema:** `loadCurrentUser()` solo distingue dos desenlaces de error: 403 → `'no-access'`, cualquier otro error (red caída, backend caído, 500, CORS, timeout) → `'anonymous'`. El guard, sin embargo, solo comprueba `if (auth.status() === 'no-access') return redirect` y en cualquier otro caso hace `return true`. Como resultado, si `GET /auth/me` falla por cualquier motivo que no sea 403, el usuario **entra en el `ShellComponent`** con `currentUser() === null`, en vez de ser redirigido a `/welcome` o ver un error. `ShellComponent.userName` se limita a `?? ''`, así que la cabecera queda en blanco pero la navegación protegida igualmente se muestra.
- **Sugerencia:** Comprobar el caso positivo explícito en vez de excluir solo el negativo conocido:
  ```ts
  await auth.loadCurrentUser();
  if (auth.status() !== 'authenticated') {
    return auth.status() === 'no-access' ? router.parseUrl('/no-access') : router.parseUrl('/welcome');
  }
  return true;
  ```
  Añadir un test `test_authGuard_with_anonymous_status_after_failed_load_redirects_to_welcome` que fuerce este camino (los tests actuales de `auth.guard.spec.ts` solo cubren `hasActiveAccount=false`, `status='no-access'` y `status='authenticated'`; ninguno cubre el fallo no-403).
- **Por qué importa:** Es la puerta de acceso de toda la aplicación (ESP-14, Regla 5/8: "toda la aplicación exige sesión iniciada"). Aunque el backend sigue protegiendo cada endpoint de datos real, esta puerta del lado del cliente queda rota exactamente en el caso borde que un guard existe para cubrir, y el fallo es silencioso: no hay ningún indicio visual de qué pasó.

---

🟡 **IMPORTANTE — Fallos de `handleRedirect()` distintos de "sin asignación" se descartan en silencio**

- **Archivo:** `src/app/core/auth/auth.service.ts` (líneas 55–69)
- **Problema:** El `catch` de `handleRedirect()` solo actúa si el mensaje de error contiene `AADSTS50105`. Cualquier otro fallo al procesar el retorno de Entra ID (token de autorización inválido, `state` no coincide, error de red al canjear el código, etc.) se traga sin cambiar el estado, sin loguear nada y sin notificar al usuario. Como el `loggerCallback` de MSAL está deliberadamente vacío (para no exponer PII), no queda ningún rastro diagnosticable: el usuario simplemente se queda en la pantalla de bienvenida sin explicación.
- **Sugerencia:** Como mínimo, un `console.error` o log propio (sin PII) para cualquier error no reconocido, y considerar marcar un estado de error específico (`'anonymous'` con un mensaje, o reutilizar `'no-access'` con contexto) en vez de un `catch` vacío para el resto de casos.
- **Por qué importa:** Un fallo real de configuración de Entra ID (redirect URI mal registrada, client id incorrecto, etc.) sería indistinguible en producción de "el usuario simplemente no ha pulsado el botón", lo que hace muy difícil depurar incidencias de login reportadas por usuarios.

---

🟡 **IMPORTANTE — `HasRoleDirective` no reacciona a cambios de su `@Input()`**

- **Archivo:** `src/app/shared/directives/has-role.directive.ts` (líneas 26–34)
- **Problema:** `effect()` solo vuelve a ejecutarse cuando cambia una **signal** leída en su cuerpo. `this.roles` es un campo de clase normal (asignado desde el setter de `@Input()`), no una signal, así que leerlo dentro de `effect()` no crea ninguna dependencia reactiva sobre él. El efecto solo se re-ejecuta cuando cambia `auth.role()` (porque `hasRole()` sí lee esa signal internamente). Si el binding `*owHasRole="rolesDinamicos"` cambia el array de roles requeridos sin que el rol del usuario cambie a la vez, la visibilidad de la vista queda desactualizada hasta el próximo cambio de `auth.role()`.
- **Sugerencia:** Convertir la entrada en signal input (`readonly owHasRole = input<UserRole[]>([])`) y leerla dentro del `effect()`, o usar `computed()`/`toSignal` para que ambas fuentes (input y rol) sean reactivas de la misma forma.
- **Por qué importa:** La directiva está marcada como "sin uso en el MVP", pero es la pieza que futuras pantallas usarán para restricciones por rol (ESP-14, Regla 4); heredar este bug de reactividad silenciosamente cuando alguien la active por primera vez es exactamente el tipo de fallo difícil de reproducir en QA. No tiene test propio (`has-role.directive.spec.ts` no existe), así que nada lo habría detectado.

---

🔵 **SUGERENCIA — El interceptor propio y `MsalInterceptor` compiten por la cabecera `Authorization` en el reintento**

- **Archivo:** `src/app/core/interceptors/auth-error.interceptor.ts` (líneas 16–24)
- **Problema:** Tras un 401, `authErrorInterceptor` llama a `acquireTokenSilent` y clona la petición fijando manualmente `Authorization: Bearer <token>`. Pero esa petición reintentada vuelve a pasar por `MsalInterceptor` (registrado vía `withInterceptorsFromDi()` en `app.config.ts`), que también matchea `${apiUrl}/*` en su `protectedResourceMap` y **sobrescribe** la cabecera con su propia adquisición de token. El valor que fija `authErrorInterceptor` nunca llega realmente al backend tal cual se estableció.
- **Sugerencia:** Si el objetivo es solo forzar la renovación antes de reintentar, basta con `next(req.clone())` (dejando que `MsalInterceptor` ponga la cabecera con el token ya refrescado) en vez de fijarla dos veces; o documentar explícitamente por qué se hace así si es intencional.
- **Por qué importa:** No rompe el comportamiento (el resultado es equivalente), pero es trabajo duplicado y código que aparenta hacer algo que en la práctica no tiene efecto — confunde a quien lo lea después.

---

🔵 **SUGERENCIA — `MsalGuard`/`MSAL_GUARD_CONFIG` se registran pero no se usan en ninguna ruta**

- **Archivo:** `src/app/app.config.ts` (líneas 35, 38–40) y `src/app/core/auth/msal.config.ts` (líneas 39–45)
- **Problema:** `msalGuardConfigFactory`, el token `MSAL_GUARD_CONFIG` y el provider `MsalGuard` se registran en `app.config.ts`, pero el enrutado (`app.routes.ts`) protege sus rutas con el `authGuard` propio, no con `MsalGuard`. Ese bloque de providers queda inerte.
- **Sugerencia:** Eliminarlo si no hay plan de usar `MsalGuard` directamente, o dejar un comentario explicando por qué se mantiene disponible (p. ej., como opción de respaldo).
- **Por qué importa:** Código muerto en la configuración global invita a que alguien asuma que `MsalGuard` está protegiendo algo cuando no es así.

---

🔵 **SUGERENCIA — El id de analíticas del CLI de Angular quedó commiteado**

- **Archivo:** `angular.json` (línea 6): `"analytics": "25b5bf6e-5c18-410f-a3f3-9ab6a59f7302"`
- **Problema:** Ese campo lo escribe automáticamente el CLI de Angular la primera vez que se ejecuta un comando `ng` en una máquina, como respuesta al aviso de telemetría. Es un identificador local del entorno de quien ejecutó el comando, no una decisión de configuración del proyecto.
- **Sugerencia:** Quitar esa línea del archivo commiteado (`git diff` la aísla fácilmente) o añadir `"analytics": false` explícitamente si el equipo prefiere desactivar la telemetría del CLI para todo el proyecto.
- **Por qué importa:** Es ruido en el control de versiones que puede generar diffs espurios cada vez que alguien nuevo ejecuta `ng` por primera vez en una máquina distinta.

---

🔵 **SUGERENCIA — Aserción débil en el test de logout**

- **Archivo:** `src/app/core/auth/auth.service.spec.ts` (líneas 63–68), test `test_logout_calls_logoutRedirect_with_welcome_uri`
- **Problema:** `expect(msal.logoutRedirect).toHaveBeenCalledWith(expect.objectContaining({ postLogoutRedirectUri: expect.any(String) }))` solo comprueba que el valor es *alguna* cadena, no que sea el `postLogoutRedirectUri` configurado. El test pasaría igual aunque `logout()` mandara una URL completamente distinta a la de `environment.entra.postLogoutRedirectUri`.
- **Sugerencia:** `expect.objectContaining({ postLogoutRedirectUri: environment.entra.postLogoutRedirectUri })`, importando `environment` en el test.
- **Por qué importa:** El nombre del test promete verificar la URL concreta ("with_welcome_uri"), pero la aserción actual no lo hace; una regresión que cambiara la URL a un valor incorrecto no se detectaría.

---

✅ **DESTACADO — Manejo correcto del contexto de inyección en `provideAppInitializer`**

- **Archivo:** `src/app/app.config.ts` (líneas 30–37)
- Capturar `inject(MSAL_INSTANCE)` e `inject(AuthService)` de forma síncrona antes de cualquier `await`, y mover la lógica asíncrona a una función interna, evita exactamente el error `NG0203` que suele aparecer en este patrón. El comentario explica el motivo, no solo el qué.

---

✅ **DESTACADO — `navigateToLoginRequestUrl: false` con justificación explícita**

- **Archivo:** `src/app/core/auth/auth.service.ts` (líneas 56–59)
- Desactivar la navegación automática de MSAL hacia la página de origen del login (que habría competido con el `authGuard` de Angular) está bien documentado en el propio código, no solo en el historial de commits — cualquiera que lea el archivo entiende por qué está ahí sin tener que arqueológicamente rastrear el commit.

---

## Resumen de hallazgos

| Severidad | Cantidad |
|-----------|----------|
| 🔴 BLOQUEANTE | 1 |
| 🟡 IMPORTANTE | 2 |
| 🔵 SUGERENCIA | 4 |
| ✅ DESTACADO | 2 |

**Recomendación final:**
🔴 **SOLICITAR CAMBIOS** — El defecto de `authGuard` (deja pasar a la zona protegida si `GET /auth/me` falla por un motivo distinto de 403) debe corregirse antes de mergear: es la puerta de acceso de toda la aplicación y no tiene ningún test que lo cubra. Los dos hallazgos IMPORTANTE conviene resolverlos en el mismo PR ya que tocan código de esta misma feature; las SUGERENCIAs pueden abordarse aquí o en un ajuste posterior.
