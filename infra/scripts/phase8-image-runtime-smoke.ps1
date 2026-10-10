param(
  [string]$ApiImage = "docker-api:latest",
  [string]$WebImage = "docker-web:latest",
  [string]$WorkerImage = "docker-worker:latest"
)

$ErrorActionPreference = "Stop"
$suffix = [guid]::NewGuid().ToString("N").Substring(0, 10)
$apiName = "corplms-image-api-$suffix"
$webName = "corplms-image-web-$suffix"
$startedApi = $false
$startedWeb = $false
try {
  docker run -d --name $apiName --network none --memory 256m --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m `
    -e APP_ENV=production -e DATABASE_URL=postgresql+asyncpg://fixture:unused@127.0.0.1:5432/fixture `
    -e REDIS_URL=redis://127.0.0.1:6379/0 -e WEB_ORIGIN=http://127.0.0.1:3000 `
    -e API_ORIGIN=http://127.0.0.1:8000 -e ALLOWED_HOSTS=127.0.0.1,localhost `
    -e API_DOCS_ENABLED=false -e COOKIE_SECURE=true -e DEV_EMAIL_SINK=false `
    -e INTEGRATION_ALLOW_PRIVATE_URLS=false -e UVICORN_WORKERS=1 $ApiImage | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Candidate API container failed to start." }
  $startedApi = $true
  $apiReady = $false
  for ($attempt = 0; $attempt -lt 20; $attempt++) {
    $ErrorActionPreference = "Continue"
    docker exec $apiName python -c "import urllib.request; assert urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=3).status == 200" 2>$null | Out-Null
    $probeExit = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    if ($probeExit -eq 0) { $apiReady = $true; break }
    Start-Sleep -Seconds 1
  }
  if (-not $apiReady) { throw "Candidate API liveness failed." }
  docker exec $apiName python -c "import httpx; b='http://127.0.0.1:8000'; assert httpx.get(b+'/docs').status_code == 404; assert httpx.get(b+'/api/v1/health/ready').status_code == 503"
  if ($LASTEXITCODE -ne 0) { throw "Candidate API production guards failed." }

  docker run -d --name $webName --network none --memory 256m `
    -e API_ORIGIN=http://127.0.0.1:8000 -e NEXT_PUBLIC_API_ORIGIN=http://127.0.0.1:3000 $WebImage | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Candidate web container failed to start." }
  $startedWeb = $true
  $webReady = $false
  for ($attempt = 0; $attempt -lt 20; $attempt++) {
    $ErrorActionPreference = "Continue"
    docker exec $webName node -e "Promise.all(['/','/login','/dashboard'].map(async p => { const r = await fetch('http://127.0.0.1:3000'+p); if(r.status !== 200) throw Error(p+' '+r.status); })).catch(() => process.exit(1))" 2>$null | Out-Null
    $probeExit = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    if ($probeExit -eq 0) { $webReady = $true; break }
    Start-Sleep -Seconds 1
  }
  if (-not $webReady) { throw "Candidate web routes failed." }
  docker run --rm --network none --memory 256m `
    -e APP_ENV=production -e DATABASE_URL=postgresql+asyncpg://fixture:unused@127.0.0.1:5432/fixture `
    -e REDIS_URL=redis://127.0.0.1:6379/0 -e WEB_ORIGIN=http://127.0.0.1:3000 `
    -e API_ORIGIN=http://127.0.0.1:8000 -e ALLOWED_HOSTS=127.0.0.1,localhost `
    -e API_DOCS_ENABLED=false -e COOKIE_SECURE=true `
    -e DEV_EMAIL_SINK=false -e INTEGRATION_ALLOW_PRIVATE_URLS=false `
    $WorkerImage python -c "import sys; sys.path.insert(0, '/app/worker'); import run; assert callable(run.run_once) and callable(run.process_notification_webhooks) and callable(run.process_scheduled_reports)" | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "Candidate worker jobs are missing from its image." }
  $workerId = docker image inspect $WorkerImage --format "{{.Id}}"
  if ($LASTEXITCODE -ne 0) { throw "Worker image inspection failed." }
  $apiId = docker inspect $apiName --format "{{.Image}}"
  if ($LASTEXITCODE -ne 0) { throw "API image inspection failed." }
  $webId = docker inspect $webName --format "{{.Image}}"
  if ($LASTEXITCODE -ne 0) { throw "Web image inspection failed." }
  [pscustomobject]@{
    api_image = $apiId.Trim()
    web_image = $webId.Trim()
    worker_image = $workerId.Trim()
    worker_jobs_packaged = $true
    api_liveness = 200
    api_readiness_without_dependencies = 503
    api_docs_disabled = 404
    web_routes = "200: /, /login, /dashboard"
    integrated_deployment_certified = $false
  } | ConvertTo-Json -Depth 3
} finally {
  if ($startedWeb) { docker rm -f $webName 2>&1 | Out-Null }
  if ($startedApi) { docker rm -f $apiName 2>&1 | Out-Null }
}
