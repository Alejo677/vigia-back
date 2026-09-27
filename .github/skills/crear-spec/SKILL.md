---
name: crear-spec
description: |
  Redacta la especificación Gherkin de un requerimiento nuevo y la guarda como fichero
  local en docs/spec/, sin tocar Jira.
  Es el punto de entrada de una Feature: parte de una idea en prosa del analista.
  Para subirla a Jira después usa /crear-spec-jira; para modificarla, /ajustar-spec.
  Parámetros: "<Épica>" "<descripción del requerimiento>"
  Ejemplo: /crear-spec "Consumo de Tokens" "El usuario puede exportar los resultados a Excel"
argument-hint: "<Épica>" "<descripción>"
---

Actúa como Analista de Requisitos. Tu objetivo es tomar la descripción de un requerimiento
nuevo, enriquecerla consultando el contexto existente en Jira, redactarla en formato Gherkin
maduro y guardarla como archivo local con estado "Pendiente de aprobación" para revisión
del analista.

**No implementes el requerimiento. No lo subas a Jira.** Solo lo documentas localmente.

Parsea `$ARGUMENTS` así:
- Primer token (entre comillas) → nombre o clave de la Épica a la que pertenece
- Segundo token (entre comillas) → descripción del requerimiento tal como la expresa el analista

---

## Paso 0 — Contexto

Lee `CONSTITUCION.md` de la raíz del workspace y resuelve la fuente con
`_shared/fuente-especificaciones.md` (Validación). **Si no es válida, informa
y detente sin ejecutar ningún paso.** En modo Jira, `ProyectoJira` es el
`project_key` de todas las llamadas a Jira.

Lee además los ficheros de instructions activos del workspace (stack, capas,
testing y convenciones de código). Si no existen, deriva las reglas de
`CONSTITUCION.md`.

---

## Paso 1 — Consultar contexto en Jira

1. Busca la Épica indicada en el proyecto usando `mcp__jira__jira_search` con la clave del proyecto
   y el nombre de la Épica para obtener su `key` (ej. `IAFIT-3`) y su nombre completo.
2. Recupera las Historias hijas de esa Épica para entender qué ya está registrado,
   identificar patrones de nomenclatura (ej. `F3-001`, `F3-002`) y evitar duplicados.
3. Determina el siguiente ID correlativo de la Feature dentro de la Épica
   (ej. si existen `F3-001` y `F3-002`, el nuevo será `F3-003`). Guárdalo como `feature_id`.

En modo File, haz lo mismo sobre el archivo de especificaciones sin llamar a
Jira: la Épica es un título `## Épica` (su título completo hace de
`key_epica`), sus requisitos son los `###` que cuelgan de ella, y `feature_id`
sigue la numeración del archivo (si el último es `ESP-14`, el nuevo es `ESP-15`).

**Si la Épica no existe en la fuente, informa al usuario y detente.
No ejecutes ningún paso posterior bajo ninguna circunstancia.**

---

## Paso 2 — Redactar descripción funcional y criterios

Produce **dos bloques**, con la estructura obligatoria del campo Descripción
que el MCP convertirá al formato de Jira (se escribe en Markdown estándar):

**1. Descripción funcional** — prosa con el QUÉ, desglosada en subsecciones
`###` por agrupación lógica. Cada elemento en lista con el nombre en negrita,
su obligatoriedad entre paréntesis y una descripción breve:

```markdown
### Campos del formulario

- **Nombre de la variable** (obligatorio): identificador interno, visible en Backoffice
- **Tipo** (obligatorio): selector con valores Enum y Fórmula
  - ID de traducción de la sección (obligatorio)
  - Path de la imagen (opcional): texto libre
```

**2. Criterios de aceptación** — Gherkin **en español**:

```gherkin
Antecedentes:
  Dado que <precondición común a todos los escenarios>

Escenario: <título descriptivo, sin punto final>
  Dado que <estado inicial del sistema>
  Cuando <acción única del usuario>
  Entonces <resultado verificable>
  Y <resultado adicional si aplica>

Escenario: <caso de error o borde>
  Dado que <estado>
  Cuando <acción que provoca el error>
  Entonces <mensaje o comportamiento esperado>
```

Criterios de calidad:

- Incluye siempre el flujo principal y los casos de error relevantes.
- `Dado que` describe **estado**, nunca acciones.
- `Cuando` es **una sola** acción. Si hay dos, son dos escenarios.
- `Entonces` es verificable desde la perspectiva del usuario: qué ve, qué
  aparece, qué se guarda. Nada de tablas ni endpoints.
- Datos tabulares → tabla Gherkin `| columna |`.
- **Todo en español**: `Antecedentes`, `Escenario`, `Dado que`, `Cuando`,
  `Entonces`, `Y`, `Pero`. Nunca en inglés: el equipo lee los criterios en
  Jira y deben estar en su idioma.
- **Un escenario, una línea de título**, descriptivo y sin punto final.
- **Marca la obligatoriedad** de cada campo entre paréntesis: `(obligatorio)`
  o `(opcional)`.
- **Negrita para el nombre** del campo o elemento, texto normal para su
  descripción.
- **Nada de emojis** en el campo Descripción, ni detalle de implementación
  (rutas de ficheros, tablas, clases): eso va en el plan técnico.

Muestra ambos bloques al usuario con el `feature_id` asignado (ej. `F3-003`) y
el título propuesto. Ajusta si pide cambios.

---

## Paso 3 — Estimar el esfuerzo de implementación

Estima el tiempo que tomaría implementar la funcionalidad completa (backend + frontend + tests)
para un desarrollador que se apoya en IA para asistencia, pero entiende el código,
toma decisiones y valida el resultado.

| Complejidad | Criterio | Estimación |
|---|---|---|
| Simple | 1–2 escenarios, una sola capa, sin BD | `4h` – `8h` |
| Media | 3–5 escenarios, backend + frontend + tests | `1d` – `2d` |
| Alta | 6+ escenarios, múltiples capas, cambios en BD | `3d` – `5d` |
| Muy alta | Arquitectura nueva, impacto cross-feature, seguridad | `+5d` |

Guarda el valor elegido como `esfuerzo_implementacion` (ej. `"1d"`, `"3d"`).

---

## Paso 4 — Escribir el archivo local

Crea el archivo en `docs/spec/{feature_id}.md`. Si el directorio `docs/spec/` no existe, créalo.

El fichero replica **exactamente** la estructura que acabará en Jira, para que
`/crear-spec-jira` la copie sin transformar nada:

````markdown
---
feature_id: {feature_id}
epica: {key_epica}
proyecto: {project_key, o File en modo File}
fecha: {YYYY-MM-DD}
esfuerzo_implementacion: {esfuerzo}
---
estado: Pendiente de aprobación
---

## Descripción funcional

{Prosa con el propósito del requerimiento y su encaje en la épica}

### {Agrupación lógica}

- **{Elemento}** (obligatorio): {descripción}
- **{Elemento}** (opcional): {descripción}
  - {Sub-elemento si el anterior se desglosa}

## Criterios de aceptación

```gherkin
Antecedentes:
  Dado que {precondición común, sólo si aplica}

Escenario: {título del flujo principal}
  Dado que {estado}
  Cuando {acción}
  Entonces {resultado}

Escenario: {título del caso de error}
  Dado que {estado}
  Cuando {acción}
  Entonces {resultado}
```
````

> **Nota para el analista:** Revisa este documento y cambia el campo `estado` de
> `Pendiente de aprobación` a `Aprobado` antes de ejecutar `/crear-spec-jira`.

---

## Paso 5 — Confirmar

Muestra el resultado:

```
✅ Requerimiento documentado localmente

📌 Épica padre: {KEY_EPICA} — {nombre épica}
🔖 Feature ID: {feature_id}
📄 Archivo: docs/spec/{feature_id}.md
🕐 Estado: Pendiente de aprobación
⏱ Esfuerzo estimado: {esfuerzo_implementacion}

Revisa el documento y cambia el estado a "Aprobado" antes de ejecutar /crear-spec-jira.
```

Si hubo algún error al crear el directorio o escribir el archivo, muéstralo al usuario con el detalle del error.

## Paso 6 — Reportar consumo de tokens

Invoca `/token-spend "General" "crear-spec"`.