---
name: crear-spec-jira
description: |
  Sube a Jira un fichero de especificación Gherkin ya escrito y aprobado, creando la
  Feature como Story con sus criterios, y una Subtask por cada Escenario.
  Es el paso de publicación: /crear-spec redacta el fichero local, éste lo carga.
  Acepta el formato de /crear-spec o una especificación consolidada con varias Épicas.
  Parámetros: "<ruta_fichero>"
  Ejemplo: /crear-spec-jira docs/spec/F3-001.md
argument-hint: "<ruta del fichero de spec>"
---

Actúa como Scrum Master experto en Jira. Lee el fichero de especificación y crea
los issues siguiendo la estructura obligatoria del campo Descripción: Gherkin
en español, negrita para el nombre del campo, obligatoriedad entre paréntesis,
sin emojis ni detalle de implementación.

Parsea `$ARGUMENTS` así:
- Único token → ruta del archivo de especificaciones (relativa al workspace)

Lee `CONSTITUCION.md` y resuelve la fuente con
`.claude/_shared/fuente-especificaciones.md` (Validación). **Si no es válida, detente
sin ejecutar ningún paso.** En modo Jira, `ProyectoJira` es el `project_key`.

**Modo File** — el destino no es Jira sino el archivo de especificaciones:
cada creación de esta skill se aplica con las equivalencias de ese documento.
La Épica debe existir como `## Épica` (en modo masivo se crea si falta); la
Feature se añade como `### {feature_id} {summary}` con su Seguimiento
(`00.TODO`, `0h 0m`, **Estimación** = `esfuerzo_implementacion`), su
`#### Descripción funcional` y sus `#### Criterios de aceptación`; no se crean
subtareas. Si ya existe un `###` con ese `feature_id`, no lo dupliques:
informa y sáltalo. Si la ruta indicada es el propio archivo de
especificaciones, no hay nada que publicar: informa y detente. El worklog del
Paso 5 se suma a su **Tiempo invertido**.

Ejecuta los pasos en orden.

---

## Paso 1: Leer el archivo y detectar el modo

Usa la herramienta `Read` con la ruta del archivo indicada en el argumento.

Si el archivo no existe, informa al usuario y detente.

Detecta el modo según el contenido:

**Modo individual** (archivo generado por `/crear-spec`): el archivo comienza con un bloque de metadatos
(`---`) con los campos `feature_id`, `epica` y `esfuerzo_implementacion`, y contiene
las secciones `## Descripción funcional` y `## Criterios de aceptación`.
Guarda los valores del bloque de metadatos para usarlos en los pasos siguientes.

**Modo masivo** (especificación consolidada): el archivo contiene títulos `##` para Épicas,
títulos `###` para Features, cada una con su descripción funcional en prosa y su
bloque Gherkin de criterios.

Si el archivo no corresponde a ninguno de los dos formatos, informa al usuario y detente.

---

## Paso 2: Extraer la jerarquía completa

### En modo individual

Del bloque de metadatos: `feature_id`, `epica` (key de la Épica padre) y
`esfuerzo_implementacion`.

Del cuerpo:

- **descripcion_funcional**: la sección `## Descripción funcional` completa,
  con sus subsecciones `###` y listas, tal cual
- **criterios**: el bloque Gherkin de `## Criterios de aceptación`, íntegro
- **summary**: el título de la Feature

### En modo masivo

**Épicas** (título `##`)
- **summary**: título sin el `## `
- **description**: el blockquote `>` que le sigue

**Features** (título `###`)
- **feature_id**: el código inicial del título (`F1-001`)
- **summary**: título completo sin `### `
- **descripcion_funcional**: la sección de descripción de la Feature
- **criterios**: su bloque Gherkin íntegro
- **epic_parent**: la Épica `##` inmediatamente anterior
- **esfuerzo_implementacion**: si el documento lo anota; si no, omite
  `timetracking` al crear el issue

> Si el Gherkin del documento está en inglés (`Scenario`, `Given`, `When`,
> `Then`), **tradúcelo al español** antes de subirlo: `Escenario`, `Dado
> que`, `Cuando`, `Entonces`, `Y`, `Pero`.

---

## Paso 3: Validar y crear las Épicas

### En modo individual

La Épica ya está identificada por su key en el bloque de metadatos. Llama a `mcp__jira__jira_get_issue`
con esa key para confirmar que existe en Jira. Guarda el key y el nombre de la Épica para los pasos siguientes.

**Si la Épica no existe en Jira, informa al usuario y detente.**

### En modo masivo

Para cada Épica identificada en el documento, busca en Jira si ya existe una Epic con ese mismo `summary`
en el proyecto usando `mcp__jira__jira_search`.

- Si **ya existe**: guarda su key y úsala para los pasos siguientes. No crees un duplicado.
- Si **no existe**: llama a `mcp__jira__jira_create_issue` con:
  - `project_key`: valor de `ProyectoJira`
  - `summary`: título de la Épica
  - `issue_type`: `"Epic"`
  - `description`: texto del bloque `>` de la Épica

**Guarda el `key` de cada Épica** (ej. `IAFIT-1`) para usarlo como `parent` en los pasos siguientes.

---

## Paso 4: Crear los issues de Feature y sus subtareas

### 4.1 — Crear el issue de Feature

La `description` lleva **las dos secciones**: la descripción funcional da el
contexto y los criterios lo hacen verificable. Una Story sin criterios en su
descripción obliga a abrir las subtasks para saber qué se pide.

````markdown
## Descripción funcional

{contenido de descripcion_funcional, con sus subsecciones ### y listas}

## Criterios de aceptación

```gherkin
{contenido de criterios, íntegro y en español}
```
````

Llama a `mcp__jira__jira_create_issue` con:
- `project_key`: valor de `ProyectoJira`
- `summary`: `<feature_id> — <summary>`
- `issue_type`: `"Story"`
- `description`: el markdown de arriba
- `additional_fields`:
  ```json
  {
    "parent": "<key_epica>",
    "labels": ["feature"],
    "timetracking": { "originalEstimate": "<esfuerzo_implementacion>" }
  }
  ```
  Omite `timetracking` si no hay estimación.

**Guarda el `key` de la Feature** (ej. `IAFIT-11`).

### 4.2 — Crear una subtarea por cada Escenario

Extrae cada `Escenario:` de `criterios` individualmente.

Para cada uno, llama a `mcp__jira__jira_create_issue` con:
- `project_key`: valor de `ProyectoJira`
- `summary`: el título del escenario, sin el prefijo `Escenario:`
- `issue_type`: `"Subtask"`
- `description`: el escenario completo con sus pasos y tablas, en bloque
  `gherkin`:
  ````
  ```gherkin
  Escenario: <título>
    Dado que <...>
    Cuando <...>
    Entonces <...>
  ```
  ````
- `additional_fields`: `{ "parent": "<key_feature>" }`

**Guarda el `key` de cada subtarea** para el reporte del paso 6.

> Si hay bloque `Antecedentes:`, inclúyelo al principio de **cada** subtarea
> para que sea autocontenida.

---

## Paso 5: Registrar tiempo invertido por Feature

Para cada Feature creada, estima el tiempo dedicado a procesarla en este skill
(leer su bloque Gherkin, construir la descripción, crear el issue):
- 1–2 escenarios, Gherkin claro → `5m`
- 3–5 escenarios o con Antecedentes → `10m`
- 6+ escenarios o tablas complejas → `15m`

Llama a `mcp__jira__jira_add_worklog` por cada Feature con:
- `issue_key`: key de la Feature
- `time_spent`: duración estimada (ej. `"5m"`, `"10m"`, `"15m"`)
- `comment`: `"Especificación Gherkin cargada desde <nombre_archivo>"`

---

## Paso 6: Mostrar resumen final

Al completar la creación, muestra un resumen con este formato:

```
✅ Issues creados en proyecto <PROYECTO>

📌 Épicas (N):
  <KEY>: <titulo>
  ...

📋 Features (N):
  <KEY>: <feature_id> — <summary> → Epic: <KEY_EPICA>
  ...

🔢 Total: N issues creados
```

Si hubo errores en algún issue, muéstralos al final con el tipo y título del issue fallido.

---

## Paso 7 — Reportar consumo de tokens

Invoca `/token-spend "General" "crear-spec-jira"`.
