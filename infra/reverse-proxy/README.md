# Reverse proxy

Production ingress is handled by the `gateway` service in `infra/docker/docker-compose.app.yml`.

The supplied Nginx policy:
- exposes only the gateway port;
- keeps Next.js internal to the Compose network;
- forwards host and client forwarding headers;
- disables server tokens;
- limits upload size;
- emits baseline security headers;
- provides `/proxy-health`.

TLS should terminate at the managed load balancer/ingress or at a hardened TLS-enabled proxy in the target environment. Production certificate material must never be committed to the repository.
