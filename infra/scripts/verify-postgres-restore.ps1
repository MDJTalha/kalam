param(
  [Parameter(Mandatory=$true)][string]$BackupFile,
  [string]$ComposeFile = "docker-compose.yml",
  [string]$SourceDatabase = "corplms",
  [string]$RestoreDatabase = "",
  [string]$User = "lms"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root
$BackupFile = (Resolve-Path $BackupFile -ErrorAction Stop).Path
if (-not $RestoreDatabase) {
  $RestoreDatabase = "corplms_restore_check_" + [guid]::NewGuid().ToString("N").Substring(0, 8)
}
foreach ($value in @($SourceDatabase, $RestoreDatabase, $User)) {
  if ($value -notmatch '^[A-Za-z_][A-Za-z0-9_]{0,62}$') { throw "Invalid database identifier: $value" }
}
if ($RestoreDatabase -eq $SourceDatabase) { throw "Restore database must differ from source." }

function Db-Scalar([string]$Database, [string]$Sql) {
  $value = docker compose -f $ComposeFile exec -T postgres psql -U $User -d $Database -tAc $Sql
  if ($LASTEXITCODE -ne 0) { throw "Database query failed in $Database." }
  return ($value | Out-String).Trim()
}
$exists = Db-Scalar "postgres" "SELECT 1 FROM pg_database WHERE datname = '$RestoreDatabase';"
if ($exists) { throw "Refusing to replace existing database: $RestoreDatabase" }

$created = $false
try {
  docker compose -f $ComposeFile exec -T postgres createdb -U $User $RestoreDatabase
  if ($LASTEXITCODE -ne 0) { throw "Could not create verification database." }
  $created = $true

  $restoreCommand = 'docker compose -f "' + $ComposeFile + '" exec -T postgres pg_restore -U ' + $User + ' -d ' + $RestoreDatabase + ' --no-owner --no-privileges < "' + $BackupFile + '"'
  cmd /c $restoreCommand
  if ($LASTEXITCODE -ne 0) { throw "pg_restore failed with exit code $LASTEXITCODE." }

  $sourceVersion = Db-Scalar $SourceDatabase "SELECT string_agg(version_num, ',' ORDER BY version_num) FROM alembic_version;"
  $restoredVersion = Db-Scalar $RestoreDatabase "SELECT string_agg(version_num, ',' ORDER BY version_num) FROM alembic_version;"
  if (-not $sourceVersion -or $sourceVersion -ne $restoredVersion) {
    throw "Alembic revision mismatch: source=$sourceVersion restored=$restoredVersion"
  }
  foreach ($table in @("tenants", "users", "courses")) {
    $sourceCount = Db-Scalar $SourceDatabase "SELECT count(*) FROM $table;"
    $restoredCount = Db-Scalar $RestoreDatabase "SELECT count(*) FROM $table;"
    if ($sourceCount -ne $restoredCount) {
      throw "Row-count mismatch for $($table): source=$sourceCount restored=$restoredCount"
    }
  }
  Write-Output "Verified revision $restoredVersion and row counts for tenants, users, courses."
}
finally {
  if ($created) {
    docker compose -f $ComposeFile exec -T postgres dropdb -U $User $RestoreDatabase
    if ($LASTEXITCODE -ne 0) { throw "Verification database cleanup failed: $RestoreDatabase" }
  }
}
Write-Output "Restore verification passed; temporary database removed."
