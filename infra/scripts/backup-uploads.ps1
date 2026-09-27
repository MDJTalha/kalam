param(
  [Parameter(Mandatory=$true)][string]$VolumeName,
  [string]$OutputDir = "backups\uploads",
  [string]$ArchiveImage = "postgres:18.6-alpine"
)

$ErrorActionPreference = "Stop"
if ($VolumeName -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$') {
  throw "Invalid volume name."
}
$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $root
docker volume inspect $VolumeName --format "{{.Name}}" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Upload volume not found: $VolumeName" }

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$outputPath = (Resolve-Path $OutputDir).Path
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd-HHmmss")
$suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
$archiveName = "corplms-uploads-$stamp-$suffix.tar"
$archivePath = Join-Path $outputPath $archiveName
docker run --rm --mount "type=volume,src=$VolumeName,dst=/source,readonly" --mount "type=bind,src=$outputPath,dst=/archive" --entrypoint tar $ArchiveImage -C /source -cf "/archive/$archiveName" .
if ($LASTEXITCODE -ne 0) { throw "Upload archive creation failed." }
$archive = Get-Item $archivePath -ErrorAction Stop
if ($archive.Length -le 0) { throw "Upload archive is empty." }
$entries = @(tar -tf $archivePath)
if ($LASTEXITCODE -ne 0) { throw "Upload archive cannot be listed." }
$files = @($entries | Where-Object { $_ -ne "." -and $_ -ne "./" -and $_ -notlike "*/" })
$manifest = [pscustomobject]@{
  created_at_utc = (Get-Date).ToUniversalTime().ToString("o")
  volume_name = $VolumeName
  archive_name = $archiveName
  bytes = $archive.Length
  sha256 = (Get-FileHash $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
  file_count = $files.Count
}
$manifestPath = "$archivePath.json"
$manifest | ConvertTo-Json | Set-Content -Encoding UTF8 $manifestPath
Write-Output $manifestPath
