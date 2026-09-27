# Fuente de especificaciones

Las skills que leen, escriben o cambian de estado un requisito no asumen que
viva en Jira: lo deciden tres parámetros de `CONSTITUCION.md`.

| Parámetro | Valores | Uso |
|---|---|---|
| **Fuente Especificaciones** | `Jira` \| `File` | Dónde viven los requisitos, su estado y su tiempo |
| **ProyectoJira** | `{proyectoJira}` | `project_key` de las llamadas a Jira. Obligatorio si la fuente es `Jira` |
| **Archivo Especificaciones** | `{ruta del archivo}` | Fichero de requisitos, relativo al workspace. Obligatorio si la fuente es `File` |

## Validación (antes de cualquier otro paso)

Lee `CONSTITUCION.md` y resuelve la fuente. Compara el valor sin distinguir
mayúsculas ni espacios.

| Caso | Acción |
|---|---|
| `Fuente Especificaciones` = `Jira` y `ProyectoJira` definido | **Modo Jira**: usa las herramientas `mcp__jira__*` con ese `project_key` |
| `Fuente Especificaciones` = `File` y el archivo existe | **Modo File**: usa el archivo; **no llames a ninguna herramienta `mcp__jira__*`** |
| `Fuente Especificaciones` ausente o vacía | Modo Jira (compatibilidad con constituciones anteriores) |
| Valor distinto de `Jira` o `File` | Detente: `⛔ Fuente Especificaciones = "{valor}" no es válido. Usa Jira o File.` |
| Modo Jira con `ProyectoJira` ausente, vacío o `TODO` | Detente: `⛔ Fuente Jira sin ProyectoJira en CONSTITUCION.md.` |
| Modo File con `Archivo Especificaciones` ausente, vacío, `TODO` o inexistente | Detente: `⛔ No se encuentra el archivo de especificaciones "{ruta}".` |

Indica siempre en la salida de la skill el modo usado: `Fuente: Jira ({proyectoJira})`
o `Fuente: File ({ruta})`.

En modo File, `KEY` es el identificador del requisito dentro del archivo
(`ESP-01`, `BUG-03`…) y cumple el mismo papel que el key de Jira: nombra la
rama (`feature/ESP-01`), el plan (`docs/plan/ESP-01.md`) y el registro de tokens.

---

## Formato del archivo (modo File)

```markdown
## Épica {N} {Nombre}                      ← Épica

{descripción de la épica}

### {KEY} {Título}                         ← requisito (Feature/Story)

#### Seguimiento

| Campo | Valor |
|---|---|
| **Estado** | 00.TODO |
| **Tiempo invertido** | 0h 0m |
| **Estimación** | 1d |
| **Relacionado con** | — |

#### Historia de usuario
...
#### Descripción funcional
...
#### Criterios de aceptación
```gherkin
Escenario: ...
```
```

Reglas:

- **Cada requisito tiene su tabla `#### Seguimiento`**, justo debajo del título
  `###`, con **Estado** y **Tiempo invertido** obligatorios. **Estimación** y
  **Relacionado con** son opcionales (`—` si no aplican).
- **Estado** toma uno de los valores de la tabla de `.claude/_shared/estados-jira.md`.
- **Tiempo invertido** va en formato `Xh Ym` (8h = 1d), acumulado.
- La **Épica** es el título `##` inmediatamente anterior al requisito.
- Los **Bugs** van bajo un `## Bugs` al final del archivo, con título
  `### BUG-{NN} {Título}`, la misma tabla de Seguimiento y las secciones del
  bug report (`#### Descripción del problema`, `#### Pasos para reproducir`,
  `#### Comportamiento esperado`, `#### Comportamiento actual`,
  `#### Contexto adicional`). La épica va en la fila **Épica** y la prioridad
  (`Highest`, `High`, `Medium`, `Low`) en la fila **Prioridad** de su Seguimiento.
- Los **Escenarios** del bloque Gherkin hacen el papel de las subtareas de Jira:
  no tienen estado ni tiempo propios.

Si un requisito no tiene tabla de Seguimiento, trátalo como `00.TODO` con
`0h 0m`; si la skill escribe en él, crea la tabla antes.

---

## Equivalencias Jira → File

| Operación en Jira | En modo File |
|---|---|
| `mcp__jira__jira_get_issue` | Lee la sección `### {KEY}` hasta el siguiente `###` o `##`. Estado, tiempo, estimación y vínculos salen de su Seguimiento; descripción de las secciones `####`; criterios del bloque Gherkin; épica del `##` anterior |
| `mcp__jira__jira_search` | Recorre los títulos `##` y `###` del archivo y filtra por épica, tipo (Feature = `###` bajo una épica, Bug = `###` bajo `## Bugs`) o Estado |
| `mcp__jira__jira_get_transitions` | Los estados de `.claude/_shared/estados-jira.md` |
| `mcp__jira__jira_create_issue` (Epic) | Añade `## Épica {N} {Nombre}` antes de `## Bugs` (o al final) |
| `mcp__jira__jira_create_issue` (Story) | Añade `### {KEY} {Título}` al final de su épica, con Seguimiento en `00.TODO` y `0h 0m`. El `KEY` sigue la numeración existente (`ESP-15` tras `ESP-14`) |
| `mcp__jira__jira_create_issue` (Subtask) | No aplica: el Escenario ya está en el bloque Gherkin |
| `mcp__jira__jira_create_issue` (Bug) | Añade `### BUG-{NN} {Título}` bajo `## Bugs` (lo crea si no existe) |
| `mcp__jira__jira_create_issue_link` | Añade el key a **Relacionado con** en el Seguimiento de ambos requisitos |
| `mcp__jira__jira_add_worklog` | Suma la duración a **Tiempo invertido** y reescribe el total en `Xh Ym` |
| `mcp__jira__jira_transition_issue` | Sustituye el valor de **Estado**. No lo muevas hacia atrás |

Escribe en el archivo con ediciones puntuales sobre la sección del requisito:
nunca reescribas el archivo entero ni toques otros requisitos.

Estas equivalencias no amplían lo que cada skill puede hacer: si una skill no
transiciona ni registra tiempo en modo Jira, tampoco modifica **Estado** ni
**Tiempo invertido** en modo File.
