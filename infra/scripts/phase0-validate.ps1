param(
    [switch]$RunDatabaseTests,
    [string]$IsolatedDatabaseUrl
)

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

if ($RunDatabaseTests) {
    if (-not $IsolatedDatabaseUrl) {
        throw "Database tests require -IsolatedDatabaseUrl pointing to a separately provisioned disposable test database."
    }
    $normalizedTestUrl = $IsolatedDatabaseUrl -replace '^postgresql\+asyncpg:', 'postgresql:'
    try { $testUri = [uri]$normalizedTestUrl } catch { throw "The isolated database URL is invalid." }
    $testDbName = $testUri.AbsolutePath.TrimStart('/')
    if ($testDbName -notmatch '^corplms_test_[a-z0-9_]+$' -or
        $testUri.Host -notin @('localhost', '127.0.0.1', '::1', 'kalam-test-postgres') -or
        $testUri.Port -eq 55434) {
        throw "Refusing database tests: target must be a disposable corplms_test_* database on an isolated test endpoint, never the canonical host port 55434."
    }
}
else {
    Write-Warning "Skipping database-connected checks. Use -RunDatabaseTests with a verified isolated corplms_test_* database. No Docker services will be started by this script."
}

Step "API foundation"
$Python = "apps/api/.venv/Scripts/python.exe"
if (-not (Test-Path $Python)) { throw "API virtual environment missing: $Python" }

Push-Location "apps/api"
try {
    & ".venv/Scripts/python.exe" -m ruff check app tests
    if ($LASTEXITCODE -ne 0) { throw "Ruff failed" }

    & ".venv/Scripts/python.exe" -m mypy app
    if ($LASTEXITCODE -ne 0) { throw "mypy failed" }

    if ($RunDatabaseTests) {
        if (-not $env:CI_FIXTURE_PASSWORD) {
            throw "Database tests require CI_FIXTURE_PASSWORD matching the isolated test fixtures."
        }
        $previousDatabaseUrl = $env:DATABASE_URL
        $previousTestDatabaseUrl = $env:KALAM_TEST_DATABASE_URL
        try {
            $env:DATABASE_URL = $IsolatedDatabaseUrl
            $env:KALAM_TEST_DATABASE_URL = $IsolatedDatabaseUrl
            & ".venv/Scripts/python.exe" "scripts/check_migration_head.py"
            if ($LASTEXITCODE -ne 0) { throw "Alembic head verification failed on isolated test database" }
            & ".venv/Scripts/python.exe" -m pytest -q
            if ($LASTEXITCODE -ne 0) { throw "API pytest failed on isolated test database" }
        }
        finally {
            if ($null -eq $previousDatabaseUrl) {
                Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
            }
            else {
                $env:DATABASE_URL = $previousDatabaseUrl
            }
            if ($null -eq $previousTestDatabaseUrl) {
                Remove-Item Env:KALAM_TEST_DATABASE_URL -ErrorAction SilentlyContinue
            }
            else {
                $env:KALAM_TEST_DATABASE_URL = $previousTestDatabaseUrl
            }
        }
    }
}
finally {
    Pop-Location
}

Step "Web foundation"
npm --workspace apps/web run typecheck
if ($LASTEXITCODE -ne 0) { throw "Web TypeScript failed" }
npm --workspace apps/web run lint
if ($LASTEXITCODE -ne 0) { throw "Web ESLint failed" }

$previousNextDistDir = $env:NEXT_DIST_DIR
try {
    # Keep production output isolated from a running local development server.
    $env:NEXT_DIST_DIR = ".next-phase8-final"
    npm --workspace apps/web run build
    if ($LASTEXITCODE -ne 0) { throw "Web production build failed" }
}
finally {
    if ($null -eq $previousNextDistDir) {
        Remove-Item Env:NEXT_DIST_DIR -ErrorAction SilentlyContinue
    }
    else {
        $env:NEXT_DIST_DIR = $previousNextDistDir
    }
}

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
