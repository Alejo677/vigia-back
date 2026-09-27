---
name: specone
description: |
  Explica qué hacer a continuación: sin argumentos muestra el ciclo completo y por
  dónde empezar; con un KEY de Jira mira el estado real del issue y dice qué skill
  toca ahora y por qué.
  Úsala cuando no sepas qué comando ejecutar, cuando un issue esté atascado o al
  empezar a trabajar con SpecOne.
  Parámetros: [<KEY_JIRA>] — opcional
  Ejemplo: /specone IAFIT-42
argument-hint: "[KEY_JIRA]"
---

Actúa como guía del método SpecOne. Orienta sobre qué paso toca, sin ejecutarlo.

**No hagas el trabajo.** Explicas y recomiendas; el usuario decide e invoca.

---

## Sin argumento — el ciclo completo

Muestra el mapa y para:

```
CICLO SPECONE

  Especificación
    /crear-spec "<Épica>" "<descripción>"   idea → docs/spec/{ID}.md
    /crear-spec-jira <ruta>                 spec → Jira (Story + Subtasks) o archivo de specs
    /ajustar-spec <ruta> "<cambio>"         corregir la spec

  Desarrollo
    /analisis-spec <KEY>                    → docs/plan/{KEY}.md (requiere aprobación)
    /ajustar-plan <ruta> "<cambio>"         corregir el plan
    /implementacion-plan <KEY>              → código commiteado en local
    /figma-to-angular <URL> [KEY]           diseño de Figma → Angular
    /solucionar-fix <KEY>                   igual, para bugs
    /ajustar-implementacion <KEY> "<cambio>"  corregir código en la rama

  Cierre
    /pr-review <PR> [KEY]                   → docs/pr-review/{PR}.md

  Consulta
    /listar-issues [columna|KEY]            estado del tablero
    /specone [KEY]                          esta guía

BUGS:  /crear-fix "<descripción>" "<Épica>"  →  /solucionar-fix <KEY>

Las skills mueven la tarjeta hasta 02.DEVELOPS y registran el tiempo en Jira.
De ahí en adelante es tuyo: el push, el PR, el merge y mover el issue a
03.REVISION y 04.READYFORQA son tu aprobación del trabajo.
Con Fuente Especificaciones = File, "Jira" es el archivo de especificaciones:
mover la tarjeta es cambiar su Estado y el tiempo va en Tiempo invertido.
Cada skill termina dándote el comando exacto, listo para copiar.

Ejecuta /specone <KEY> para saber qué toca en un issue concreto.
```

---

## Con un KEY — qué toca ahora

Resuelve la fuente con `.claude/_shared/fuente-especificaciones.md` (Validación). Los
estados salen de `.claude/_shared/estados-jira.md`.

Lee el issue: en modo Jira con `mcp__jira__jira_get_issue`; en modo File, su
sección `### {KEY}` del archivo de especificaciones (el estado está en su
Seguimiento). Comprueba también:

- ¿Existe `docs/spec/{KEY}.md` o el fichero de spec de su Feature?
- ¿Existe `docs/plan/{KEY}.md`? ¿En qué `Estado:` está?
- ¿Hay rama `feature/{KEY}` o `fix/{KEY}`? (`git branch --list`)
- ¿Hay PR abierto? (`gh pr list --head feature/{KEY}`)

Con eso, recomienda **un solo paso siguiente**:

| Situación | Recomendación |
|---|---|
| Estado DEPRECATED | Reabrir si sigue vigente |
| 00.TODO, sin plan | `/analisis-spec {KEY}` |
| 01.DESIGN, plan `pendiente de aprobacion` | Revisarlo y cambiarlo a `aprobado` |
| 01.DESIGN, plan `aprobado`, sin rama | `/implementacion-plan {KEY}` (o `/solucionar-fix` si es Bug; si el plan trae `## Diseño (Figma)`, esa UI se implementa con `/figma-to-angular`) |
| 02.DEVELOPS, con rama y commits, sin PR | Revisar en local, hacer `push`, abrir el PR y mover el issue a 03.REVISION |
| 03.REVISION, sin revisión | `/pr-review <PR> {KEY}` |
| Revisión con BLOQUEANTES | `/ajustar-implementacion {KEY} "<corrección>"` |
| Revisión APROBADA, sin mergear | Mergear el PR y mover el issue a 04.READYFORQA |
| 04.READYFORQA | Nada: le toca a QA |
| DONE | Ciclo completo |

Formato de salida:

```
{KEY} — {título}
Estado: {estado actual}

{Una o dos frases sobre dónde está el trabajo: qué existe ya y qué falta.}

Siguiente paso:
  {comando exacto, listo para copiar}

{Por qué ese y no otro, en una línea.}
```

Si detectas algo incoherente —plan aprobado pero el issue en 00.TODO, PR abierto
sin rama local— dilo: suele significar que alguien trabajó fuera del flujo y es
mejor saberlo antes de seguir.

---

## Preguntas sobre una skill concreta

Si el usuario pregunta qué hace una skill en vez de pasar un KEY, resume su
propósito, cuándo se usa y con qué se confunde. No copies su contenido: el
fichero del comando está a un paso si lo necesita.

---

## Reportar consumo de tokens

Invoca `/token-spend "General" "specone"`.
