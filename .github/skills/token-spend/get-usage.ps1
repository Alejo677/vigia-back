# get-usage.ps1
# Lee el último turno completado de la sesión activa de VS Code chat y devuelve un JSON con créditos, tiempo y modelo.
# Uso: .\get-usage.ps1 -SessionLogPath "<VSCODE_TARGET_SESSION_LOG>"

param(
    [Parameter(Mandatory=$true)]
    [string]$SessionLogPath
)

$sessionId = [System.IO.Path]::GetFileNameWithoutExtension($SessionLogPath)
$wsStorage = Split-Path (Split-Path (Split-Path $SessionLogPath -Parent) -Parent) -Parent
$chatFile  = Join-Path $wsStorage "chatSessions\$sessionId.jsonl"

if (-not (Test-Path $chatFile)) {
    Write-Error "No se encontró el archivo de sesión: $chatFile"
    exit 1
}

$events   = [System.IO.File]::ReadAllLines($chatFile) | ForEach-Object { $_ | ConvertFrom-Json }
$turnData = @{}
$lastModel = ""

foreach ($ev in $events) {
    if ($ev.k -and $ev.k.Count -eq 1 -and $ev.k[0] -eq "requests" -and $ev.v -is [array] -and $ev.v.Count -gt 0) {
        $req = $ev.v[$ev.v.Count - 1]
        if ($req.model) { $lastModel = $req.model }
        continue
    }

    if (-not ($ev.k -and $ev.k.Count -ge 2 -and $ev.k[0] -eq "requests")) { continue }

    $ti = [string]$ev.k[1]
    if (-not $turnData[$ti]) {
        $turnData[$ti] = @{ credits = 0; creditsSet = $false; elapsed = $null; modelo = $lastModel }
    }

    $field = if ($ev.k.Count -ge 3) { $ev.k[2] } else { $null }
    switch ($field) {
        "copilotCredits" { $turnData[$ti].credits = $ev.v; $turnData[$ti].creditsSet = $true }
        "elapsedMs"      { $turnData[$ti].elapsed = $ev.v }
    }
}

# Turno en vuelo: tiene elapsed pero copilotCredits aun no llego; descartarlo evita reportar creditos:0 falsos
$last = $turnData.GetEnumerator() |
        Where-Object { $_.Value.elapsed -ne $null -and $_.Value.creditsSet } |
        Sort-Object { [int]$_.Key } -Descending |
        Select-Object -First 1

if (-not $last) {
    Write-Error "No se encontraron turnos completados en la sesión."
    exit 1
}

$modelo = if ($last.Value.modelo) { $last.Value.modelo } else { "desconocido" }

[PSCustomObject]@{
    sessionId = $sessionId
    turnIndex = $last.Key
    modelo    = $modelo
    creditos  = [math]::Round($last.Value.credits, 4)
    tiempo    = "$([math]::Round($last.Value.elapsed / 1000, 1))s"
} | ConvertTo-Json -Compress
