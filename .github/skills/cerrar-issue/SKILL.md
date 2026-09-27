---
name: cerrar-issue
description: |
  Verifica que el PR de un issue esté listo para mergear: aprobado, sin conflictos
  y con los checks en verde.
  No mergea ni mueve el issue: deja el veredicto y los comandos exactos para que
  los ejecute el Tech Lead, que es quien aprueba con ese gesto.
  Se ejecuta cuando /pr-review ha aprobado.
  Parámetros: "<KEY_JIRA>" [<número de PR>]
  Ejemplo: /cerrar-issue IAFIT-42
argument-hint: "<KEY_JIRA>" [PR]
---

Asiste al Tech Lead en el cierre del ciclo: comprueba que el PR revisado está
en condiciones de mergearse y prepara el trabajo.

**No mergeas ni mueves el issue.** Verificas y entregas los comandos; quien
los ejecuta es el Tech Lead, y con ese gesto aprueba. El paso a DONE lo da QA
tras probarlo.

`$ARGUMENTS`: primer token = key del issue. Segundo opcional = número del PR;
si se omite, se localiza por la rama `feature/{KEY}` o `fix/{KEY}`.

---

## Paso 0 — Contexto

Lee `CONSTITUCION.md`. Resuelve la fuente con `_shared/fuente-especificaciones.md` (Validación) y
detente si no es válida. Comprueba el estado actual: en modo Jira con
`mcp__jira__jira_get_issue` (`ProyectoJira` es el `project_key`); en modo File,
en el Seguimiento de `### {KEY}` del archivo de especificaciones.
Los estados salen de `_shared/estados-jira.md`.

Comprueba el estado del issue. Si está en **DEPRECATED** o ya en
**DONE**, detente con el aviso correspondiente.

---

## Paso 1 — Localizar el PR

Con número explícito, úsalo. Sin él, búscalo por rama:

```bash
gh pr list --head feature/{KEY} --json number,title,state
gh pr list --head fix/{KEY} --json number,title,state
```

Si no aparece ninguno, detente:

> ⛔ No hay PR abierto para `{KEY}`. Ejecuta `/implementacion-plan {KEY}` o
> `/solucionar-fix {KEY}` primero.

Si hay varios, muéstralos y pide que se indique cuál.

---

## Paso 2 — Verificar que es mergeable

Esta es la parte que no se salta. Mergear algo sin revisar o con la CI en rojo
mete a `develop` código que nadie ha validado.

```bash
gh pr view <PR> --json reviewDecision,mergeable,statusCheckRollup,isDraft
```

**Detente si:**

| Condición | Motivo |
|---|---|
| `isDraft: true` | Es un borrador: aún no está listo |
| `reviewDecision` ≠ `APPROVED` | Falta la aprobación. Ejecuta `/pr-review <PR> {KEY}` |
| `mergeable: CONFLICTING` | Hay conflictos: resuélvelos en la rama |
| Algún check en `FAILURE` | La CI está en rojo |

Muestra qué falla y **no mergees**. Un cierre a medias es peor que no cerrar.

Si algún check sigue en `PENDING`, avisa y pregunta si esperar o continuar.

---

## Paso 3 — Entrega al Tech Lead

**Aquí la skill se detiene.** El merge y el paso a 04.READYFORQA los ejecuta
una persona: mergear escribe en `develop` y no se deshace, y mover la tarjeta
a QA es el gesto con el que se declara que el trabajo está listo.

Después muestra el veredicto y los comandos exactos, listos para copiar:

```text
✅ PR #<PR> verificado — listo para mergear

📌 Issue: <KEY> — <título>
🔀 PR #<PR>: <título>  ·  <rama> → develop
👤 Revisión: APROBADA por <revisor>
🧪 Checks: <N> en verde
📄 Revisión: docs/pr-review/<PR>.md
⚙️ Ficheros modificados: <N>

Cuando estés conforme:

  gh pr merge <PR> --squash --delete-branch

Y mueve el issue a 04.READYFORQA en Jira, dejando constancia (en modo File:
cambia su Estado en el archivo de especificaciones y omite el comentario):

  ## Ciclo de desarrollo completado
  PR #<PR> mergeado en develop
  - Ficheros modificados: <N>
  - Revisión: docs/pr-review/<PR>.md
  Listo para validación de QA.

El paso a DONE lo da QA tras validar.
```

Squash es la estrategia por defecto: el historial de `develop` queda con un
commit por issue. Si el proyecto usa otra, muéstrala en su lugar.

No ejecutes ninguno de esos comandos: los muestras para que los lance el
Tech Lead.

---

## Si algo impide mergear

Muestra qué falla y **detente**. No propongas el comando de merge: un PR sin
aprobar o con la CI en rojo no se mergea, y ofrecer el atajo invita a saltarse
la verificación.

## PASO 4 — Reportar consumo de tokens

Invoca `/token-spend <KEY_JIRA> "cerrar-issue"`.