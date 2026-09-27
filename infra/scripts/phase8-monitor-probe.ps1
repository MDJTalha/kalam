param(
  [string]$GatewayUrl = "http://127.0.0.1:3100",
  [string]$ApiContainer = "docker-api-1",
  [string]$StatePath = (Join-Path $PSScriptRoot "../../qa/phase8-monitor-state.json"),
  [int]$TimeoutSec = 10
)

$ErrorActionPreference = "Stop"
if ($TimeoutSec -lt 1 -or $TimeoutSec -gt 60) { throw "TimeoutSec must be between 1 and 60." }
if ($ApiContainer -notmatch '^[a-zA-Z0-9][a-zA-Z0-9_.-]*$') { throw "Invalid API container name." }
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

$previous = $null
if (Test-Path -LiteralPath $StatePath) {
  $previous = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
  if ($previous.schema_version -ne 1) { throw "Unknown probe state schema; refusing to reset failure history." }
}
$gatewayCount = if ($gatewayOk) { 0 } elseif ($previous -and $previous.gateway_failures) { [int]$previous.gateway_failures + 1 } else { 1 }
$apiCount = if ($apiOk) { 0 } elseif ($previous -and $previous.api_failures) { [int]$previous.api_failures + 1 } else { 1 }
$apiFirst = if ($apiOk) { $null } elseif ($previous -and $previous.api_failures -and $previous.api_first_failed_utc) { [string]$previous.api_first_failed_utc } else { $now.ToString("o") }
$apiElapsed = if ($apiFirst) { ($now - [datetime]::Parse($apiFirst).ToUniversalTime()).TotalMinutes } else { 0 }
$severity = if (-not $gatewayOk -or (-not $apiOk -and $apiElapsed -ge 5)) {
  "critical"
} elseif ($apiCount -ge 2) {
  "warning"
} elseif (-not $apiOk) {
  "observing"
} else {
  "healthy"
}
$state = [pscustomobject]@{
  schema_version = 1
  checked_at_utc = $now.ToString("o")
  gateway_failures = $gatewayCount
  api_failures = $apiCount
  api_first_failed_utc = $apiFirst
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
} | ConvertTo-Json -Depth 3
if ($severity -eq "critical") { exit 2 }
if ($severity -eq "warning") { exit 1 }
exit 0
