---
name: analisis-spec
description: |
  Convierte un issue de Jira en un plan técnico y lo escribe en docs/plan/{KEY}.md
  con Estado: pendiente de aprobacion, para que un humano lo revise antes de codificar.
  Diseña las capas de backend y frontend, el impacto y el plan de pruebas — pero no
  escribe código: eso lo hace /implementacion-plan una vez aprobado el plan.
  No mueve el issue: el trabajo aún no ha empezado.
  Parámetros: "<KEY_JIRA>"
  Ejemplo: /analisis-spec IAFIT-42
argument-hint: "<KEY_JIRA>"
---

Actúa como Arquitecto Full-Stack Senior. Analiza el item, evalúa su impacto y
produce un documento de diseño que un humano pueda revisar y aprobar antes de que
empiece el desarrollo.

Ejecuta los pasos en orden.

---

## Paso 1 — Contexto

Lee `CONSTITUCION.md`. Resuelve la fuente con `_shared/fuente-especificaciones.md` (Validación) y
detente si no es válida. En modo Jira, `ProyectoJira` es el `project_key` de
las llamadas a Jira. Si `Archivo Especificaciones` está definido, léelo entero:
es el marco funcional del análisis. Los estados salen de `_shared/estados-jira.md`.

Del issue extrae descripción funcional, criterios de aceptación y
dependencias con otros issues (implementados y pendientes): en modo Jira con
`mcp__jira__jira_get_issue` (criterios = subtareas); en modo File, de la
sección `### {KEY}` del archivo (criterios = Escenarios del Gherkin;
dependencias = **Relacionado con** y la tabla de dependencias del archivo).

---

## Paso 2 — Impacto

1. **Riesgos de regresión**: qué issues ya implementados podría romper este
   cambio, con nombre de fichero y motivo concreto.
2. **TODOs relacionados**: busca `# TODO: ... {KEY}` en el código y lista
   fichero:línea.
3. **Cambios transversales**: esquema de BD, variables de entorno
   (`.env.example`, `local.settings.json`), dependencias (`pyproject.toml`,
   `package.json`).

---

## Paso 3 — Diseño

Sigue el orden de capas de `CONSTITUCION.md`. Para cada capa afectada,
lista los ficheros a crear o modificar con **ruta exacta** y una descripción
breve de su contenido.

**Backend** (Inside-Out): enums y excepciones → entidades → modelos de resultado
→ interfaces → casos de uso → prompts de IA si aplica → infraestructura →
entrega (sólo si los criterios de aceptación la exigen).

**Frontend** (Domain-First): modelos de dominio → contratos de repositorio →
servicios de aplicación → infraestructura → componentes de presentación.

**Diseño (Figma)**: busca en el issue (descripción, comentarios, adjuntos,
enlaces) URLs de Figma (`figma.com/design/`, `figma.com/file/`,
`figma.com/proto/`). Si hay alguna, el plan debe incluir una sección
`## Diseño (Figma)` con cada URL (y su `node-id` si lo lleva) y a qué
pantalla o componente corresponde, indicando que la capa de UI de esas
pantallas se implementará con `/figma-to-angular` en vez de a mano. Si no
hay ninguna URL, no añadas esa sección — no inventes diseños.

---

## Paso 4 — Plan de pruebas

Lista los casos unitarios y de integración con escenario y resultado esperado,
usando `test_<funcion>_<escenario>_<resultado_esperado>`.

---

## Paso 5 — Documento

Crea `docs/plan/{KEY}.md` con esta estructura exacta:

```markdown
# Análisis de Implementación — {KEY}: {título}

Estado: pendiente de aprobacion

---

## 1. Descripción funcional
{descripción completa del issue, tal como está en la fuente (Jira o archivo)}

## 2. Criterios de aceptación
{los Escenarios Gherkin del issue, uno por línea numerada}

## 3. Análisis de impacto
### 3.1 Riesgos de regresión
{issue afectado, fichero y motivo. "Ninguno" si no aplica}

### 3.2 TODOs a resolver
{ruta/fichero:línea. "Ninguno" si no hay}

### 3.3 Cambios transversales
{BD, variables de entorno, dependencias. "Ninguno" si no aplica}

## 4. Plan de implementación — Backend
| Capa | Archivo | Acción | Descripción |
|---|---|---|---|

## 5. Plan de implementación — Frontend
| Capa | Archivo | Acción | Descripción |
|---|---|---|---|

## Diseño (Figma) — sólo si el issue trae URLs de Figma
{URL, node-id si lo lleva, y pantalla/componente al que corresponde. La UI
se implementa con /figma-to-angular en vez de a mano}

## 6. Plan de pruebas
| Test | Tipo | Escenario | Resultado esperado |
|---|---|---|---|

## 7. Notas y decisiones de diseño
{decisiones no triviales, alternativas descartadas, advertencias}
```

---

## Paso 6 — Reportar consumo de tokens

Invoca `/token-spend <KEY_JIRA> "analisis-spec"`.

Indica la duración del análisis para que se impute a mano en el worklog (en
modo File, en **Tiempo invertido** del Seguimiento del requisito).

El issue **no se mueve**: analizar produce el plan, pero la implementación aún
no ha empezado. Lo mueve a 02.DEVELOPS quien la arranque.

Termina mostrando:

> **Plan generado en `docs/plan/{KEY}.md`.**
> Revísalo y cambia `Estado: pendiente de aprobacion` por `Estado: aprobado`.
> Luego ejecuta: `/implementacion-plan {KEY}`
