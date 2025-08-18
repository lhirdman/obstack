# Full-Stack Observability (Docker Compose) — v2
Adds anomaly/delta alerts, rightsizing rules, and dashboards.

## Quick start
1) Create buckets: `docker compose --profile init up mc && docker compose --profile init down`
2) `docker compose up -d`
3) Grafana http://localhost:3000

## Prometheus rules added
- `prometheus/rules.delta-anomaly.yml`
- `prometheus/rules.rightsizing.yml`

Dashboards auto-load under *Starter* folder.
