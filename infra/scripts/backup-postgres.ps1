param(
  [string]$ComposeFile = "docker-compose.yml",
  [string]$OutputDir = "backups",
  [string]$Database = "corplms",
  [string]$User = "lms"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$outputPath = (Resolve-Path $OutputDir).Path
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$out = Join-Path $outputPath "corplms-$stamp.dump"

foreach ($value in @($Database, $User)) {
  if ($value -notmatch '^[A-Za-z_][A-Za-z0-9_]{0,62}$') { throw "Invalid database identifier: $value" }
}

$command = "docker compose -f `"$ComposeFile`" exec -T postgres pg_dump -U $User -d $Database -Fc > `"$out`""
cmd /c $command
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE." }
$backup = Get-Item $out -ErrorAction Stop
if ($backup.Length -eq 0) { throw "Backup file was not created or is empty." }

$manifest = [pscustomobject]@{
  created_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  database = $Database
  backup_name = $backup.Name
  bytes = $backup.Length
  sha256 = (Get-FileHash $out -Algorithm SHA256).Hash.ToLowerInvariant()
}
$manifestPath = "$out.json"
$manifest | ConvertTo-Json | Set-Content -Encoding UTF8 $manifestPath
Write-Output $manifestPath
