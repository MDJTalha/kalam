param(
  [Parameter(Mandatory=$true)][string]$ManifestFile
)

$ErrorActionPreference = "Stop"
$manifestPath = (Resolve-Path $ManifestFile -ErrorAction Stop).Path
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
if ($manifest.backup_name -notmatch '^[A-Za-z0-9._-]+\.dump$') {
  throw "Invalid backup name in manifest."
}
$backupPath = Join-Path (Split-Path $manifestPath -Parent) $manifest.backup_name
$backup = Get-Item $backupPath -ErrorAction Stop
if ($backup.Length -ne [int64]$manifest.bytes) { throw "Backup size mismatch." }
$hash = (Get-FileHash $backupPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne [string]$manifest.sha256) { throw "Backup SHA-256 mismatch." }

$format = & docker run --rm --mount "type=bind,src=$backupPath,dst=/backup.dump,readonly" postgres:18.6-alpine pg_restore -l /backup.dump
if ($LASTEXITCODE -ne 0) { throw "pg_restore catalog inspection failed." }
if (-not ($format | Select-String -Pattern 'TABLE DATA.*tenants')) {
  throw "Backup catalog does not contain tenant table data."
}
Write-Output "PostgreSQL backup verification passed: $($backup.Name), SHA-256 $hash."
