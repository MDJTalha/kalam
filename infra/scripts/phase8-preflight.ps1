param(
  [switch]$SkipTests,
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$originalLocation = Get-Location
$temporaryVariables = @("POSTGRES_PASSWORD", "WEB_ORIGIN", "API_ORIGIN", "NEXT_PUBLIC_API_ORIGIN", "ALLOWED_HOSTS", "INTERNAL_API_ORIGIN", "NEXT_DIST_DIR")
$originalVariables = @{}
foreach ($name in $temporaryVariables) {
  $originalVariables[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

function Assert-Exit([string]$Name) {
  if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE." }
  Write-Output "[PASS] $Name"
}

try {
Set-Location $root
docker compose -f docker-compose.yml config --quiet
Assert-Exit "development compose validation"

$env:POSTGRES_PASSWORD = "preflight-validation-only"
$env:WEB_ORIGIN = "https://lms.example.com"
$env:API_ORIGIN = "https://lms.example.com/api"
$env:NEXT_PUBLIC_API_ORIGIN = "https://lms.example.com/api"
$env:ALLOWED_HOSTS = "lms.example.com,api"
$env:INTERNAL_API_ORIGIN = "http://api:8000"
docker compose -f infra/docker/docker-compose.app.yml config --quiet
Assert-Exit "production compose validation"

# The production Compose check above intentionally uses the canonical public
# host. Local TestClient requests use localhost and must not inherit that
# deployment-only allowlist.
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"

Push-Location apps/api
try {
.\.venv\Scripts\python.exe -m alembic current --check-heads
Assert-Exit "alembic current at all heads"
.\.venv\Scripts\python.exe -m ruff check app tests
Assert-Exit "api ruff"
.\.venv\Scripts\python.exe -m mypy app
Assert-Exit "api mypy"
if (-not $SkipTests) {
  .\.venv\Scripts\python.exe -m pytest tests -q
  Assert-Exit "api tests"
}
} finally { Pop-Location }

npm run typecheck:web
Assert-Exit "web typecheck"
npm run lint:web
Assert-Exit "web lint"
if (-not $SkipBuild) {
  $env:NEXT_DIST_DIR = ".next-phase8-preflight"
  npm run build:web
  Assert-Exit "isolated web production build"
}

Write-Output "Phase 8 preflight passed."
} finally {
  foreach ($name in $temporaryVariables) {
    [Environment]::SetEnvironmentVariable($name, $originalVariables[$name], "Process")
  }
  Set-Location $originalLocation
}
