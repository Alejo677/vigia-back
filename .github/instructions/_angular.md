# Proyecto Front — Angular

Angular 21 con **standalone components** — sin NgModules.

> Arquitectura limpia por features · Repositorio independiente: `front/`
>
> Prototipo de referencia: https://dimly-woven-86209062.figma.site (una sola aplicación sin rutas por pantalla; se navega por el menú lateral).

```
front/
  src/
    app/
      app.config.ts               # providers globales (provideRouter, provideHttpClient con interceptores, provideAnimationsAsync, MSAL)
      app.routes.ts               # rutas lazy-load con loadComponent; aquí se aplica roleGuard a las rutas restringidas
      core/
        auth/                     # configuración MSAL, AuthService (usuario, role()), pantallas de bienvenida y "sin acceso"
        guards/                   # authGuard (sesión MSAL iniciada), roleGuard (rol requerido)
        interceptors/             # token de Entra ID como bearer hacia apiUrl + captura de 401, manejo de errores
        tokens/                   # injection tokens globales
        layout/                   # shell con menú lateral y cabecera (usuario + cerrar sesión)
      shared/
        components/               # componentes reutilizables (tabla paginada, etiqueta de estado, modales de confirmación, tarjetas de totales)
        directives/               # directivas reutilizables (ej. directiva de rol)
        pipes/                    # pipes reutilizables
      features/
        summary/                  # Espacio de trabajo › Resumen (totales)
        inventory/                # Espacio de trabajo › Inventario (consulta + botón Sincronizar) — ESP-01/02/03/05
        catalog/                  # Espacio de trabajo › Catálogo (consulta) — ESP-04/05
        alerts/                   # Espacio de trabajo › Alertas (consulta + Marcar revisadas) — ESP-09
        news-sources/             # Maestros › Fuentes de noticias (listado, formulario, detalle) — ESP-06
        prompt-templates/         # Maestros › Plantillas de prompt (listado, formulario, detalle) — ESP-13
        activity/                 # Sistema › Actividad (consulta) — ESP-02
        settings/                 # Sistema › Configuración
        <feature>/
          <feature>.routes.ts     # rutas propias de la feature (lazy)
          <feature>.component.ts  # smart component (orquesta estado y servicios)
          components/             # dumb components de la feature (solo inputs/outputs)
          services/               # servicio HTTP de la feature
          models/                 # interfaces y tipos propios de la feature
  environments/
    environment.ts                # apiUrl → http://localhost:8000/api/v1 (dev) + entra { tenantId, spaClientId, apiScope, redirectUri }
    environment.prod.ts           # apiUrl y entra en producción (no son secretos: la SPA es un cliente público)
  index.html                      # carga Inter desde Google Fonts
  styles.scss                     # estilos globales (reset, font-family, background)
  package.json
  angular.json
```

**Reglas de código:**
- **Signals** para estado local y comunicación entre componentes; evitar Subject/BehaviorSubject para estado simple.
- **`ChangeDetectionStrategy.OnPush`** en todos los componentes por defecto.
- **`inject()`** en lugar de constructor injection.
- **TypeScript strict mode** activado; prohibido el uso de `any`.
- **`@defer`** para renderizado condicional pesado en lugar de `*ngIf` con componentes grandes.
- Los smart components solo orquestan; la lógica de negocio va en servicios.
- No mezclar componentes de distintas features; lo compartido va en `shared/`.
- Preferir `styles.scss` globales que estilos por componente.

**Autenticación y roles (ESP-14):**
- Autenticación con **Microsoft Entra ID** mediante `@azure/msal-angular` + `@azure/msal-browser`: flujo de código de autorización con PKCE (redirect), `cacheLocation: 'sessionStorage'`. No hay formulario de email y contraseña: la pantalla de bienvenida solo tiene el botón **Iniciar sesión con Microsoft**.
- Los tokens los gestiona MSAL; la aplicación no los copia a `localStorage` ni a signals propios.
- Tras iniciar sesión, `AuthService` llama a `GET /api/v1/auth/me` y expone el usuario y `role()` como signals; guards y directivas lo consultan sin duplicar lógica. El rol lo decide el backend a partir del claim `roles`.
- El interceptor (`MsalInterceptor` con `protectedResourceMap` sobre `apiUrl` y el *scope* `api://<client-id>/access_as_user`) añade `Authorization: Bearer <token>`. Ante un 401 intenta `acquireTokenSilent`; si falla, redirige al inicio de sesión. Ante un 403 de `/auth/me`, muestra la pantalla "No tienes acceso a OneWatch".
- `authGuard` (o `MsalGuard`) protege toda la aplicación salvo la pantalla de bienvenida. `roleGuard` y la directiva de rol existen para restringir pantallas u opciones editando `app.routes.ts` o las plantillas; en el MVP no se aplican a ninguna ruta. Cambiar qué ve un rol es una modificación de código, no de datos.
- No hay pantallas de usuarios, roles ni permisos: la administración de usuarios se hace en Entra ID.
- La cabecera muestra el nombre del usuario y el botón de cerrar sesión (`logoutRedirect`, cierra también la sesión de Entra ID); el rol no se muestra como algo accionable.

**Reglas funcionales de las pantallas:**
- Inventario, Catálogo, Alertas y Actividad son de **consulta**: no incluyen formularios de alta o edición. El botón **Nuevo componente** del Catálogo queda sin implementar en el MVP.
- Los formularios de los maestros muestran los errores de validación del backend junto a cada campo. Las validaciones del cliente son una ayuda, no sustituyen las del backend.
- Estado de las fuentes como etiqueta de color: gris (pendiente), verde (operativa), rojo (en error); fuentes desactivadas atenuadas.
- Las acciones destructivas (eliminar fuente o plantilla) piden confirmación; ante un 409 se ofrece la alternativa (desactivar).
