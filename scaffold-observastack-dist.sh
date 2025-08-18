#!/usr/bin/env bash
set -euo pipefail
ROOT="observastack"
mkdir -p "$ROOT" && cd "$ROOT"

cat > README.md <<'MD'
# observastack (distribution)
Installers, BOM, and configuration overlays for ObservaStack.
MD

mkdir -p release install/compose/kong install/helm/stack/templates install/ansible/playbooks install/ansible/roles/{kong,frontend,bff,grafana,loki,prometheus,tempo,keycloak,opensearch,redpanda}/tasks config/rule-packs/community config/keycloak docs

cat > release/stack.yaml <<'YAML'
version: 0.1.0
profiles:
  core-min:
    images:
      frontend: registry.example.com/observastack/frontend:v0.1.0
      bff: registry.example.com/observastack/bff:v0.1.0
      kong: docker.io/library/kong:3.6
      grafana: grafana/grafana:11.1.0
      loki: grafana/loki:3.0.0
      prometheus: prom/prometheus:v2.53.0
      tempo: grafana/tempo:2.6.0
    optional:
      keycloak: quay.io/keycloak/keycloak:26.0
      opensearch: opensearchproject/opensearch:2.17.0
      redpanda: redpandadata/redpanda:v24.2.3
  pro-default:
    extends: core-min
    enable: [keycloak, opensearch]
    ha: true
YAML

cat > install/compose/.env.example <<'ENV'
# ObservaStack Community (core-min)
OBSERVASTACK_TENANT=default
OBSERVASTACK_EDITION=community
KONG_HTTP=8080
KONG_HTTPS=8443
GRAFANA_PORT=3001
LOKI_RETENTION_DAYS=7
PROM_RETENTION_DAYS=15
TEMPO_RETENTION_DAYS=7
ENV

cat > install/compose/docker-compose.yaml <<'YAML'
version: "3.9"
name: observastack
services:
  kong:
    image: ${KONG_IMAGE:-kong:3.6}
    ports: ["${KONG_HTTP:-8080}:8080", "${KONG_HTTPS:-8443}:8443"]
    environment:
      - KONG_DATABASE=off
    volumes:
      - ./kong/kong.yml:/usr/local/kong/declarative/kong.yml:ro
    depends_on: [bff, frontend, grafana]
  frontend:
    image: ${FRONTEND_IMAGE:-observastack/frontend:dev}
    ports: ["3000:3000"]
  bff:
    image: ${BFF_IMAGE:-observastack/bff:dev}
    environment:
      - EDITION=${OBSERVASTACK_EDITION:-community}
    ports: ["8000:8000"]
  grafana:
    image: ${GRAFANA_IMAGE:-grafana/grafana:11.1.0}
    ports: ["${GRAFANA_PORT:-3001}:3000"]
  loki:
    image: ${LOKI_IMAGE:-grafana/loki:3.0.0}
  prometheus:
    image: ${PROM_IMAGE:-prom/prometheus:v2.53.0}
  tempo:
    image: ${TEMPO_IMAGE:-grafana/tempo:2.6.0}
  minio:
    image: quay.io/minio/minio:RELEASE.2025-01-30T00-00-00Z
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    ports: ["9000:9000", "9001:9001"]
YAML

cat > install/compose/kong/kong.yml <<'YAML'
_format_version: "3.0"
_transform: true
services:
  - name: api
    url: http://bff:8000
    routes:
      - name: api
        paths: ["/api"]
        strip_path: false
  - name: app
    url: http://frontend:3000
    routes:
      - name: app
        paths: ["/app"]
        strip_path: false
  - name: grafana
    url: http://grafana:3000
    routes:
      - name: grafana
        paths: ["/grafana"]
        strip_path: true
plugins:
  - name: cors
    config:
      origins: ["*"]
      methods: ["GET","POST","PUT","DELETE","OPTIONS"]
      headers: ["Authorization","Content-Type"]
YAML

cat > install/helm/stack/Chart.yaml <<'YAML'
apiVersion: v2
name: observastack
description: ObservaStack umbrella chart
type: application
version: 0.1.0
appVersion: "0.1.0"
dependencies:
  - name: loki
    version: 6.6.2
    repository: https://grafana.github.io/helm-charts
    condition: loki.enabled
  - name: tempo
    version: 1.9.0
    repository: https://grafana.github.io/helm-charts
    condition: tempo.enabled
  - name: kube-prometheus-stack
    version: 65.1.0
    repository: https://prometheus-community.github.io/helm-charts
    condition: prometheus.enabled
YAML

cat > install/helm/stack/values.yaml <<'YAML'
frontend:
  image: registry.example.com/observastack/frontend:v0.1.0
bff:
  image: registry.example.com/observastack/bff:v0.1.0
loki: { enabled: true }
tempo: { enabled: true }
prometheus: { enabled: true }
YAML

cat > install/helm/stack/templates/frontend.yaml <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata: { name: observastack-frontend }
spec:
  replicas: 1
  selector: { matchLabels: { app: observastack-frontend } }
  template:
    metadata: { labels: { app: observastack-frontend } }
    spec:
      containers:
        - name: web
          image: {{ .Values.frontend.image }}
          ports: [{ containerPort: 3000 }]
YAML

cat > install/helm/stack/templates/bff.yaml <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata: { name: observastack-bff }
spec:
  replicas: 1
  selector: { matchLabels: { app: observastack-bff } }
  template:
    metadata: { labels: { app: observastack-bff } }
    spec:
      containers:
        - name: bff
          image: {{ .Values.bff.image }}
          ports: [{ containerPort: 8000 }]
YAML

cat > install/ansible/playbooks/install.yml <<'YAML'
- hosts: all
  become: yes
  vars:
    stack_version: "0.1.0"
  roles:
    - role: kong
    - role: frontend
    - role: bff
    - role: grafana
    - role: loki
    - role: prometheus
    - role: tempo
YAML

for r in kong frontend bff grafana loki prometheus tempo keycloak opensearch redpanda; do
cat > install/ansible/roles/$r/tasks/main.yml <<'YAML'
- name: TODO configure component
  debug:
    msg: "configure me"
YAML
done

cat > install/ansible/playbooks/airgap-mirror.yml <<'YAML'
- hosts: localhost
  connection: local
  tasks:
    - name: TODO mirror required container images and charts
      debug: { msg: "Mirror images and charts to offline bundle" }
YAML

cat > config/rule-packs/community/sre-basic.rules.yml <<'YAML'
groups:
  - name: sre-basic
    rules:
      - alert: HighCPUUsage
        expr: sum(rate(container_cpu_usage_seconds_total[5m])) by (instance) > 0.9
        for: 5m
        labels: { severity: high }
        annotations: { summary: "High CPU usage" }
YAML

cat > config/keycloak/realm-observastack.json <<'JSON'
{ "realm": "observastack", "enabled": true, "clients": [ { "clientId": "observastack-frontend", "publicClient": true, "redirectUris": ["*"] } ] }
JSON

cat > .gitlab-ci.yml <<'CI'
stages: [render, package]
render:compose:
  image: alpine:3.20
  stage: render
  script: ["echo render compose placeholder"]
  artifacts: { paths: [install/compose/docker-compose.yaml] }
package:helm:
  image: alpine:3.20
  stage: package
  script: ["echo package helm placeholder"]
  artifacts: { paths: [install/helm/stack] }
CI

cat > bootstrap.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
REPO_URL="${1:-}"
if [[ -z "$REPO_URL" ]]; then echo "Usage: ./bootstrap.sh <git-remote-url>"; exit 1; fi
git init -b master
git add .
git commit -m "chore: initial scaffold (observastack distribution)"
git remote add origin "$REPO_URL"
git push -u origin master
SH
chmod +x bootstrap.sh

echo "✓ observastack (distribution) scaffolded."
