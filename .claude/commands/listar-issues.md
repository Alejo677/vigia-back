---
name: listar-issues
description: |
  Consulta el tablero de Jira y muestra un dashboard de solo lectura con los issues
  agrupados por columna del tablero, su tiempo invertido y su estimación.
  No modifica nada: sirve para saber en qué estado está el proyecto.
  Admite filtrar por columna, por tipo (Bug/Feature) o ver el detalle de un issue.
  Parámetros: [<columna | KEY | tipo>] — opcional
  Ejemplo: /listar-issues "02.DEVELOPS"
argument-hint: "[columna | KEY | Bug | Feature]"
---

Actúa como Jefe de Proyecto. Tu objetivo es consultar Jira y presentar un reporte
visual del estado actual del proyecto, incluyendo información de tiempo.

---

## Paso 0 — Contexto

Resuelve la fuente con `.claude/_shared/fuente-especificaciones.md` (Validación) y
detente si no es válida. En modo Jira, `ProyectoJira` es el `project_key` de
las consultas JQL; en modo File, los issues son los requisitos del archivo
indicado en `Archivo Especificaciones`.

Las columnas del tablero están en `.claude/_shared/estados-jira.md`. **No las
hardcodees en el JQL**: consúltalas con `mcp__jira__jira_get_transitions` sobre
un issue del proyecto, o deja que la consulta devuelva todos los estados y
agrúpalos por el que traiga cada issue.

---

## Paso 1 — Interpretar el argumento

El argumento recibido es: `$ARGUMENTS`

| Argumento | Comportamiento |
|---|---|
| Vacío | Consulta todas las columnas |
| Nombre de columna (ej. `02.DEVELOPS`) | Solo esa columna |
| Key de issue (ej. `IAFIT-42`) | Detalle completo de ese issue |
| `Bug` | Solo issues de tipo Bug en todas las columnas |
| `Feature` | Solo issues de tipo Feature en todas las columnas |

---

## Paso 2 — Consultar la fuente

**Modo File** — no llames a Jira. Lee el archivo y aplica las equivalencias de
`.claude/_shared/fuente-especificaciones.md`: cada `###` es un issue (Feature bajo una
épica, Bug bajo `## Bugs`); su **Estado** es la columna, **Tiempo invertido**
es Time Spent y **Estimación** es Original Estimate. Los campos sin
equivalente (prioridad, asignado, fechas) se muestran como `—`; en la vista
de un issue, los Escenarios del Gherkin sustituyen a las subtareas. Aplica
los mismos filtros del Paso 1 y continúa en el Paso 3.

**Modo Jira** — usa `mcp__jira__jira_search` con JQL y los campos necesarios.

### Consulta general (todas las columnas o filtrada por columna/tipo)

> Las Features se publican como `issuetype = "Story"` con `labels = "feature"`
> (ver `.claude/commands/crear-spec-jira.md:129-139`), no como
> `issuetype = "Feature"`. El JQL debe reflejar esa convención.

```
JQL: project = {ProyectoJira}
     AND (issuetype = "Bug" OR (issuetype = "Story" AND labels = "feature"))
     [AND status = "{columna}"]                          ← solo si se filtró por columna
     [AND issuetype = "Bug"]                              ← solo si se filtró por Bug
     [AND issuetype = "Story" AND labels = "feature"]     ← solo si se filtró por Feature
     ORDER BY status ASC, created ASC

fields: summary, status, issuetype, priority, assignee,
        timespent, timeoriginalestimate, timeestimate,
        parent, labels, created, updated
```

### Consulta de issue específico

Si el argumento es un key de issue, usa `mcp__jira__jira_get_issue` con ese key
y solicita los campos: `summary, status, issuetype, priority, assignee, description,
timespent, timeoriginalestimate, timeestimate, parent, subtasks, labels, created, updated`.

---

## Paso 3 — Procesar tiempos

Los valores de tiempo en Jira vienen en segundos (en modo File ya vienen en
`Xh Ym`: úsalos tal cual). Conviértelos al formato `Xh Ym`:
- `timespent` → **Time Spent**
- `timeoriginalestimate` → **Original Estimate**
- Si el campo es `null` o `0` → mostrar `—`

```
Ejemplo: 7200 segundos → "2h 0m"
         5400 segundos → "1h 30m"
```

---

## Paso 4 — Construir el reporte

### Vista de tablero completo (sin filtro o filtro por tipo)

```
## 📋 Issues — {ProyectoJira o nombre del archivo}
📅 {fecha actual}    🔍 Filtro: {argumento o "Todos"}    📂 Fuente: {Jira | File}

### Resumen por columna
| Columna | Issues | Time Spent | Original Estimate |
|---|---|---|---|
| {una fila por columna del tablero, en su orden} | N | Xh Ym | Xh Ym |
| **TOTAL** | N | Xh Ym | Xh Ym |

---

### {Primera columna} (N)
| Key       | Tipo     | Título                          | Prioridad | Estimate | Asignado |
|-----------|----------|---------------------------------|-----------|----------|----------|
| {KEY} | Story | {título} | 🔴 High | 4h 0m | — |
| ...       | ...      | ...                             | ...       | ...      | ...      |

### {Siguiente columna} (N)
| Key       | Tipo     | Título                          | Prioridad | Estimate | Time Spent | Asignado |
|-----------|----------|---------------------------------|-----------|----------|------------|----------|
| {KEY} | Story | {título} | 🟠 Medium | 3h 0m | 1h 30m | — |
| ...       | ...      | ...                             | ...       | ...      | ...        | ...      |

### {Columnas intermedias} (N)
(mismas columnas)



### {Columna final: DONE} (N)
| Key       | Tipo     | Título                          | Time Spent | Estimate | Desviación |
|-----------|----------|---------------------------------|------------|----------|------------|
| {KEY} | Story | {título} | 8h 0m | 6h 0m | +2h 0m |
| ...       | ...      | ...                             | ...        | ...      | ...        |
```

> En la columna **DONE** agrega **Desviación** = Time Spent − Original Estimate
> (formato `+Xh Ym` si se excedió, `-Xh Ym` si se terminó antes, `—` si falta algún valor).

---

### Vista de columna única (filtro por columna)

Muestra solo la sección de esa columna con el resumen de totales de tiempo al final.

---

### Vista de issue específico

```
## 🔍 IAFIT-42 — {título}

| Campo              | Valor                  |
|--------------------|------------------------|
| Tipo               | Historia               |
| Estado             | 02.DEVELOPS            |
| Prioridad          | 🔴 High                |
| Épica padre        | IAFIT-3 — {nombre}     |
| Asignado           | —                      |
| Original Estimate  | 4h 0m                  |
| Time Spent         | 1h 30m                 |
| Tiempo restante    | 2h 30m                 |
| Creado             | 2026-05-15             |
| Actualizado        | 2026-05-28             |
| Labels             | feature                |

### Descripción
{descripción completa del issue}

### Subtareas (N)
| Key       | Título                                    | Estado      | Time Spent |
|-----------|-------------------------------------------|-------------|------------|
| {KEY} | {título del escenario} | DONE | 0h 45m |
| {KEY} | {título del escenario} | 02.DEVELOPS | — |
```

---

## Paso 5 — Notas al pie

Añade siempre al final:

- Issues sin estimación: keys con `Original Estimate = —` en columnas activas
  (excluye 00.TODO, DONE y DEPRECATED).
- Issues en curso (02.DEVELOPS, 03.REVISION) sin asignado.
- Ordenar siempre por key ascendente dentro de cada columna.

---

## Paso 6 — Reportar consumo de tokens

Invoca `/token-spend "General" "listar-issues"`.
