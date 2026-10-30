param(
  [switch]$SkipTests,
  [switch]$SkipBuild,
  [switch]$RequireCleanTree
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$originalLocation = Get-Location
$temporaryVariables = @("POSTGRES_PASSWORD", "WEB_ORIGIN", "API_ORIGIN", "NEXT_PUBLIC_API_ORIGIN", "NEXT_PUBLIC_SITE_URL", "ALLOWED_HOSTS", "INTERNAL_API_ORIGIN", "OUTBOUND_HTTP_PROXY", "NEXT_DIST_DIR", "DATABASE_URL", "APP_ENV", "SAAS_OPS_TENANT_SLUG")
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
if ($RequireCleanTree) {
  $changes = @(git status --porcelain --untracked-files=all)
  Assert-Exit "git status"
  if ($changes.Count -gt 0) { throw "Release candidate working tree is not clean; commit and review its contents before certification." }
  Write-Output "[PASS] clean release-candidate tree"
}
docker compose -f docker-compose.yml config --quiet
Assert-Exit "development compose validation"

$env:POSTGRES_PASSWORD = "preflight-validation-only"
$env:WEB_ORIGIN = "https://lms.example.com"
$env:API_ORIGIN = "https://lms.example.com/api"
$env:NEXT_PUBLIC_API_ORIGIN = "https://lms.example.com/api"
$env:NEXT_PUBLIC_SITE_URL = "https://lms.example.com"
$env:ALLOWED_HOSTS = "lms.example.com,api"
$env:INTERNAL_API_ORIGIN = "http://api:8000"
# Validation-only placeholder: this is never a usable production proxy.
$env:OUTBOUND_HTTP_PROXY = "http://egress-proxy.example.invalid:3128"
docker compose -f infra/docker/docker-compose.app.yml config --quiet
Assert-Exit "production compose validation"

# The production Compose check above uses deployment-only placeholder values.
# Restore their caller-provided values before importing application settings or
# running tests; in particular, the fake outbound proxy must never intercept
# requests to local integration-test servers.
foreach ($name in @("POSTGRES_PASSWORD", "WEB_ORIGIN", "API_ORIGIN", "NEXT_PUBLIC_API_ORIGIN", "NEXT_PUBLIC_SITE_URL", "INTERNAL_API_ORIGIN", "OUTBOUND_HTTP_PROXY")) {
  [Environment]::SetEnvironmentVariable($name, $originalVariables[$name], "Process")
}
# Local TestClient requests use localhost and must not inherit a deployment-only allowlist.
$env:ALLOWED_HOSTS = "localhost,127.0.0.1"

if (-not $env:KALAM_TEST_DATABASE_URL -or $env:KALAM_TEST_DATABASE_URL -notmatch "^postgresql(\+asyncpg)?://") {
  throw "Set KALAM_TEST_DATABASE_URL to a dedicated isolated PostgreSQL test database. Release preflight will not fall back to a developer or SQLite database."
}
$testDatabaseUri = [System.Uri]::new($env:KALAM_TEST_DATABASE_URL)
if (-not $testDatabaseUri.IsLoopback) {
  throw "KALAM_TEST_DATABASE_URL must point to a loopback PostgreSQL host. Remote/shared databases are not accepted by local release preflight."
}
$env:DATABASE_URL = $env:KALAM_TEST_DATABASE_URL
$env:APP_ENV = "ci"
$env:SAAS_OPS_TENANT_SLUG = "kalam"

Push-Location apps/api
try {
.\.venv\Scripts\python.exe scripts\check_migration_head.py
Assert-Exit "alembic current at all heads"
.\.venv\Scripts\python.exe -m ruff check app tests
Assert-Exit "api ruff"
.\.venv\Scripts\python.exe -m mypy app
Assert-Exit "api mypy"
if (-not $SkipTests) {
  .\.venv\Scripts\python.exe scripts\bootstrap_saas_ops.py
  Assert-Exit "isolated SaaS operations test fixtures"
  .\.venv\Scripts\python.exe scripts\seed_ci_fixtures.py
  Assert-Exit "deterministic tenant and role fixtures"
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
