param(
  [Parameter(Mandatory=$true)][string]$ManifestFile
)

$ErrorActionPreference = "Stop"
$manifestPath = (Resolve-Path $ManifestFile -ErrorAction Stop).Path
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
if ($manifest.archive_name -notmatch '^[A-Za-z0-9._-]+\.tar$') {
  throw "Invalid archive name in manifest."
}
$archivePath = Join-Path (Split-Path $manifestPath -Parent) $manifest.archive_name
$archive = Get-Item $archivePath -ErrorAction Stop
if ($archive.Length -ne [int64]$manifest.bytes) { throw "Archive size mismatch." }
$hash = (Get-FileHash $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne [string]$manifest.sha256) { throw "Archive SHA-256 mismatch." }

$entries = @(tar -tf $archivePath)
if ($LASTEXITCODE -ne 0) { throw "Archive listing failed." }
foreach ($entry in $entries) {
  if ($entry.StartsWith("/") -or $entry -match '(^|/)\.\.(/|$)' -or $entry -match '^[A-Za-z]:') {
    throw "Unsafe archive path: $entry"
  }
}
$details = @(tar -tvf $archivePath)
if ($LASTEXITCODE -ne 0) { throw "Archive metadata listing failed." }
foreach ($line in $details) {
  if ($line.Length -gt 0 -and $line[0] -notin @("-", "d")) {
    throw "Archive contains a non-file entry type."
  }
}
$files = @($entries | Where-Object { $_ -ne "." -and $_ -ne "./" -and $_ -notlike "*/" })
if ($files.Count -ne [int]$manifest.file_count) { throw "Manifest file count mismatch." }

$extractDir = Join-Path ([System.IO.Path]::GetTempPath()) ("corplms-uploads-check-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $extractDir | Out-Null
try {
  tar -xf $archivePath -C $extractDir
  if ($LASTEXITCODE -ne 0) { throw "Archive extraction failed." }
  $extracted = @(Get-ChildItem $extractDir -Recurse -File -Force)
  if ($extracted.Count -ne $files.Count) { throw "Extracted file count mismatch." }
  Write-Output "Upload restore verification passed: $($files.Count) files, SHA-256 $hash."
}
finally {
  Remove-Item $extractDir -Recurse -Force
}
