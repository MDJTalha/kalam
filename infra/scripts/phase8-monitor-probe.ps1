param(
  [string]$GatewayUrl = "http://127.0.0.1:3100",
  [string]$ApiContainer = "docker-api-1",
  [string]$WorkerContainer = "docker-worker-1",
  [string]$StatePath = (Join-Path $PSScriptRoot "../../qa/phase8-monitor-state.json"),
  [int]$TimeoutSec = 10
)

$ErrorActionPreference = "Stop"
if ($TimeoutSec -lt 1 -or $TimeoutSec -gt 60) { throw "TimeoutSec must be between 1 and 60." }
if ($ApiContainer -notmatch '^[a-zA-Z0-9][a-zA-Z0-9_.-]*$') { throw "Invalid API container name." }
if ($WorkerContainer -notmatch '^[a-zA-Z0-9][a-zA-Z0-9_.-]*$') { throw "Invalid worker container name." }
$now = (Get-Date).ToUniversalTime()
$gatewayOk = $false
$gatewayError = ""
try {
  $base = $GatewayUrl.TrimEnd("/")
  $health = Invoke-WebRequest "$base/proxy-health" -UseBasicParsing -TimeoutSec $TimeoutSec
  $homepage = Invoke-WebRequest "$base/" -UseBasicParsing -TimeoutSec $TimeoutSec
  $gatewayOk = $health.StatusCode -eq 200 -and $homepage.StatusCode -eq 200 -and $homepage.Content -match "<title>"
  if (-not $gatewayOk) { $gatewayError = "Unexpected gateway or homepage response." }
} catch { $gatewayError = $_.Exception.Message }

$apiOk = $false
$apiError = ""
try {
  $raw = docker exec $ApiContainer python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=5).read().decode())" 2>&1
  if ($LASTEXITCODE -ne 0) { throw "API readiness command failed (exit $LASTEXITCODE)." }
  $ready = ($raw | Out-String | ConvertFrom-Json)
  $apiOk = $ready.status -eq "ready" -and $ready.database -eq "ready" -and $ready.redis -eq "ready"
  if (-not $apiOk) { $apiError = "API dependency readiness is not ready." }
} catch { $apiError = $_.Exception.Message }

$workerOk = $false
$workerError = ""
$workerId = $null
$workerRestarts = $null
try {
  $workerState = docker inspect $WorkerContainer --format "{{.State.Running}}|{{.State.Restarting}}|{{.RestartCount}}|{{.Id}}" 2>&1
  if ($LASTEXITCODE -ne 0) { throw "Worker inspection failed (exit $LASTEXITCODE)." }
  $parts = ($workerState | Out-String).Trim().Split("|")
  if ($parts.Count -ne 4 -or $parts[2] -notmatch '^\d+$' -or $parts[3] -notmatch '^[a-f0-9]{64}$') { throw "Unexpected worker state response." }
  $workerRestarts = [int]$parts[2]
  $workerId = $parts[3]
  $workerOk = $parts[0] -eq "true" -and $parts[1] -eq "false"
  if (-not $workerOk) { $workerError = "Worker is not stably running." }
} catch { $workerError = $_.Exception.Message }

$previous = $null
if (Test-Path -LiteralPath $StatePath) {
  $previous = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
  if ($previous.schema_version -notin @(1, 2, 3)) { throw "Unknown probe state schema; refusing to reset failure history." }
}
$workerRestarted = $workerOk -and $previous -and $previous.worker_container_id -eq $workerId -and
  $null -ne $previous.worker_restart_count -and $workerRestarts -gt [int]$previous.worker_restart_count
$gatewayCount = if ($gatewayOk) { 0 } elseif ($previous -and $previous.gateway_failures) { [int]$previous.gateway_failures + 1 } else { 1 }
$apiCount = if ($apiOk) { 0 } elseif ($previous -and $previous.api_failures) { [int]$previous.api_failures + 1 } else { 1 }
$workerCount = if ($workerOk) { 0 } elseif ($previous -and $previous.worker_failures) { [int]$previous.worker_failures + 1 } else { 1 }
$apiFirst = if ($apiOk) { $null } elseif ($previous -and $previous.api_failures -and $previous.api_first_failed_utc) { [string]$previous.api_first_failed_utc } else { $now.ToString("o") }
$workerFirst = if ($workerOk) { $null } elseif ($previous -and $previous.worker_failures -and $previous.worker_first_failed_utc) { [string]$previous.worker_first_failed_utc } else { $now.ToString("o") }
$apiElapsed = if ($apiFirst) { ($now - [datetime]::Parse($apiFirst).ToUniversalTime()).TotalMinutes } else { 0 }
$workerElapsed = if ($workerFirst) { ($now - [datetime]::Parse($workerFirst).ToUniversalTime()).TotalMinutes } else { 0 }
$severity = if (
  -not $gatewayOk -or
  (-not $apiOk -and $apiElapsed -ge 5) -or
  (-not $workerOk -and $workerElapsed -ge 5)
) {
  "critical"
} elseif ($apiCount -ge 2 -or $workerCount -ge 2 -or $workerRestarted) {
  "warning"
} elseif (-not $apiOk -or -not $workerOk) {
  "observing"
} else {
  "healthy"
}
$state = [pscustomobject]@{
  schema_version = 3
  checked_at_utc = $now.ToString("o")
  gateway_failures = $gatewayCount
  api_failures = $apiCount
  api_first_failed_utc = $apiFirst
  worker_failures = $workerCount
  worker_first_failed_utc = $workerFirst
  worker_container_id = $workerId
  worker_restart_count = $workerRestarts
}
$parent = Split-Path -Parent $StatePath
if ($parent -and -not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
$state | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $StatePath -Encoding utf8

[pscustomobject]@{
  checked_at_utc = $now.ToString("o")
  severity = $severity
  gateway_healthy = $gatewayOk
  gateway_failures = $gatewayCount
  gateway_error = $gatewayError
  api_ready = $apiOk
  api_failures = $apiCount
  api_first_failed_utc = $apiFirst
  api_error = $apiError
  worker_running = $workerOk
  worker_restarted = [bool]$workerRestarted
  worker_restart_count = $workerRestarts
  worker_failures = $workerCount
  worker_first_failed_utc = $workerFirst
  worker_error = $workerError
} | ConvertTo-Json -Depth 3
if ($severity -eq "critical") { exit 2 }
if ($severity -eq "warning") { exit 1 }
exit 0
