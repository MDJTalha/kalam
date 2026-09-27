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
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$out = Join-Path $OutputDir "corplms-$stamp.dump"

$command = "docker compose -f `"$ComposeFile`" exec -T postgres pg_dump -U $User -d $Database -Fc > `"$out`""
cmd /c $command
if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE." }
if (-not (Test-Path $out) -or (Get-Item $out).Length -eq 0) { throw "Backup file was not created or is empty." }
Write-Output $out
