---
name: token-spend
description: |
  Registra el consumo de IA asociado a un issue de Jira en un archivo JSON local,
  anotando qué skill lo originó.
  La invoca cada skill al terminar; rara vez se ejecuta a mano.
  Parámetros: "<KEY>" "<Skill_Origen>"
  Ejemplo: /token-spend IAFIT-42 implementacion-plan
argument-hint: "<KEY | General>" "<Skill_Origen>"
---

Registra el consumo en `./docs/token-spend/token_spend_claude.json`.

---

## Paso 1 — Parsear los argumentos

De `$ARGUMENTS` extrae:
- **Primer token** → `issue_key` (ej. `IAFIT-42`, o `General` si la skill no opera sobre un issue)
- **Segundo token** → `Skill_Origen` (ej. `implementacion-plan`)

Si falta el `issue_key`, muestra el uso correcto y detente.

---

## Paso 2 — Obtener métricas del turno

Las métricas salen del transcript JSONL de la sesión activa de Claude Code, en
`~/.claude/projects/<slug-del-proyecto>/<session-id>.jsonl`. Cada línea de tipo
`assistant` incluye `message.model` y `message.usage`.

Del **último turno completado** (los mensajes `assistant` posteriores al último
mensaje `user` de tipo humano) toma:

| Campo | Origen en `message.usage` |
|---|---|
| `tokens.input` | suma de `input_tokens` |
| `tokens.output` | suma de `output_tokens` |
| `tokens.cache_read` | suma de `cache_read_input_tokens` |
| `tokens.cache_write_5m` | suma de `cache_creation.ephemeral_5m_input_tokens` |
| `tokens.cache_write_1h` | suma de `cache_creation.ephemeral_1h_input_tokens` |
| `modelo` | `message.model` del último mensaje `assistant` |

`tiempo` es la diferencia entre el `timestamp` del primer y el último mensaje
del turno, en segundos con un decimal y sufijo `s` (ej. `"67.5s"`).

Si el transcript no está accesible o no se puede identificar el turno, usa los
valores de respaldo y continúa: `modelo` → `"no se pudo identificar"`, todos los
campos de `tokens` → `0`, `tiempo` → `"0s"`.

---

## Paso 3 — Leer el archivo existente

Lee el archivo `./docs/token-spend/token_spend_claude.json`.

Si no existe, inicialízalo con esta estructura:

```json
{
  "version": "2.0",
  "ultimo_actualizado": "",
  "consumo": []
}
```

---

## Paso 4 — Construir la nueva entrada

```json
{
  "issue": "<issue_key>",
  "fecha": "<fecha y hora ISO 8601 actual>",
  "modelos": [
    {
      "skill": "<Skill_Origen>",
      "modelo": "<modelo>",
      "tokens": {
        "input": <input>,
        "output": <output>,
        "cache_read": <cache_read>,
        "cache_write_5m": <cache_write_5m>,
        "cache_write_1h": <cache_write_1h>
      },
      "tiempo": "<tiempo>"
    }
  ]
}
```

---

## Paso 5 — Actualizar y guardar el JSON

1. Agrega la nueva entrada al arreglo `consumo`.
2. Actualiza `ultimo_actualizado` con la fecha/hora actual en ISO 8601.
3. Escribe el archivo `./docs/token-spend/token_spend_claude.json`.

**Estructura final de referencia:**

```json
{
  "version": "2.0",
  "ultimo_actualizado": "2026-08-31T14:32:00",
  "consumo": [
    {
      "issue": "IAFIT-42",
      "fecha": "2026-08-31T10:15:00",
      "modelos": [
        {
          "skill": "analisis-spec",
          "modelo": "claude-sonnet-5",
          "tokens": {
            "input": 12500,
            "output": 3200,
            "cache_read": 45000,
            "cache_write_5m": 8000,
            "cache_write_1h": 0
          },
          "tiempo": "67.5s"
        }
      ]
    },
    {
      "issue": "IAFIT-42",
      "fecha": "2026-08-31T14:32:00",
      "modelos": [
        {
          "skill": "implementacion-plan",
          "modelo": "claude-sonnet-5",
          "tokens": {
            "input": 38200,
            "output": 9100,
            "cache_read": 120000,
            "cache_write_5m": 15000,
            "cache_write_1h": 0
          },
          "tiempo": "187.8s"
        }
      ]
    }
  ]
}
```
