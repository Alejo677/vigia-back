---
name: ajustar-spec
description: |
  Modifica un fichero de especificación Gherkin ya existente en docs/spec/ cuando el
  analista pide añadir un escenario, corregir un criterio o aclarar el alcance.
  Opera sobre el QUÉ funcional, antes de que exista plan técnico.
  No usar para planes de diseño (usa /ajustar-plan) ni para código (usa /ajustar-implementacion).
  Parámetros: "<ruta_del_fichero.md>" "<ajuste solicitado>"
  Ejemplo: /ajustar-spec "docs/spec/IAFIT-42.md" "Añadir escenario de error cuando el token SAS expira"
argument-hint: "<ruta docs/spec/*.md>" "<ajuste>"
---

Actúa como Analista de Requisitos Senior. Evalúa el ajuste solicitado sobre una
especificación existente y aplícalo si es válido, o explica por qué no lo es.

**No implementes el requerimiento.** Solo modificas el documento.

`$ARGUMENTS`: primer token entrecomillado = ruta del fichero; segundo = ajuste solicitado.

---

## Paso 0 — Contexto

Lee el fichero indicado. Si no existe, informa y detente.

Lee `CONSTITUCION.md` para conocer épicas en alcance y restricciones vigentes.

---

## Paso 1 — Viabilidad

Rechaza el ajuste si:

- **Amplía el alcance** más allá de las épicas de `CONSTITUCION.md`, o añade casos
  de uso excluidos explícitamente.
- **Viola una restricción de seguridad** declarada en la constitución.
- **Degrada el Gherkin**: `Dado que` describe acciones en vez de estado,
  `Cuando` con más de una acción, `Entonces` no verificable desde la
  perspectiva del usuario.
- **Contradice** escenarios ya definidos en el mismo fichero o el stack declarado.

Si el ajuste corrige una omisión, añade un caso borde válido o mejora la
redacción sin ampliar alcance, es válido.

---

## Paso 2 — Aplicar

Reescribe **sólo las secciones afectadas**, conservando la estructura:

```markdown
---
feature_id: {feature_id}
epica: {key_epica}
proyecto: {project_key}
fecha: {YYYY-MM-DD}
esfuerzo_implementacion: {esfuerzo}
---
estado: Pendiente de aprobación
---

## Descripción funcional
{prosa con subsecciones ### y listas}

## Criterios de aceptación
{bloque gherkin}
```

Gherkin **en español** (`Escenario`, `Dado que`, `Cuando`, `Entonces`, `Y`,
`Pero`) — nunca en inglés: el equipo lee los criterios en Jira y deben estar
en su idioma. `Dado que` describe estado, `Cuando` es una sola acción,
`Entonces` es verificable desde la perspectiva del usuario. Un escenario, una
línea de título, sin punto final. Cada `Escenario:` será una Subtarea en Jira.

En la descripción funcional: **negrita para el nombre** del campo o elemento,
`(obligatorio)` u `(opcional)` entre paréntesis. Nada de emojis ni detalle de
implementación (rutas, tablas, clases): eso va en el plan técnico.

Si el fichero aún usa el formato antiguo (`## 1. Contexto y Alcance`,
`## 2. Especificación Funcional`, o Gherkin en inglés), **migra la estructura
completa** al formato actual mientras aplicas el ajuste.

`estado:` permanece en `Pendiente de aprobación`. Elimina secciones que no
pertenezcan a la estructura canónica. Sobrescribe el fichero en su ruta.

---

## Paso 3 — Reportar consumo de tokens

Invoca `/token-spend "General" "ajustar-spec"`.

**Si se aplicó:**

```text
✅ Requerimiento ajustado

📌 Épica: <KEY_EPICA> — <nombre>
📂 Fichero: docs/spec/{KEY}.md
📋 Estado: Pendiente de aprobación
⚠️ Cambios: [qué escenarios o secciones se tocaron y por qué son válidos]
```

Muestra debajo los `Escenario:` añadidos o modificados.

**Si se rechazó:** usa el mismo formato con `❌ Ajuste rechazado`, indicando el
motivo, la sección de `CONSTITUCION.md` que aplica y una alternativa viable.
