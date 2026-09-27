# Proyecto Front — Angular

Angular 21 con **standalone components** — sin NgModules.

> Arquitectura limpia por features · Repositorio independiente: `front/`
>
> Prototipo de referencia: https://dimly-woven-86209062.figma.site (una sola aplicación sin rutas por pantalla; se navega por el menú lateral).

```
front/
  src/
    app/
      app.config.ts               # providers globales (provideRouter, provideHttpClient con interceptores, provideAnimationsAsync)
      app.routes.ts               # rutas lazy-load con loadComponent; aquí se aplica roleGuard a las rutas restringidas
      core/
        auth/                     # AuthService (token, usuario, role()), pantalla de login
        guards/                   # authGuard (sesión iniciada), roleGuard (rol requerido)
        interceptors/             # auth bearer + captura de 401 → login, manejo de errores
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
        users/                    # Maestros › Usuarios (solo admin) — ESP-14
        activity/                 # Sistema › Actividad (consulta) — ESP-02
        settings/                 # Sistema › Configuración
        <feature>/
          <feature>.routes.ts     # rutas propias de la feature (lazy)
          <feature>.component.ts  # smart component (orquesta estado y servicios)
          components/             # dumb components de la feature (solo inputs/outputs)
          services/               # servicio HTTP de la feature
          models/                 # interfaces y tipos propios de la feature
  environments/
    environment.ts                # apiUrl → http://localhost:8000/api/v1 (dev)
    environment.prod.ts           # apiUrl en producción
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
- Autenticación propia: login con email y contraseña contra `POST /api/v1/auth/login`; **no** se usa MSAL ni Entra ID.
- `AuthService` guarda el token y expone el usuario y `role()` como signals; guards y directivas lo consultan sin duplicar lógica.
- El interceptor añade `Authorization: Bearer <token>` a cada llamada y, ante un 401, limpia la sesión y redirige al login.
- `authGuard` protege toda la aplicación salvo el login. `roleGuard` se aplica manualmente en `app.routes.ts`; en el MVP solo a las rutas de `users/`. Cambiar qué ve un rol es una modificación de código, no de datos.
- El menú oculta **Maestros › Usuarios** a los usuarios con rol `user`; esto es cosmético, el backend responde 403 igualmente.
- La cabecera muestra el nombre del usuario y el botón de cerrar sesión; el rol no se muestra como algo accionable.
- Mensaje único "Usuario o contraseña incorrectos" ante cualquier fallo de login.

**Reglas funcionales de las pantallas:**
- El frontend solo llama al backend; nunca a GitHub, feeds, Azure OpenAI, Slack ni SMTP.
- Inventario, Catálogo, Alertas y Actividad son de **consulta**: no incluyen formularios de alta o edición. El botón **Nuevo componente** del Catálogo queda sin implementar en el MVP.
- Los formularios de los maestros muestran los errores de validación del backend junto a cada campo. Las validaciones del cliente son una ayuda, no sustituyen las del backend.
- Estado de las fuentes como etiqueta de color: gris (pendiente), verde (operativa), rojo (en error); fuentes desactivadas atenuadas.
- Las acciones destructivas (eliminar fuente o plantilla) piden confirmación; ante un 409 se ofrece la alternativa (desactivar).
