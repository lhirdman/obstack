# Docker Compose Deployment

Docker Compose provides the fastest way to get ObservaStack running for development, testing, and small production deployments.

## Overview

The Docker Compose setup includes:

- **ObservaStack Application** (Frontend + BFF)
- **Observability Stack** (Prometheus, Loki, Tempo, Grafana)
- **Supporting Services** (Keycloak, Redis, MinIO)
- **Data Collection** (Vector, OpenTelemetry Collector)

## Prerequisites

### System Requirements

- **Docker**: Version 20.10+ 
- **Docker Compose**: Version 2.0+
- **Memory**: 8GB+ RAM (16GB recommended)
- **Storage**: 20GB+ available disk space
- **CPU**: 4+ cores recommended

### Verify Installation

```bash
# Check Docker version
docker --version
# Output: Docker version 20.10.0 or higher

# Check Docker Compose version  
docker compose version
# Output: Docker Compose version v2.0.0 or higher

# Verify Docker daemon is running
docker info
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/observastack/observastack.git
cd observastack/docker
```

### 2. Initialize Storage

```bash
# Initialize MinIO buckets (first time only)
docker compose --profile init up mc && docker compose --profile init down
```

### 3. Start Services

```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps
```

### 4. Access Applications

| Service | URL | Credentials |
|---------|-----|-------------|
| **ObservaStack** | http://localhost:3000 | admin/admin |
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9090 | - |
| **Keycloak** | http://localhost:8080 | admin/admin |

## Configuration

### Environment Variables

Create `.env` file in the docker directory:

```bash
# ObservaStack Configuration
OBSERVASTACK_VERSION=latest
OBSERVASTACK_ENV=development
OBSERVASTACK_DEBUG=true

# Authentication
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin
KEYCLOAK_DB_PASSWORD=keycloak

# Database
POSTGRES_PASSWORD=postgres
REDIS_PASSWORD=redis

# Storage
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# Monitoring
PROMETHEUS_RETENTION=15d
LOKI_RETENTION=168h
TEMPO_RETENTION=24h

# Network
EXTERNAL_DOMAIN=localhost
GRAFANA_PORT=3001
PROMETHEUS_PORT=9090
```

### Service Configuration

#### Prometheus Configuration

Edit `prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'observastack-dev'

rule_files:
  - "alert_rules/*.yml"

scrape_configs:
  # ObservaStack application metrics
  - job_name: 'observastack-bff'
    static_configs:
      - targets: ['observastack-bff:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # Container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### Loki Configuration

Edit `loki-config.yaml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /tmp/loki
  storage:
    s3:
      endpoint: minio:9000
      buckets: loki-data
      access_key_id: minioadmin
      secret_access_key: minioadmin
      insecure: true
      s3forcepathstyle: true
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: s3
      schema: v11
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 168h
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
```

#### Vector Configuration

Edit `vector-aggregator.toml`:

```toml
# Vector configuration for log aggregation

[sources.docker_logs]
type = "docker_logs"
include_images = ["observastack/*"]

[sources.syslog]
type = "syslog"
address = "0.0.0.0:514"
mode = "udp"

[transforms.parse_logs]
type = "remap"
inputs = ["docker_logs", "syslog"]
source = '''
  .timestamp = parse_timestamp!(.timestamp, "%Y-%m-%dT%H:%M:%S%.fZ")
  .level = upcase(.level // "INFO")
  .service = .container_name // .appname // "unknown"
  .tenant_id = .labels.tenant_id // "default"
'''

[sinks.loki]
type = "loki"
inputs = ["parse_logs"]
endpoint = "http://loki:3100"
encoding.codec = "json"
labels.service = "{{ service }}"
labels.level = "{{ level }}"
labels.tenant_id = "{{ tenant_id }}"
```

## Service Profiles

The Docker Compose setup uses profiles for different deployment scenarios:

### Development Profile (Default)

```bash
# Start development services
docker compose up -d
```

Includes:
- ObservaStack application
- Core observability stack
- Development tools (hot reload, debug ports)

### Production Profile

```bash
# Start production services
docker compose --profile production up -d
```

Includes:
- Optimized builds
- Health checks
- Resource limits
- Security hardening

### Monitoring Profile

```bash
# Start with enhanced monitoring
docker compose --profile monitoring up -d
```

Includes:
- Additional exporters (node-exporter, cadvisor)
- Enhanced alerting rules
- Performance monitoring

### Init Profile

```bash
# Initialize storage and configuration
docker compose --profile init up mc && docker compose --profile init down
```

Includes:
- MinIO bucket creation
- Initial configuration setup
- Database initialization

## Advanced Configuration

### Custom Docker Compose Override

Create `docker-compose.override.yml` for local customizations:

```yaml
version: '3.8'

services:
  observastack-bff:
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    volumes:
      - ../observastack-app/bff:/app
    ports:
      - "8001:8000"  # Additional debug port

  observastack-frontend:
    volumes:
      - ../observastack-app/frontend:/app
    environment:
      - VITE_DEBUG=true

  prometheus:
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
```

### Resource Limits

Configure resource limits for production:

```yaml
services:
  observastack-bff:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  prometheus:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### Health Checks

Add health checks for better reliability:

```yaml
services:
  observastack-bff:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  prometheus:
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Data Persistence

### Volume Configuration

```yaml
volumes:
  prometheus_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/observastack/prometheus

  loki_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/observastack/loki

  grafana_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/observastack/grafana
```

### Backup Strategy

```bash
#!/bin/bash
# backup-observastack.sh

BACKUP_DIR="/backup/observastack/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Stop services
docker compose stop

# Backup volumes
docker run --rm -v prometheus_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/prometheus.tar.gz -C /data .
docker run --rm -v loki_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/loki.tar.gz -C /data .
docker run --rm -v grafana_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/grafana.tar.gz -C /data .

# Backup configuration
cp -r . "$BACKUP_DIR/config"

# Start services
docker compose start

echo "Backup completed: $BACKUP_DIR"
```

## Monitoring and Maintenance

### Service Monitoring

```bash
# Check service status
docker compose ps

# View service logs
docker compose logs -f observastack-bff
docker compose logs -f prometheus

# Monitor resource usage
docker stats

# Check service health
curl http://localhost:8000/health
curl http://localhost:9090/-/healthy
```

### Log Management

```bash
# Configure log rotation
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

# Restart Docker daemon
systemctl restart docker
```

### Updates and Maintenance

```bash
# Update to latest images
docker compose pull

# Restart services with new images
docker compose up -d

# Clean up old images
docker image prune -f

# Clean up unused volumes
docker volume prune -f
```

## Troubleshooting

### Common Issues

#### Services Won't Start

```bash
# Check Docker daemon
systemctl status docker

# Check available resources
free -h
df -h

# Check port conflicts
netstat -tlnp | grep -E ':(3000|8000|9090|3100)'

# View detailed logs
docker compose logs --tail=50 observastack-bff
```

#### Performance Issues

```bash
# Monitor resource usage
docker stats --no-stream

# Check disk I/O
iostat -x 1

# Monitor network
netstat -i

# Analyze container performance
docker exec observastack-bff top
```

#### Data Issues

```bash
# Check volume mounts
docker compose config | grep -A 5 volumes

# Verify data persistence
docker exec prometheus ls -la /prometheus

# Check storage space
docker system df
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug environment
export COMPOSE_LOG_LEVEL=DEBUG
export OBSERVASTACK_DEBUG=true

# Start with verbose logging
docker compose --verbose up -d

# Access debug endpoints
curl http://localhost:8000/debug/info
curl http://localhost:9090/api/v1/status/config
```

## Security Considerations

### Network Security

```yaml
# Custom network configuration
networks:
  observastack:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  observastack-bff:
    networks:
      - observastack
    expose:
      - "8000"
    # Don't expose to host in production
```

### Secrets Management

```bash
# Use Docker secrets for sensitive data
echo "your-secret-password" | docker secret create db_password -

# Reference in compose file
services:
  postgres:
    secrets:
      - db_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
```

### SSL/TLS Configuration

```yaml
# Add reverse proxy for SSL termination
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - observastack-frontend
      - observastack-bff
```

## Next Steps

- [Ansible Deployment](ansible.md) - Production deployment with Ansible
- [Kubernetes Deployment](kubernetes.md) - Container orchestration
- [Production Setup](production-setup.md) - Production best practices
- [Troubleshooting](../troubleshooting/common-issues.md) - Common issues and solutions