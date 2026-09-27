---
name: implementacion-plan
description: |
  Escribe el código de una Feature o Fix siguiendo un plan ya aprobado en docs/plan/{KEY}.md.
  Requiere el plan con Estado: aprobado.
  Implementa backend, frontend y tests, y lo deja commiteado en local.
  No publica: el push y el Pull Request los hace el desarrollador.
  Al terminar mueve el issue a 02.DEVELOPS y registra el tiempo invertido.
  Es el paso que produce código; /analisis-spec lo precede generando el plan.
  Parámetros: "<KEY_JIRA>"
  Ejemplo: /implementacion-plan IAFIT-42
argument-hint: "<KEY_JIRA>"
---

Actúa como Desarrollador Full-Stack Senior. Implementa el item siguiendo el plan
aprobado. Ejecuta las fases en orden; no avances sin completar la anterior.

---

## Fase 0 — Validación

Lee `CONSTITUCION.md` y los ficheros de instructions activos del workspace
(`.claude/instructions/`). Con `mcp__jira__jira_get_issue` extrae estado,
subtareas, Original Estimate, título y épica. Los estados y sus transiciones
salen de `.claude/_shared/estados-jira.md`.

**Fuente** — resuélvela con `.claude/_shared/fuente-especificaciones.md` (Validación) y
detente si no es válida. En modo File, cada lectura de Jira de esta skill es la
sección `### <KEY_JIRA>` del archivo de especificaciones: estado y estimación salen
de su Seguimiento; las subtareas, de los Escenarios del Gherkin.

**Issue** (`mcp__jira__jira_get_issue` con `$ARGUMENTS`) — detente si está en
DEPRECATED. Si ya está en 03.REVISION o posterior, advierte que el ciclo
de implementación ya terminó.

La skill moverá el issue a **02.DEVELOPS** en la Fase 5, al terminar el código.

**Plan** (`docs/plan/<KEY_JIRA>.md`):

- No existe → detente: primero `/analisis-spec <KEY_JIRA>`
- `Estado: pendiente de aprobacion` → detente: pide que lo revisen y aprueben
- `Estado: aprobado` → es la **fuente de verdad exclusiva** de la implementación

Del plan usa: **§2** criterios de aceptación (tu checklist), **§3.3** cambios
transversales, **§4** backend, **§5** frontend, **§6** pruebas, **§7** decisiones
ya tomadas (no las contradigas).

---

## Fase 1 — Rama

La rama del ciclo **sale siempre de `develop` actualizado**, en frontend y
backend: partir de otra arrastra trabajo ajeno al issue y ensucia el PR.

```bash
git fetch origin develop
git checkout -b feature/<KEY_JIRA> origin/develop   # fix/<KEY_JIRA> si es un Bug
```

Si ya existe la rama del ciclo, trabaja sobre ella. Si hay cambios locales sin
guardar, **detente y avisa**: no descartes trabajo del desarrollador.

---

## Fase 2 — Desarrollo

**Base de datos** — si §3.3 lo indica, ejecuta los scripts contra la BD de
desarrollo y actualiza `scripts/DB/DB.sql`.

**Backend** — orden de capas según `CONSTITUCION.md`, siguiendo §4 del
plan. Verifica si un enum ya existe antes de crearlo.

**Frontend** — orden de capas según `CONSTITUCION.md`, siguiendo §5. Si el
plan tiene sección `## Diseño (Figma)`, la UI de esas pantallas **no se
maqueta a mano**: por cada diseño listado, ejecuta
`/figma-to-angular <URL> <KEY_JIRA>` y respeta su resultado — no continúes
hasta que su comprobación de completitud (su Paso 6, `check_completeness.py`)
pase. Si el MCP de Figma no está disponible, detente e informa igual que hace
esa skill; nunca maquetes a partir de capturas o a ojo. Sin sección de Figma,
implementa la UI como de costumbre. El resto de §5 (fuera de esas pantallas)
sigue el flujo normal.

**Pruebas** — implementa §6 con la nomenclatura de las instructions del
workspace.

---

## Fase 3 — Calidad local

1. Suite completa. **Criterio: 100% pasan.**
2. `ruff check` en backend, corrige advertencias.
3. Si cambiaron dependencias Python:
   `uv export --format requirements-txt --no-hashes --no-annotate --output-file requirements.txt`
4. Commit con el key en el mensaje: `[<KEY_JIRA>] {descripción}` — **sólo commit
   local**, nunca `push`: el desarrollador revisa antes de publicar

---

## Fase 4 — Integración

Merge de `develop` sobre tu rama y suite completa de nuevo.
**Criterio: 100% siguen pasando.** Resuelve conflictos antes de continuar.

---

## Fase 5 — Cierre y entrega

**Registra el tiempo.** Estima la duración de la implementación y llama a
`mcp__jira__jira_add_worklog` con:
- `issue_key`: `<KEY_JIRA>`
- `time_spent`: duración estimada (ej. `"3h"`, `"1d"`)
- `comment`: `"Implementación completada según docs/plan/<KEY_JIRA>.md"`

**Mueve el issue a 02.DEVELOPS.** Pide las transiciones disponibles con
`mcp__jira__jira_get_transitions`, localiza la que lleva a ese estado y
aplícala con `mcp__jira__jira_transition_issue`.

**En modo File** registra el tiempo y el estado en el Seguimiento del
requisito (`.claude/_shared/fuente-especificaciones.md`) en lugar de llamar a Jira.

**El push y el Pull Request no los ejecuta la skill.** Revisar la
implementación en local antes de publicarla es parte del trabajo del
desarrollador. Muestra el resumen y los comandos exactos, listos para copiar:

```text
✅ Implementación lista para revisar

📌 Issue: <KEY_JIRA> — <título>
🔄 Estado: 02.DEVELOPS  ·  ⏱ Tiempo registrado: <duración>
🌿 Rama: feature/<KEY_JIRA>  ·  <N> commits en local  # fix/<KEY_JIRA> si es un Bug
✅ Criterios de §2 implementados: <N/N>
🧪 Pruebas: <N pasadas / N fallidas>
📋 Decisiones de §7 relevantes para quien revise: <resumen>

Revisa el cambio en local. Cuando estés conforme:

  git push -u origin feature/<KEY_JIRA>

  gh pr create --base develop --title "[<KEY_JIRA>] <título del issue>" --body "<criterios de §2 como checklist, más las decisiones de §7>"

Y mueve el issue a 03.REVISION en Jira (en modo File: cambia su Estado en
el archivo de especificaciones).

Después: /pr-review <número> <KEY_JIRA>
```

No ejecutes ninguno de esos comandos: los muestras para que los lance el
desarrollador. Si el proyecto tiene frontend y backend en repos distintos,
muestra el par de comandos de cada uno.

---

## Fase 6 — Registro de autorizaciones

Si durante el flujo se solicitó aprobación manual para comandos de terminal, genera al final
un reporte con los fragmentos exactos para copiar en `settings.json` y `settings.local.json`,
listando únicamente los comandos que requirieron autorización.

---

## Fase 7 — Reportar consumo de tokens

Invoca `/token-spend <KEY_JIRA> "implementacion-plan"`.
