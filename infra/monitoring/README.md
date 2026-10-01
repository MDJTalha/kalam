# Monitoring and release observability

Production release monitoring must cover:
- API liveness: `GET /api/v1/health/live`
- API readiness: `GET /api/v1/health/ready` (PostgreSQL + Redis/Valkey)
- Gateway health: `GET /proxy-health`
- Web availability through the gateway
- Worker process availability and failed-job evidence
- PostgreSQL and Valkey container health
- SMTP, webhook, integration and AI provider delivery/check evidence where configured

Minimum alerting policy:
- readiness unavailable for 2 consecutive checks: warning
- readiness unavailable for 5 minutes: critical
- gateway unavailable: critical
- repeated worker failures or delivery retry exhaustion: warning/critical based on queue impact

Do not mark a deployment production-ready unless health/readiness, logging, backup/restore, rollback and external dependency checks are evidenced.

## Local Compose probe
Run `infra/scripts/phase8-monitor-probe.ps1` periodically on the Docker host. Point
`-GatewayUrl` to the gateway, `-ApiContainer` to the API container and
`-WorkerContainer` to the worker; retain `-StatePath` between runs. It checks
gateway health/homepage, API dependency readiness and the worker's running,
restarting and restart-count state. The restart count is compared only while
the container ID is unchanged. Example for the local stack:

```powershell
& .\infra\scripts\phase8-monitor-probe.ps1 -GatewayUrl http://127.0.0.1:3100 -ApiContainer phase8rc-api-1 -WorkerContainer phase8rc-worker-1 -StatePath C:\Projects\CorpLMS\qa\phase8-monitor-state.json
```

Schedule it once per minute with one non-overlapping runner and preserve the
state file. JSON output includes current health, consecutive failures and severity.
Exit 0 means healthy or the first API/worker failure (`observing`); exit 1
means warning after two consecutive API/worker failures or a new worker restart;
exit 2 means critical for gateway failure or an API/worker failure lasting five
minutes. Wire exit 1/2 and the JSON output into the target environment's alert
transport and verify delivery to the on-call owner. A probe result alone does
not establish external alert delivery, successful worker jobs, queue depth,
TLS or provider monitoring.
