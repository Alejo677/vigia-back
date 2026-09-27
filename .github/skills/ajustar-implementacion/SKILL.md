---
name: ajustar-implementacion
description: |
  Modifica código ya escrito en la rama activa cuando hay que corregir algo durante
  el desarrollo: mover lógica de capa, arreglar un test o aplicar una convención.
  Requiere estar en la rama feature/{KEY} o fix/{KEY} del issue.
  Nunca toca código mergeado en develop.
  No usar para especificaciones (usa /ajustar-spec) ni para planes de diseño (usa /ajustar-plan).
  Parámetros: "<KEY_JIRA>" "<instrucción del ajuste>"
  Ejemplo: /ajustar-implementacion "PROJ-42" "Mover la validación de fechas al use case"
argument-hint: "<KEY_JIRA>" "<ajuste>"
---

Actúa como Desarrollador Full-Stack Senior. Evalúa el ajuste y aplícalo si es
coherente con la arquitectura, o arguméntalo si no lo es.

**Aplica el cambio mínimo necesario.** No refactorices código no relacionado, no
añadas funcionalidad no pedida ni toques ficheros que el ajuste no exija.

`$ARGUMENTS`: primer token entrecomillado = key del issue; segundo = instrucción.

---

## Paso 0 — Verificar ciclo activo

Comprueba la rama con `git branch --show-current`. Debe coincidir con
`feature/{KEY}` o `fix/{KEY}`. Si no:

> ⛔ La rama activa no corresponde al ciclo de `{KEY}`. Cambia a `feature/{KEY}`
> o `fix/{KEY}` antes de ejecutar este skill.

Lee `CONSTITUCION.md` de la raíz del workspace: ahí están las reglas
arquitectónicas. Resuelve la fuente con `_shared/fuente-especificaciones.md` (Validación) y
detente si no es válida. Verifica el estado y extrae los criterios de aceptación y el
título: en modo Jira con `mcp__jira__jira_get_issue` (`ProyectoJira` es el
`project_key`; criterios = subtareas); en modo File, de la sección `### {KEY}`
del archivo (estado en su Seguimiento; criterios = Escenarios del Gherkin). Los estados salen de
`_shared/estados-jira.md`.

El issue debe estar en **02.DEVELOPS** o **03.REVISION**. Si está en
DEPRECATED, detente; si no ha empezado, advierte que el ciclo de
implementación no ha comenzado.

---

## Paso 1 — Pertinencia

Aplica las reglas arquitectónicas de `CONSTITUCION.md`, más una regla propia de
esta skill:

- **Fuera del ciclo activo**: rechaza si el ajuste toca ficheros ajenos al
  trabajo de esta rama, o si la funcionalidad pertenece a otro issue.

Es válido si corrige un error de implementación, alinea el código con la
arquitectura, mejora un test existente o aplica una convención declarada.

Si no es válido: **no modifiques ningún fichero**, salta al Paso 3.

---

## Paso 2 — Aplicar

Sigue el orden de capas de `CONSTITUCION.md` según lo que toque el
cambio.

Si el ajuste cambia una firma, el flujo de control o el comportamiento
observable, actualiza los tests afectados y ejecuta la suite.
**Criterio: 100% deben pasar.**

---

## Paso 3 — Reportar consumo de tokens

Invoca `/token-spend <KEY_JIRA> "ajustar-implementacion"`.


Si el ajuste llevó tiempo reseñable, indica cuánto para que el desarrollador
lo impute él en el worklog del issue (en modo File, en **Tiempo invertido**
del archivo de especificaciones).

**Si se aplicó:**

```text
✅ Ajuste aplicado

📌 Issue: <KEY_JIRA> — <título>
🌿 Rama: <rama activa>
⚙️ Ficheros:
   - <ruta> — <cambio>
🧪 Pruebas: <N pasadas / N fallidas>
⚠️ Observaciones: [qué cambió, en qué capa y cómo encaja]
```

**Si se rechazó:** mismo formato con `❌ Ajuste rechazado`, indicando la regla
violada, la referencia normativa y una alternativa compatible.
