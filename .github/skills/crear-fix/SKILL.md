---
name: crear-fix
description: |
  Registra un defecto nuevo en Jira como issue de tipo Bug, redactando el bug report
  a partir de la descripción del usuario y asociándolo a su Épica.
  Es el punto de entrada de un bug: sólo lo documenta y lo crea.
  Para corregirlo después usa /solucionar-fix.
  Parámetros: "<descripción del bug>" "<Épica>" [<key Historia opcional>]
  Ejemplo: /crear-fix "El filtro de fechas se ignora con granularidad por minuto" "Consumo de Tokens" IAFIT-42
argument-hint: "<descripción>" "<Épica>" [KEY_HISTORIA]
---

Actúa como QA Engineer y Scrum Master. Tu objetivo es tomar la descripción de un defecto,
enriquecerla con el contexto de Jira, redactarla en el formato estándar de bug report
y registrarla como un issue de tipo Bug en el proyecto.

**No implementes el fix.** Solo lo documentas y registras.

Parsea `$ARGUMENTS` así:
- Primer token (entre comillas) → descripción del bug tal como la reporta el usuario
- Segundo token (entre comillas) → nombre o clave de la Épica a la que pertenece
- Tercer token (opcional) → key de la Historia relacionada (ej. `IAFIT-42`); si se omite, el bug solo se asocia a la Épica

---

## Paso 0 — Contexto

Lee `CONSTITUCION.md`. Resuelve la fuente con `_shared/fuente-especificaciones.md` (Validación) y
detente si no es válida. En modo Jira, `ProyectoJira` es el `project_key` de
todas las llamadas a Jira.

En modo File, cada operación de Jira de esta skill se hace sobre el archivo de
especificaciones con las equivalencias de ese documento: la Épica es un
`## Épica`, la Historia un `### {KEY}` y el Bug se crea como `### BUG-{NN}`
bajo `## Bugs`, con Seguimiento en `00.TODO` y `0h 0m`, la **Estimación** del
Paso 3.1 y las filas **Épica** y **Prioridad**. El vínculo del Paso 4 va en
**Relacionado con**.

---

## Paso 1 — Consultar contexto en Jira

1. Busca la Épica indicada en el proyecto usando `mcp__jira__jira_search` con la clave del proyecto
   y el nombre o key de la Épica para obtener su `key` (ej. `IAFIT-3`).
2. Si se proporcionó una Historia en el cuarto argumento, recupera ese issue con `mcp__jira__jira_get_issue`
   para entender el requerimiento afectado y usarlo como contexto en la descripción del bug.
3. Revisa los bugs existentes bajo esa Épica para evitar duplicados y entender el patrón de numeración.

Si la Épica no existe en Jira, informa al usuario y detente.

---

## Paso 2 — Analizar y redactar el bug report

Con base en la descripción del usuario y el contexto recuperado, redacta el bug report
con el siguiente formato estándar:

Usa esta plantilla:

```markdown
## Descripción del problema

<qué falla, en una o dos frases>

## Pasos para reproducir

1. <paso concreto y repetible>
2. <siguiente paso>
3. <el que desencadena el error>

## Comportamiento esperado

<qué debería ocurrir, referenciable a un criterio de aceptación>

## Comportamiento actual

<qué ocurre en realidad>

## Contexto adicional

<entorno, condiciones especiales, notas. Omite la sección si no aplica>
```

La **severidad no va en la descripción**: se refleja en el campo Priority.
**Nada de emojis** en el campo Descripción: van en la salida por consola de
la skill, no en el issue. Determínala para mapearla en el Paso 3:

| Severidad | Criterio | Priority |
|---|---|---|
| Crítica | Bloquea una funcionalidad principal sin workaround | `Highest` |
| Alta | Impacta una funcionalidad principal, hay workaround | `High` |
| Media | Impacta una funcionalidad secundaria o degradada | `Medium` |
| Baja | Cosmético o usabilidad menor | `Low` |

Criterios para la redacción:
- Los pasos para reproducir deben ser específicos y repetibles.
- El comportamiento esperado debe poder referenciarse en la especificación o en el criterio de aceptación del requerimiento afectado.
- Asigna la severidad según el impacto real en el usuario final, no en la dificultad técnica de la corrección.
- Si la descripción original es vaga, infiere el contexto razonable a partir de la Épica e Historia recuperadas.

Muestra el bug report redactado al usuario antes de continuar. Ajusta si el usuario solicita cambios.

---

## Paso 3 — Crear el Bug en Jira

### 3.1 — Estimar el esfuerzo de corrección

Antes de crear el issue, estima el tiempo que tomaría corregir el bug a un desarrollador
que se apoya en IA para asistencia (autocompletado, revisión, sugerencias), pero **no** usa
vibe coding ni spec-driven development — es decir, el desarrollador entiende el código,
toma decisiones y valida el resultado.

Usa esta escala como referencia:

| Complejidad | Criterio | Estimación |
|---|---|---|
| Trivial | Cambio de texto, config, CSS cosmético | `30m` |
| Simple | Lógica puntual en una función o componente | `1h` |
| Medio | Afecta un flujo completo, requiere tests | `2h` – `3h` |
| Complejo | Múltiples capas, impacto en BD o seguridad | `4h` – `8h` |
| Crítico | Rediseño de flujo, impacto cross-feature | `16h` |

Registra la estimación elegida como `original_estimate` en formato Jira (ej. `"2h"`, `"30m"`).

### 3.2 — Crear el issue

Crea el issue llamando a `mcp__jira__jira_create_issue` con:
- `project_key`: clave del proyecto
- `summary`: título corto y descriptivo del bug (máx. 10 palabras, en español)
  (ej. `Filtro de fechas ignorado con granularidad por minuto`)
- `issue_type`: `"Bug"`
- `description`: bug report completo redactado en el Paso 2
- `additional_fields`:
  ```json
  {
    "parent": "<key_epica>",
    "labels": ["bug"],
    "priority": { "name": "<Highest|High|Medium|Low>" },
    "timetracking": { "originalEstimate": "<original_estimate>" }
  }
  ```
  La `priority` sale de la tabla de severidad del Paso 2.

Guarda el `key` del Bug creado (ej. `IAFIT-55`) para los pasos siguientes.

---

## Paso 4 — Vincular al requerimiento (si se proporcionó)

Si el cuarto argumento contiene una key de Historia, crea un vínculo entre el bug y esa Historia
llamando a `mcp__jira__jira_create_issue_link` con:
- `issue_key`: key del Bug recién creado
- `linked_issue_key`: key de la Historia proporcionada
- `link_type`: `"Relates"` (relación bidireccional: el bug se relaciona con el requerimiento)

> Si `"Relates"` falla, reintenta con `"relates to"` o `"Relacionado con"`.

---

## Paso 5 — Confirmar

Muestra al usuario el resultado con este formato:

```
✅ Bug registrado en proyecto <PROYECTO>

📌 Épica padre: <KEY_EPICA> — <nombre épica>
🐛 Bug creado: <KEY> — <título>  ·  Prioridad: <nivel>
🔗 Vinculado a: <KEY_HISTORIA> — <título>   ← sólo si se proporcionó

Siguiente paso: /analisis-spec <KEY> para planificar la corrección,
o directamente /solucionar-fix <KEY> si la causa ya está clara.
```

Si hubo errores en algún issue o en el vínculo, muéstralos al final indicando qué falló y el motivo.

## Paso 6 — Reportar consumo de tokens

Invoca `/token-spend <KEY_BUG> "crear-fix"`, usando el key de la epica donde se creo el Bug creado en el Paso 3.2.