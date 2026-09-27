---
name: token-spend
description: |
  Registra el consumo de créditos Copilot asociado a un issue de Jira en un archivo JSON local.
  Lee automáticamente el último turno completado de la sesión activa.
  Parámetros: "<KEY>" "<Skill_Origen>"
  Ejemplo: /token-spend IAFIT-42 implementacion-plan
---

Registra el consumo en `./docs/token-spend/token_spend.json` llamando al script `get-usage.ps1`.

---

## Paso 1 — Parsear los argumentos

De `$ARGUMENTS` extrae:
- **Primer token** → `issue_key` (ej. `IAFIT-42`)
- **Segundo token** → `Skill_Origen` (ej. `implementacion-plan`)

Si falta el `issue_key`, muestra el uso correcto y detente.

---

## Paso 2 — Obtener métricas del último turno

Ejecutar en terminal PowerShell:

```powershell
$usageJson = & ".\.github\skills\token-spend\get-usage.ps1" `
    -SessionLogPath "{{VSCODE_TARGET_SESSION_LOG}}"
$usage = $usageJson | ConvertFrom-Json
```

El script devuelve un objeto JSON con:
- `modelo` — nombre del modelo usado
- `creditos` — créditos Copilot del turno
- `tiempo` — duración del turno (ej. `"67.5s"`)
- `sessionId` / `turnIndex` — para referencia

Si el script falla (`exit 1`), `$usage` queda vacío. En ese caso, antes de continuar,
sustituye los valores por:
- `modelo` → `"no se pudo identificar"`
- `creditos` → `0`
- `tiempo` → `0`

---

## Paso 3 — Leer el archivo existente

Lee el archivo `./docs/token-spend/token_spend.json`.

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
      "modelo": "<usage.modelo>",
      "creditos": <usage.creditos>,
      "tiempo": "<usage.tiempo>"
    }
  ]
}
```

---

## Paso 5 — Actualizar y guardar el JSON

1. Agrega la nueva entrada al arreglo `consumo`.
2. Actualiza `ultimo_actualizado` con la fecha/hora actual en ISO 8601.
3. Escribe el archivo `./docs/token-spend/token_spend.json`.

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
          "modelo": "claude-sonnet-4-6", 
          "creditos": 34.02, 
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
          "modelo": "claude-sonnet-4-6", 
          "creditos": 60.15, 
          "tiempo": "187.8s" 
        }
      ]
    }
  ]
}
```