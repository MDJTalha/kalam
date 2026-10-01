$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $Root

function Step([string]$Name) {
    Write-Host ""
    Write-Host "== $Name ==" -ForegroundColor Cyan
}

function Require-Path([string]$Path) {
    if (-not (Test-Path $Path)) {
        throw "Required Phase 0 artifact missing: $Path"
    }
    Write-Host "PASS  $Path"
}

Step "Phase 0 required artifacts"
$required = @(
    "docs/01-governance/PROJECT_MASTER_PLAN.md",
    "docs/02-product/REQUIREMENTS_BASELINE.md",
    "docs/02-product/REQUIREMENTS_TRACEABILITY_MATRIX.md",
    "docs/02-product/DOMAIN_MODEL.md",
    "docs/03-architecture/ARCHITECTURE_AND_TECHNICAL_PLAN.md",
    "docs/03-architecture/ARCHITECTURE_DIAGRAMS.md",
    "docs/04-security-compliance/SECURITY_COMPLIANCE_BASELINE.md",
    "docs/05-quality/QA_TEST_STRATEGY.md",
    "docs/05-quality/CI_BASELINE.md",
    "docs/06-delivery/ENVIRONMENT_MATRIX.md",
    "docs/07-decisions/ADR_INDEX.md",
    ".github/workflows/ci.yml",
    ".env.example",
    ".env.platform.example",
    "apps/api/.env.example",
    "apps",
    "packages",
    "database",
    "infra",
    "tests"
)
$required | ForEach-Object { Require-Path $_ }

$adrCount = @(Get-ChildItem "docs/07-decisions" -Filter "ADR-*.md").Count
if ($adrCount -lt 13) { throw "Expected at least 13 Phase 0 ADR records; found $adrCount." }
Write-Host "PASS  $adrCount ADR records present"

Step "Canonical environment contract"
$rootEnv = Get-Content ".env.example" -Raw
$apiEnv = Get-Content "apps/api/.env.example" -Raw
$matrix = Get-Content "docs/06-delivery/ENVIRONMENT_MATRIX.md" -Raw
$checks = @(
    @{ Name="web origin"; Value="http://127.0.0.1:3000" },
    @{ Name="api origin"; Value="http://127.0.0.1:8000" },
    @{ Name="postgres host port"; Value="55434" },
    @{ Name="valkey host port"; Value="56379" },
    @{ Name="clamav host port"; Value="55000" }
)
foreach ($check in $checks) {
    if ($rootEnv -notmatch [regex]::Escape($check.Value) -and
        $apiEnv -notmatch [regex]::Escape($check.Value) -and
        $matrix -notmatch [regex]::Escape($check.Value)) {
        throw "Canonical $($check.Name) missing from Phase 0 environment sources: $($check.Value)"
    }
    Write-Host "PASS  $($check.Name) = $($check.Value)"
}

if ($apiEnv -match "REDI_URL|SESSION_TTL_SECOND3") {
    throw "Deprecated Phase 0 environment typo remains in apps/api/.env.example"
}
Write-Host "PASS  environment variable names normalized"

Step "Compose configuration"
docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw "docker compose config failed" }
Write-Host "PASS  docker-compose.yml parses"

docker compose up -d postgres valkey clamav
if ($LASTEXITCODE -ne 0) { throw "Phase 0 dependency startup failed" }

$postgresReady = $false
$clamavReady = $false
for ($i = 0; $i -lt 60; $i++) {
    $postgresHealth = docker inspect corplms-postgres --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}running{{end}}' 2>$null
    $clamavHealth = docker inspect corplms-clamav --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}unknown{{end}}' 2>$null
    if ($postgresHealth -eq "healthy") { $postgresReady = $true }
    if ($clamavHealth -eq "healthy") { $clamavReady = $true }
    if ($postgresReady -and $clamavReady) { break }
    Start-Sleep -Seconds 5
}
if (-not $postgresReady) { throw "PostgreSQL did not become healthy" }
if (-not $clamavReady) { throw "ClamAV did not become healthy" }
$valkeyPong = docker exec corplms-valkey valkey-cli ping
if ($valkeyPong -ne "PONG") { throw "Valkey readiness check failed" }
Write-Host "PASS  PostgreSQL, Valkey and ClamAV are ready"

Step "API foundation"
$Python = "apps/api/.venv/Scripts/python.exe"
if (-not (Test-Path $Python)) { throw "API virtual environment missing: $Python" }

Push-Location "apps/api"
try {
    & ".venv/Scripts/python.exe" "scripts/check_migration_head.py"
    if ($LASTEXITCODE -ne 0) { throw "Alembic head verification failed" }

    & ".venv/Scripts/python.exe" -m ruff check app tests
    if ($LASTEXITCODE -ne 0) { throw "Ruff failed" }

    & ".venv/Scripts/python.exe" -m mypy app
    if ($LASTEXITCODE -ne 0) { throw "mypy failed" }

    & ".venv/Scripts/python.exe" -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "API pytest failed" }
}
finally {
    Pop-Location
}

Step "Web foundation"
npm --workspace apps/web run typecheck
if ($LASTEXITCODE -ne 0) { throw "Web TypeScript failed" }
npm --workspace apps/web run lint
if ($LASTEXITCODE -ne 0) { throw "Web ESLint failed" }

npm --workspace apps/web run build
if ($LASTEXITCODE -ne 0) { throw "Web production build failed" }

Step "Repository state"
$branch = git branch --show-current
$status = @(git status --porcelain=v1)
$remotes = @(git remote -v)
Write-Host "Branch: $branch"
Write-Host "Working-tree entries: $($status.Count)"
if ($remotes.Count -eq 0) {
    Write-Warning "No Git remote configured. Hosted CI evidence remains an external closure dependency."
} else {
    Write-Host "PASS  Git remote configured"
}

Write-Host ""
Write-Host "PHASE 0 LOCAL FOUNDATION VALIDATION: PASS" -ForegroundColor Green
Write-Host "Hosted CI is authoritative only when a remote repository and successful workflow run are recorded."
