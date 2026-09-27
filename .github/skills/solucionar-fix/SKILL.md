---
name: solucionar-fix
description: |
  Corrige un Bug ya registrado en Jira: diagnostica la causa raíz, aplica el cambio
  mínimo y añade el test que lo cubre, dejándolo commiteado en local.
  Crea fix/{KEY} desde develop actualizado.
  No publica: el push, el PR y la transición en Jira los hace el desarrollador.
  Para Features usa /implementacion-plan; para registrar el bug primero, /crear-fix.
  Parámetros: "<KEY_JIRA>"
  Ejemplo: /solucionar-fix IAFIT-55
argument-hint: "<KEY_JIRA>"
---

Actúa como Desarrollador Senior especializado en diagnóstico de defectos. Resuelve
el bug con el **cambio mínimo necesario**: sin refactorizaciones ni funcionalidad
no solicitada.

Ejecuta las fases en orden.

---

## Fase 0 — Contexto y diagnóstico

Lee `CONSTITUCION.md` y los ficheros de instructions activos del workspace.
Los estados salen de `_shared/estados-jira.md`.

**Fuente** — resuélvela con `_shared/fuente-especificaciones.md` (Validación) y
detente si no es válida. En modo File, cada lectura de Jira de esta skill es la
sección `### {KEY}` (bajo `## Bugs`) del archivo de especificaciones: estado y estimación salen
de su Seguimiento; las subtareas, de los Escenarios del Gherkin.

Del issue (`mcp__jira__jira_get_issue` con `$ARGUMENTS`) extrae como fuente de
verdad: pasos para reproducir, comportamiento esperado y actual, prioridad,
épica padre e issue vinculado.

Detente si el issue está en DEPRECATED. Si ya está en 03.REVISION o
posterior, advierte que la corrección ya terminó.

Si el issue no existe o su descripción no permite reproducir el bug, detente.

**No muevas el issue.** Si aún no está en **02.DEVELOPS**, recuérdalo al
usuario para que lo mueva él: las transiciones en Jira son suyas.

**Causa raíz** — antes de tocar nada, produce un resumen con:

1. Ficheros involucrados
2. La causa raíz, no el síntoma
3. Riesgo de regresión sobre features ya implementadas
4. TODOs relacionados con este key
5. Enfoque de corrección

---

## Fase 1 — Rama

La rama del ciclo **sale siempre de `develop` actualizado**: partir de otra
rama arrastra trabajo ajeno al fix y ensucia el PR.

```bash
git fetch origin develop
git checkout -b fix/{KEY} origin/develop      # feature/{KEY} si es una Feature
```

Si ya existe la rama del ciclo, trabaja sobre ella. Si hay cambios locales sin
guardar, **detente y avisa**: no descartes trabajo del desarrollador.

---

## Fase 2 — Corrección

Corrige exactamente lo que describe el bug report. No reescribas lo que
funciona. Si detectas deuda técnica adyacente, regístrala con `# TODO` en vez de
arreglarla aquí.

Respeta el orden de capas de `CONSTITUCION.md` — pero no crees capas
enteras si el fix es puntual.

- **BD** — si el fix lo exige, ejecuta los scripts en desarrollo y actualiza
  `scripts/DB/DB.sql`
- **Frontend** — comprueba que spinner, error y éxito siguen funcionando
- **Pruebas** — añade el test del escenario que causó el defecto.
  **El test que fallaba antes del fix debe pasar después.**

---

## Fase 3 — Calidad local

1. `pytest tests/ -m unit` — **100% deben pasar**
2. `ruff check` — corrige todo; usa `--fix` donde aplique
3. Si cambiaron dependencias Python:
   `uv export --format requirements-txt --no-hashes --no-annotate --output-file requirements.txt`
4. `git commit -m "fix({KEY}): descripción concisa"` — **sólo commit local**,
   nunca `push`: el desarrollador revisa antes de publicar

---

## Fase 4 — Integración

```
git fetch origin develop
git merge origin/develop
```

Resuelve conflictos; si son complejos, descríbelos antes de tocarlos. Vuelve a
ejecutar la suite: **100% siguen pasando.**

---

## Fase 5 — Entrega al desarrollador

**Aquí la skill se detiene.** El push, el Pull Request y la transición en Jira
los ejecuta una persona: revisar el fix en local antes de publicarlo es parte
del trabajo, y mover la tarjeta es el gesto con el que se aprueba.

Después muestra el resumen y los comandos exactos, listos para copiar:

```text
✅ Corrección lista para revisar

📌 Issue: {KEY} — <título>
🌿 Rama: fix/{KEY}  ·  <N> commits en local
⚙️ Ficheros:
   - <ruta> — <cambio>
🧪 Pruebas: <N pasadas / N fallidas>
🔍 Causa raíz: <una línea>

Revisa el cambio en local. Cuando estés conforme:

  git push -u origin fix/{KEY}

  gh pr create --base develop --title "fix({KEY}): <título corto>" --body "<causa raíz, ficheros, cómo verificar, tests que la validan>"

Y mueve el issue a 03.REVISION en Jira (en modo File: cambia su Estado en
el archivo de especificaciones).

Después: /pr-review <número> {KEY}
```

No ejecutes ninguno de esos comandos: los muestras para que los lance el
desarrollador.

---

## Paso 6: Reportar consumo de tokens

Invoca `/token-spend {KEY} "solucionar-fix"`.

