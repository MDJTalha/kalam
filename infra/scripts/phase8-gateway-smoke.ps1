param(
  [string]$GatewayUrl = "http://127.0.0.1:3100",
  [string]$ApiContainer = "docker-api-1",
  [string]$WorkerContainer = "docker-worker-1",
  [string]$MigrateContainer = "docker-migrate-1",
  [string]$ExpectedApiImage = "",
  [string]$ExpectedWebImage = "",
  [string]$ExpectedWorkerImage = ""
)

$ErrorActionPreference = "Stop"
$base = $GatewayUrl.TrimEnd("/")
$health = Invoke-WebRequest "$base/proxy-health" -UseBasicParsing -TimeoutSec 10
if ($health.StatusCode -ne 200) { throw "Gateway health failed: $($health.StatusCode)" }
$webResponse = Invoke-WebRequest "$base/" -UseBasicParsing -TimeoutSec 15
if ($webResponse.StatusCode -ne 200 -or $webResponse.Content -notmatch "<title>") {
  throw "Web homepage failed."
}

$expectedHeaders = @{
  "X-Content-Type-Options" = "nosniff"
  "X-Frame-Options" = "DENY"
  "Referrer-Policy" = "strict-origin-when-cross-origin"
  "Permissions-Policy" = "camera=()"
}
foreach ($name in $expectedHeaders.Keys) {
  $value = [string]$webResponse.Headers[$name]
  if ($value -notlike "*$($expectedHeaders[$name])*") {
    throw "Missing or incorrect gateway header: $name"
  }
}
$apiHealth = docker exec $ApiContainer python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=5).read().decode())"
if ($LASTEXITCODE -ne 0) { throw "API readiness request failed." }
$ready = ($apiHealth | Out-String | ConvertFrom-Json)
if ($ready.status -ne "ready" -or $ready.database -ne "ready" -or $ready.redis -ne "ready") {
  throw "API dependencies are not ready."
}
$migrationExit = docker inspect $MigrateContainer --format "{{.State.ExitCode}}"
if ($LASTEXITCODE -ne 0 -or $migrationExit.Trim() -ne "0") {
  throw "Migration service did not exit successfully."
}
$apiImage = docker inspect $ApiContainer --format "{{.Image}}"
$webContainer = $ApiContainer -replace "-api-", "-web-"
$webImage = docker inspect $webContainer --format "{{.Image}}"
if ($LASTEXITCODE -ne 0) { throw "Could not inspect web image." }
$workerRunning = docker inspect $WorkerContainer --format "{{.State.Running}}"
if ($LASTEXITCODE -ne 0 -or $workerRunning.Trim() -ne "true") { throw "Worker container is not running." }
$workerImage = docker inspect $WorkerContainer --format "{{.Image}}"
if ($LASTEXITCODE -ne 0) { throw "Could not inspect worker image." }
if ($ExpectedApiImage -and $apiImage.Trim() -ne $ExpectedApiImage) { throw "API image differs from the release candidate." }
if ($ExpectedWebImage -and $webImage.Trim() -ne $ExpectedWebImage) { throw "Web image differs from the release candidate." }
if ($ExpectedWorkerImage -and $workerImage.Trim() -ne $ExpectedWorkerImage) { throw "Worker image differs from the release candidate." }
[pscustomobject]@{
  checked_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  gateway_url = $base
  gateway_health = $health.StatusCode
  web_status = $webResponse.StatusCode
  security_headers = "pass"
  api_readiness = "ready"
  database = $ready.database
  redis = $ready.redis
  migration_exit = [int]$migrationExit
  api_image = $apiImage
  web_image = $webImage
  worker_running = $true
  worker_image = $workerImage
} | ConvertTo-Json -Depth 3
