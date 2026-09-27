---
name: pr-review
description: |
  Revisa un Pull Request de GitHub ya abierto: obtiene el diff con la CLI de gh,
  analiza sólo el código nuevo y emite hallazgos clasificados por severidad
  (BLOQUEANTE, IMPORTANTE, SUGERENCIA, DESTACADO) en docs/pr-review/<número>.md.
  Requiere gh autenticado. Revisa código ya escrito; no lo modifica.
  Parámetros: "<número o URL del PR>" [KEY_JIRA]
  Ejemplo: /pr-review 42 IAFIT-55
argument-hint: "<número o URL del PR> [KEY_JIRA]"
---

Actúa como revisor de código senior. Analiza el PR indicado y produce una
revisión accionable.

`$ARGUMENTS`: primer token = número o URL del PR (de una URL extrae `owner/repo`
y número; de un número suelto usa el repo activo). Segundo token opcional =
`KEY_JIRA`; si se omite, usa `PR{número}` como identificador para los tokens.

---

## Paso 1 — Obtener metadatos y diff del PR

Ejecuta los tres comandos siguientes para recopilar todo el contexto:

```bash
# 1. Metadata del PR
gh pr view <PR> --json number,title,body,baseRefName,headRefName,author,files

# 2. Diff completo (líneas nuevas y de contexto)
gh pr diff <PR>

# 3. Lista de archivos modificados
gh pr view <PR> --json files --jq '.files[].path'
```

Guarda en memoria de sesión:
- Número de PR → `{{PR_NUMBER}}`
- Título del PR → `{{PR_TITLE}}`
- Rama base / rama origen
- Lista de archivos cambiados

---

## Paso 2 — Analizar ÚNICAMENTE el código nuevo

Enfócate **exclusivamente** en:

- Líneas añadidas (comienzan con `+` en el diff)
- Archivos nuevos agregados en este PR
- Archivos de configuración modificados (`.env`, `*.yml`, `*.yaml`, `*.json`, `*.toml`, `*.ini`, `Dockerfile`, `docker-compose.*`, archivos de CI/CD)

**NO revisar:**
- Líneas eliminadas (comienzan con `-`)
- Líneas de contexto sin cambios
- Código que existía antes del PR

---

## Paso 3 — Criterios de evaluación

Para cada archivo modificado, evalúa el código nuevo bajo estos ejes:

### Corrección
- ¿La nueva lógica funciona como se espera?
- ¿Se manejan los casos borde (null, vacío, fuera de rango, errores async)?
- ¿Hay errores de off-by-one, condiciones incorrectas o flujo de control roto?

### Integración con el entorno existente
- ¿El nuevo código rompe o entra en conflicto con interfaces, contratos o APIs existentes?
- ¿Se respetan importaciones, dependencias y límites de módulos?
- ¿Sigue las convenciones de nomenclatura y patrones arquitectónicos del proyecto?
- ¿Las variables de entorno, secretos o valores de configuración son consistentes con el resto del código?

### Archivos de configuración
- ¿Las nuevas claves son consistentes con la estructura de configuración existente?
- ¿Los secretos o valores sensibles están correctamente gestionados (no hardcodeados)?
- ¿Los cambios en CI/CD, Docker o infraestructura mantienen el comportamiento existente del pipeline?
- ¿Las nuevas dependencias están fijadas a versiones seguras?

### Seguridad
- ¿Hay riesgos de inyección (SQL, comandos, XSS)?
- ¿Se exponen datos sensibles en logs o respuestas?
- ¿Hay valores por defecto inseguros o falta validación de entrada?

### Rendimiento
- ¿Hay consultas N+1, llamadas bloqueantes o bucles innecesarios en el nuevo código?

### Legibilidad y mantenibilidad
- ¿El nuevo código es claro y autoexplicativo?
- ¿Falta documentación en lógica compleja?
- ¿Quedó código muerto o artefactos de debug?

---

## Paso 4 — Formato de cada comentario de revisión

Por cada problema encontrado, usa esta estructura:

```
**[SEVERIDAD] — Título corto del problema**

- **Archivo:** `ruta/al/archivo.ext` (línea X o líneas X–Y)
- **Problema:** Descripción clara del problema encontrado en el nuevo código.
- **Sugerencia:** Recomendación concreta o ejemplo de corrección. Solo sobre código nuevo, nunca preexistente.
- **Por qué importa:** Una frase explicando el riesgo o impacto.
```

### Niveles de severidad

| Icono | Nivel | Cuándo usarlo |
|-------|-------|---------------|
| 🔴 | **BLOQUEANTE** | Bug, problema de seguridad, riesgo de pérdida de datos — debe corregirse antes del merge |
| 🟡 | **IMPORTANTE** | Rompe patrones, comportamiento riesgoso, problema de configuración — debería corregirse |
| 🔵 | **SUGERENCIA** | Legibilidad, optimización menor, estilo — sería bueno mejorar |
| ✅ | **DESTACADO** | Algo genuinamente bien hecho — usar con moderación |

---

## Paso 5 — Generar y guardar el documento de revisión

Construye el documento de revisión completo con esta estructura y guárdalo en:

```
docs/pr-review/<PR_NUMBER>.md
```

> Si el directorio `docs/pr-review/` no existe, créalo.

### Estructura del documento

```markdown
# Revisión de PR #<PR_NUMBER> — <PR_TITLE>

**Autor:** <autor>  
**Rama:** `<headRefName>` → `<baseRefName>`  
**Fecha de revisión:** <fecha actual ISO 8601>  
**Archivos revisados:** <n>

---

## Resumen ejecutivo

<2-4 frases describiendo el propósito del PR, la calidad general del código
y la recomendación final: Aprobar / Aprobar con sugerencias / Solicitar cambios>

---

## Comentarios de revisión

<todos los comentarios generados en el Paso 4, uno por problema>

---

## Resumen de hallazgos

| Severidad | Cantidad |
|-----------|----------|
| 🔴 BLOQUEANTE | N |
| 🟡 IMPORTANTE | N |
| 🔵 SUGERENCIA | N |
| ✅ DESTACADO | N |

**Recomendación final:**  
- ✅ **APROBAR** — Sin bloqueantes ni importantes.  
- 🟡 **APROBAR CON SUGERENCIAS** — Solo sugerencias menores pendientes.  
- 🔴 **SOLICITAR CAMBIOS** — Hay issues BLOQUEANTES o IMPORTANTES que deben resolverse antes del merge.
```

---

## Paso 6 — Registro

La revisión **no escribe en Jira ni cierra nada**. Es un dictamen: quien
decide qué hacer con él es la persona que lo lee.

**Sin comentario, sin worklog y sin transición.** El issue sigue en
03.REVISION hasta que alguien mergee el PR y lo mueva a 04.READYFORQA.

---

## Paso 7 — Confirmar al usuario

```
✅ Revisión guardada en `docs/pr-review/<PR_NUMBER>.md`

Resumen: <N> bloqueantes · <N> importantes · <N> sugerencias · <N> destacados
Recomendación: <APROBAR | APROBAR CON SUGERENCIAS | SOLICITAR CAMBIOS>

La recomendación es un dictamen, no una decisión: publicarla, aprobar el PR
y mover el issue lo haces tú.

Para publicar la revisión en el PR (elige una):
  gh pr review <PR_NUMBER> --comment --body "$(cat docs/pr-review/<PR_NUMBER>.md)"
  gh pr review <PR_NUMBER> --request-changes --body "$(cat docs/pr-review/<PR_NUMBER>.md)"
  gh pr review <PR_NUMBER> --approve --body "$(cat docs/pr-review/<PR_NUMBER>.md)"

Si quieres dejar constancia en Jira, pega el veredicto como comentario
en <KEY_JIRA>.
```

No ejecutes ninguno de esos comandos: los muestras para que los lance quien
revisa.

---

## Paso 8 — Reportar consumo de tokens

Si no hubo `KEY_JIRA`, usa `PR{PR_NUMBER}` como identificador.

Invoca `/token-spend {KEY_JIRA:-PR{PR_NUMBER}} "pr-review"`.
