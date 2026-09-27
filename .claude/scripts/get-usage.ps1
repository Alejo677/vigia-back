# get-usage.ps1
# Lee el ultimo turno completado de la sesion activa de Claude Code y devuelve
# un JSON con tokens (desglosados), tiempo y modelo.
# Uso normal (sin parametros): .\get-usage.ps1
# Uso con fixture de prueba:    .\get-usage.ps1 -TranscriptPath "<ruta.jsonl>"

param(
    [string]$TranscriptPath
)

function Resolve-ActiveTranscript {
    $cwd = (Get-Location).Path.TrimEnd('\', '/')
    $mangled = $cwd -replace '[:\\/.]', '-'
    $projectsRoot = Join-Path $env:USERPROFILE ".claude\projects"
    $projectDir = Join-Path $projectsRoot $mangled

    if (-not (Test-Path $projectDir)) {
        $match = Get-ChildItem -Path $projectsRoot -Directory -ErrorAction SilentlyContinue |
                 Where-Object { $_.Name -ieq $mangled } |
                 Select-Object -First 1
        if ($match) { $projectDir = $match.FullName }
    }

    if (-not (Test-Path $projectDir)) {
        Write-Error "No se encontro la carpeta de proyecto de Claude Code: $projectDir"
        exit 1
    }

    if ($env:CLAUDE_CODE_SESSION_ID) {
        $primary = Join-Path $projectDir "$($env:CLAUDE_CODE_SESSION_ID).jsonl"
        if (Test-Path $primary) { return $primary }
    }

    $fallback = Get-ChildItem -Path $projectDir -File -Filter '*.jsonl' -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1

    if (-not $fallback) {
        Write-Error "No se encontraron transcripts de sesion en: $projectDir"
        exit 1
    }

    return $fallback.FullName
}

if (-not $TranscriptPath) {
    $TranscriptPath = Resolve-ActiveTranscript
}

if (-not (Test-Path $TranscriptPath)) {
    Write-Error "No se encontro el archivo de sesion: $TranscriptPath"
    exit 1
}

$sessionId = [System.IO.Path]::GetFileNameWithoutExtension($TranscriptPath)

# Cada turno agrupa: limite de usuario genuino + todos los registros hasta el
# proximo limite genuino (los "user" con toolUseResult/sourceToolAssistantUUID
# son ecos sinteticos de tool_result, no abren turno nuevo).
$turns = New-Object System.Collections.Generic.List[object]
$current = $null

foreach ($line in [System.IO.File]::ReadLines($TranscriptPath)) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }

    try {
        $ev = $line | ConvertFrom-Json -ErrorAction Stop
    } catch {
        continue
    }

    if ($ev.type -eq "user") {
        $isSyntheticToolEcho = ($null -ne $ev.toolUseResult) -or ($null -ne $ev.sourceToolAssistantUUID)
        if (-not $isSyntheticToolEcho) {
            $current = [PSCustomObject]@{
                startTimestamp = $ev.timestamp
                lastTimestamp  = $ev.timestamp
                modelo         = $null
                lastStopReason = $null
                hasAssistant   = $false
                input          = 0
                output         = 0
                cacheRead      = 0
                cacheWrite5m   = 0
                cacheWrite1h   = 0
            }
            $turns.Add($current)
            continue
        }
    }

    if (-not $current) { continue }

    if ($ev.timestamp) { $current.lastTimestamp = $ev.timestamp }

    if ($ev.type -eq "assistant" -and $ev.message.usage) {
        $usage = $ev.message.usage
        $current.hasAssistant = $true
        $current.modelo = $ev.message.model
        $current.lastStopReason = $ev.message.stop_reason

        $current.input += [int]($usage.input_tokens)
        $current.output += [int]($usage.output_tokens)
        $current.cacheRead += [int]($usage.cache_read_input_tokens)

        if ($usage.cache_creation) {
            $current.cacheWrite5m += [int]($usage.cache_creation.ephemeral_5m_input_tokens)
            $current.cacheWrite1h += [int]($usage.cache_creation.ephemeral_1h_input_tokens)
        } elseif ($usage.cache_creation_input_tokens) {
            $current.cacheWrite5m += [int]($usage.cache_creation_input_tokens)
        }
    }
}

# El ultimo turno puede estar "en vuelo" (sin respuesta aun, o a mitad de un
# ciclo de tool_use) - descartarlo evita reportar datos de un turno incompleto.
$target = $null
$turnIndex = 0
for ($i = $turns.Count - 1; $i -ge 0; $i--) {
    $turnIndex = $i + 1
    $t = $turns[$i]
    if ($t.hasAssistant -and $t.lastStopReason -eq "end_turn") {
        $target = $t
        break
    }
}

if (-not $target) {
    Write-Error "No se encontraron turnos completados en la sesion."
    exit 1
}

$modelo = if ($target.modelo) { $target.modelo } else { "desconocido" }

$elapsedSeconds = 0
try {
    $start = [datetime]$target.startTimestamp
    $end = [datetime]$target.lastTimestamp
    $elapsedSeconds = [math]::Round(($end - $start).TotalSeconds, 1)
} catch {
    $elapsedSeconds = 0
}

[PSCustomObject]@{
    sessionId = $sessionId
    turnIndex = $turnIndex
    modelo    = $modelo
    tokens    = [PSCustomObject]@{
        input          = $target.input
        output         = $target.output
        cache_read     = $target.cacheRead
        cache_write_5m = $target.cacheWrite5m
        cache_write_1h = $target.cacheWrite1h
    }
    tiempo    = "$($elapsedSeconds)s"
} | ConvertTo-Json -Compress
