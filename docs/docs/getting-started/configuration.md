# Configuration

This guide covers the essential configuration options for ObservaStack to customize it for your environment.

## Configuration Overview

ObservaStack uses a layered configuration approach:

1. **Environment Variables** - Runtime configuration
2. **Configuration Files** - Service-specific settings
3. **Docker Compose** - Development environment
4. **Ansible Variables** - Production deployment
5. **Kubernetes ConfigMaps** - Container orchestration

## Environment Variables

### Core Application Settings

```bash
# Application Configuration
OBSERVASTACK_ENV=production
OBSERVASTACK_DEBUG=false
OBSERVASTACK_LOG_LEVEL=info

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/observastack
REDIS_URL=redis://localhost:6379/0

# Authentication
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=observastack
KEYCLOAK_CLIENT_ID=observastack-app
KEYCLOAK_CLIENT_SECRET=your-client-secret

# Data Sources
PROMETHEUS_URL=http://localhost:9090
LOKI_URL=http://localhost:3100
TEMPO_URL=http://localhost:3200
GRAFANA_URL=http://localhost:3001
```

### Multi-Tenant Configuration

```bash
# Tenant Settings
ENABLE_MULTI_TENANT=true
DEFAULT_TENANT_ID=default
TENANT_ISOLATION_MODE=strict

# RBAC Configuration
RBAC_ENABLED=true
RBAC_PROVIDER=keycloak
RBAC_CACHE_TTL=300
```

## Service Configuration Files

### Prometheus Configuration

Edit `docker/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'observastack-app'
    static_configs:
      - targets: ['observastack-bff:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Loki Configuration

Edit `docker/loki-config.yaml`:

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /tmp/loki
  storage:
    filesystem:
      chunks_directory: /tmp/loki/chunks
      rules_directory: /tmp/loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

# Multi-tenant configuration
limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  max_cache_freshness_per_query: 10m
  split_queries_by_interval: 15m
```

### Tempo Configuration

Edit `docker/tempo-config.yaml`:

```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    jaeger:
      protocols:
        thrift_http:
          endpoint: 0.0.0.0:14268
        grpc:
          endpoint: 0.0.0.0:14250
    zipkin:
      endpoint: 0.0.0.0:9411
    otlp:
      protocols:
        http:
          endpoint: 0.0.0.0:4318
        grpc:
          endpoint: 0.0.0.0:4317

ingester:
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 1h

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/traces

query_frontend:
  search:
    duration_slo: 5s
    throughput_bytes_slo: 1.073741824e+09
  trace_by_id:
    duration_slo: 5s
```

## Frontend Configuration

### Environment Configuration

Create `observastack-app/frontend/.env.local`:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_GRAFANA_BASE_URL=http://localhost:3001

# Authentication
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_KEYCLOAK_REALM=observastack
VITE_KEYCLOAK_CLIENT_ID=observastack-app

# Feature Flags
VITE_ENABLE_MULTI_TENANT=true
VITE_ENABLE_INSIGHTS=true
VITE_ENABLE_ALERTS=true

# Development
VITE_DEBUG=true
VITE_LOG_LEVEL=debug
```

### Vite Configuration

The frontend uses Vite with proxy configuration in `vite.config.ts`:

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/grafana': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/grafana/, ''),
      },
    },
  },
});
```

## Backend Configuration

### FastAPI Configuration

Edit `observastack-app/bff/app/core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Application
    app_name: str = "ObservaStack BFF"
    debug: bool = False
    version: str = "1.0.0"
    
    # Database
    database_url: str = "postgresql://user:pass@localhost/observastack"
    redis_url: str = "redis://localhost:6379/0"
    
    # Authentication
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "observastack"
    keycloak_client_id: str = "observastack-app"
    keycloak_client_secret: str = ""
    
    # Data Sources
    prometheus_url: str = "http://localhost:9090"
    loki_url: str = "http://localhost:3100"
    tempo_url: str = "http://localhost:3200"
    grafana_url: str = "http://localhost:3001"
    
    # Multi-tenant
    enable_multi_tenant: bool = True
    default_tenant_id: str = "default"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## Authentication Configuration

### Keycloak Setup

1. **Create Realm**:
   ```bash
   # Access Keycloak admin console at http://localhost:8080
   # Create new realm: "observastack"
   ```

2. **Create Client**:
   ```json
   {
     "clientId": "observastack-app",
     "enabled": true,
     "publicClient": true,
     "redirectUris": ["http://localhost:3000/*"],
     "webOrigins": ["http://localhost:3000"],
     "protocol": "openid-connect"
   }
   ```

3. **Configure Roles**:
   ```json
   {
     "roles": [
       "observastack-admin",
       "observastack-user",
       "observastack-viewer"
     ]
   }
   ```

### JWT Configuration

```python
# JWT Settings
JWT_SECRET_KEY = "your-secret-key"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DELTA = 3600  # 1 hour

# Token validation
VALIDATE_JWT_SIGNATURE = True
REQUIRE_JWT_AUDIENCE = True
JWT_AUDIENCE = "observastack-app"
```

## Data Source Integration

### Prometheus Integration

```yaml
# Add to prometheus.yml
scrape_configs:
  - job_name: 'my-application'
    static_configs:
      - targets: ['my-app:8080']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
```

### Loki Integration

```yaml
# Vector configuration for log shipping
sources:
  app_logs:
    type: file
    include:
      - /var/log/my-app/*.log

transforms:
  parse_logs:
    type: remap
    inputs: [app_logs]
    source: |
      .timestamp = parse_timestamp!(.timestamp, "%Y-%m-%d %H:%M:%S")
      .level = upcase(.level)

sinks:
  loki:
    type: loki
    inputs: [parse_logs]
    endpoint: http://loki:3100
    labels:
      service: "my-app"
      environment: "production"
```

### Tempo Integration

```yaml
# OpenTelemetry Collector configuration
exporters:
  otlp:
    endpoint: http://tempo:4317
    insecure: true

processors:
  batch:
    timeout: 1s
    send_batch_size: 1024

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp]
```

## Production Configuration

### Security Settings

```bash
# Security Configuration
SECURE_COOKIES=true
CSRF_PROTECTION=true
RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=100

# SSL/TLS
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/observastack.crt
SSL_KEY_PATH=/etc/ssl/private/observastack.key

# Security Headers
HSTS_ENABLED=true
CONTENT_SECURITY_POLICY=true
```

### Performance Tuning

```bash
# Application Performance
WORKER_PROCESSES=4
WORKER_CONNECTIONS=1000
KEEPALIVE_TIMEOUT=65

# Database Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30

# Cache Configuration
CACHE_TTL=300
CACHE_MAX_SIZE=1000
REDIS_CONNECTION_POOL=10
```

## Validation

After configuration changes, validate your setup:

```bash
# Test configuration
docker compose config

# Restart services
docker compose restart

# Check service health
curl http://localhost:8000/health
curl http://localhost:3000/health

# Validate authentication
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/user/profile
```

## Next Steps

- [Set up authentication](../user-guide/authentication.md)
- [Configure your first search](../user-guide/search.md)
- [Deploy to production](../deployment/production-setup.md)
- [Monitor performance](../troubleshooting/performance.md)