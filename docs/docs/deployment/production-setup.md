# Production Setup

This guide covers best practices and considerations for deploying ObservaStack in production environments, ensuring reliability, security, and performance.

## Production Checklist

### Pre-Deployment

- [ ] **Infrastructure Planning**: Size resources appropriately
- [ ] **Security Review**: Implement security best practices
- [ ] **Network Design**: Plan network topology and firewall rules
- [ ] **Backup Strategy**: Design backup and recovery procedures
- [ ] **Monitoring Setup**: Plan monitoring and alerting
- [ ] **Documentation**: Document deployment and procedures

### Post-Deployment

- [ ] **Health Checks**: Verify all services are healthy
- [ ] **Performance Testing**: Validate performance under load
- [ ] **Security Audit**: Conduct security assessment
- [ ] **Backup Testing**: Test backup and recovery procedures
- [ ] **Monitoring Validation**: Ensure monitoring is working
- [ ] **Team Training**: Train operations team

## Infrastructure Requirements

### Minimum Production Setup

| Component | CPU | Memory | Storage | Instances |
|-----------|-----|--------|---------|-----------|
| **Frontend** | 2 cores | 4GB | 20GB | 2+ |
| **Backend** | 4 cores | 8GB | 50GB | 2+ |
| **Prometheus** | 4 cores | 16GB | 500GB | 2+ |
| **Loki** | 4 cores | 8GB | 200GB | 2+ |
| **Tempo** | 2 cores | 4GB | 100GB | 1+ |
| **Grafana** | 2 cores | 4GB | 20GB | 1+ |
| **PostgreSQL** | 4 cores | 16GB | 200GB | 2+ |
| **Redis** | 2 cores | 8GB | 20GB | 1+ |
| **Load Balancer** | 2 cores | 4GB | 20GB | 2+ |

### Recommended Production Setup

| Component | CPU | Memory | Storage | Instances |
|-----------|-----|--------|---------|-----------|
| **Frontend** | 4 cores | 8GB | 50GB | 3+ |
| **Backend** | 8 cores | 16GB | 100GB | 3+ |
| **Prometheus** | 8 cores | 32GB | 1TB | 3+ |
| **Loki** | 8 cores | 16GB | 500GB | 3+ |
| **Tempo** | 4 cores | 8GB | 200GB | 2+ |
| **Grafana** | 4 cores | 8GB | 50GB | 2+ |
| **PostgreSQL** | 8 cores | 32GB | 500GB | 3+ |
| **Redis** | 4 cores | 16GB | 50GB | 2+ |
| **Load Balancer** | 4 cores | 8GB | 50GB | 2+ |

## Security Configuration

### SSL/TLS Setup

#### Certificate Management

```bash
# Generate SSL certificate with Let's Encrypt
certbot certonly --standalone \
  -d observastack.example.com \
  -d grafana.observastack.example.com \
  -d prometheus.observastack.example.com \
  --email admin@example.com \
  --agree-tos \
  --non-interactive

# Set up automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

#### Nginx SSL Configuration

```nginx
# /etc/nginx/sites-available/observastack
server {
    listen 443 ssl http2;
    server_name observastack.example.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/observastack.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/observastack.example.com/privkey.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Content Security Policy
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' wss:; frame-ancestors 'none';" always;

    location / {
        proxy_pass http://observastack_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Authentication Security

#### Keycloak Production Configuration

```bash
# Keycloak production settings
export KEYCLOAK_ADMIN=admin
export KEYCLOAK_ADMIN_PASSWORD=secure-admin-password
export KC_DB=postgres
export KC_DB_URL=jdbc:postgresql://db-host:5432/keycloak
export KC_DB_USERNAME=keycloak
export KC_DB_PASSWORD=secure-db-password
export KC_HOSTNAME=auth.observastack.example.com
export KC_PROXY=edge

# Start Keycloak in production mode
/opt/keycloak/bin/kc.sh start --optimized
```

#### JWT Security Configuration

```python
# app/core/config.py
class ProductionSettings(Settings):
    # JWT Configuration
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "RS256"  # Use RSA for production
    JWT_EXPIRATION_DELTA: int = 3600  # 1 hour
    JWT_REFRESH_EXPIRATION_DELTA: int = 86400  # 24 hours
    
    # Security Settings
    SECURE_COOKIES: bool = True
    CSRF_PROTECTION: bool = True
    RATE_LIMITING: bool = True
    MAX_REQUESTS_PER_MINUTE: int = 100
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "https://observastack.example.com",
        "https://grafana.observastack.example.com"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
```

### Network Security

#### Firewall Configuration

```bash
# UFW firewall rules
ufw default deny incoming
ufw default allow outgoing

# SSH access (restrict to management network)
ufw allow from 10.0.0.0/8 to any port 22

# HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Internal service communication
ufw allow from 10.0.1.0/24 to any port 5432  # PostgreSQL
ufw allow from 10.0.1.0/24 to any port 6379  # Redis
ufw allow from 10.0.1.0/24 to any port 9090  # Prometheus
ufw allow from 10.0.1.0/24 to any port 3100  # Loki
ufw allow from 10.0.1.0/24 to any port 3200  # Tempo

ufw enable
```

#### Network Segmentation

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   DMZ Network   │    │  App Network    │    │  Data Network   │
│   10.0.1.0/24   │    │  10.0.2.0/24    │    │  10.0.3.0/24    │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Load Balancers  │    │ Frontend        │    │ PostgreSQL      │
│ Web Servers     │    │ Backend API     │    │ Redis           │
│                 │    │ Grafana         │    │ Backup Storage  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## High Availability Configuration

### Load Balancer Setup

#### HAProxy Configuration

```
# /etc/haproxy/haproxy.cfg
global
    daemon
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog
    option dontlognull
    option redispatch
    retries 3

frontend observastack_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/observastack.pem
    redirect scheme https if !{ ssl_fc }
    
    # Health check endpoint
    acl health_check path_beg /health
    use_backend health if health_check
    
    default_backend observastack_web

backend observastack_web
    balance roundrobin
    option httpchk GET /health
    
    server web-01 10.0.1.10:3000 check
    server web-02 10.0.1.11:3000 check
    server web-03 10.0.1.12:3000 check

backend observastack_api
    balance roundrobin
    option httpchk GET /health
    
    server api-01 10.0.1.20:8000 check
    server api-02 10.0.1.21:8000 check
    server api-03 10.0.1.22:8000 check

listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats admin if TRUE
```

### Database High Availability

#### PostgreSQL Streaming Replication

```bash
# Primary server configuration
# /etc/postgresql/15/main/postgresql.conf
wal_level = replica
max_wal_senders = 3
max_replication_slots = 3
synchronous_commit = on
synchronous_standby_names = 'standby1,standby2'

# /etc/postgresql/15/main/pg_hba.conf
host replication replicator 10.0.3.0/24 md5
```

```bash
# Standby server setup
pg_basebackup -h primary-server -D /var/lib/postgresql/15/main -U replicator -P -v -R -W -C -S standby1
```

#### Redis Sentinel Configuration

```
# /etc/redis/sentinel.conf
port 26379
sentinel monitor mymaster 10.0.3.10 6379 2
sentinel auth-pass mymaster secure-redis-password
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000
```

## Performance Optimization

### System Tuning

#### Kernel Parameters

```bash
# /etc/sysctl.conf
# Network performance
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 3

# Memory management
vm.swappiness = 1
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.overcommit_memory = 1

# File system
fs.file-max = 2097152
fs.nr_open = 1048576

# Apply settings
sysctl -p
```

#### File Limits

```bash
# /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535

# /etc/systemd/system.conf
DefaultLimitNOFILE=65535
DefaultLimitNPROC=65535
```

### Application Performance

#### Backend Optimization

```python
# app/core/config.py
class ProductionSettings(Settings):
    # Worker configuration
    WORKER_PROCESSES: int = Field(default_factory=lambda: os.cpu_count())
    WORKER_CONNECTIONS: int = 1000
    KEEPALIVE_TIMEOUT: int = 65
    
    # Database connection pool
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # Cache configuration
    CACHE_TTL: int = 300
    CACHE_MAX_SIZE: int = 1000
    REDIS_CONNECTION_POOL: int = 10
    
    # Query optimization
    QUERY_TIMEOUT: int = 30
    MAX_QUERY_RESULTS: int = 10000
```

#### Frontend Optimization

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts', 'd3'],
          utils: ['lodash', 'date-fns']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  },
  server: {
    hmr: {
      overlay: false
    }
  }
});
```

## Monitoring and Alerting

### Production Monitoring Stack

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'production'
    environment: 'prod'

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'observastack-backend'
    static_configs:
      - targets: ['api-01:8000', 'api-02:8000', 'api-03:8000']
    scrape_interval: 30s
    metrics_path: '/metrics'

  - job_name: 'observastack-frontend'
    static_configs:
      - targets: ['web-01:3000', 'web-02:3000', 'web-03:3000']
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-01:9100', 'node-02:9100', 'node-03:9100']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['db-01:9187', 'db-02:9187']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['cache-01:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager-01:9093', 'alertmanager-02:9093']
```

#### Critical Alerts

```yaml
# alerts/critical.yml
groups:
  - name: critical.rules
    rules:
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "{{ $labels.job }} on {{ $labels.instance }} has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/second"

      - alert: DatabaseConnectionFailure
        expr: postgresql_up == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"
          description: "Cannot connect to PostgreSQL database"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space low on {{ $labels.instance }}"
          description: "Disk space is below 10% on {{ $labels.instance }}"

      - alert: MemoryUsageHigh
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 90% on {{ $labels.instance }}"
```

### Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@observastack.example.com'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 0s
      repeat_interval: 5m

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@example.com'
        subject: '[ObservaStack] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}

  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@example.com'
        subject: '[CRITICAL] ObservaStack Alert'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        title: 'Critical ObservaStack Alert'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
```

## Backup and Recovery

### Backup Strategy

#### Database Backup

```bash
#!/bin/bash
# /opt/scripts/backup-database.sh

BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup main database
pg_dump -h db-01 -U observastack -d observastack | gzip > $BACKUP_DIR/observastack_$DATE.sql.gz

# Backup Keycloak database
pg_dump -h db-01 -U keycloak -d keycloak | gzip > $BACKUP_DIR/keycloak_$DATE.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/observastack_$DATE.sql.gz s3://observastack-backups/postgresql/
aws s3 cp $BACKUP_DIR/keycloak_$DATE.sql.gz s3://observastack-backups/postgresql/

# Clean up old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log backup completion
echo "$(date): Database backup completed successfully" >> /var/log/backup.log
```

#### Configuration Backup

```bash
#!/bin/bash
# /opt/scripts/backup-config.sh

BACKUP_DIR="/backup/config"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configurations
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
  /etc/nginx/ \
  /etc/prometheus/ \
  /etc/grafana/ \
  /opt/observastack/config/

# Upload to S3
aws s3 cp $BACKUP_DIR/config_$DATE.tar.gz s3://observastack-backups/config/

echo "$(date): Configuration backup completed" >> /var/log/backup.log
```

### Recovery Procedures

#### Database Recovery

```bash
#!/bin/bash
# Database recovery script

BACKUP_FILE=$1
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop services
systemctl stop observastack-backend
systemctl stop grafana-server

# Restore database
gunzip -c $BACKUP_FILE | psql -h db-01 -U observastack -d observastack

# Start services
systemctl start observastack-backend
systemctl start grafana-server

echo "Database recovery completed"
```

## Maintenance Procedures

### Rolling Updates

```bash
#!/bin/bash
# Rolling update script

NEW_VERSION=$1
if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new_version>"
    exit 1
fi

# Update backend servers one by one
for server in api-01 api-02 api-03; do
    echo "Updating $server..."
    
    # Remove from load balancer
    curl -X POST "http://lb-01:8404/stats" -d "action=disable&b=observastack_api&s=$server"
    
    # Wait for connections to drain
    sleep 30
    
    # Update server
    ssh $server "docker pull observastack/backend:$NEW_VERSION"
    ssh $server "docker stop observastack-backend"
    ssh $server "docker run -d --name observastack-backend observastack/backend:$NEW_VERSION"
    
    # Health check
    while ! curl -f http://$server:8000/health; do
        echo "Waiting for $server to be healthy..."
        sleep 10
    done
    
    # Add back to load balancer
    curl -X POST "http://lb-01:8404/stats" -d "action=enable&b=observastack_api&s=$server"
    
    echo "$server updated successfully"
done
```

### Maintenance Windows

```bash
#!/bin/bash
# Maintenance window script

# Send maintenance notification
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-type: application/json' \
  --data '{"text":"ObservaStack maintenance starting in 10 minutes"}'

# Wait for maintenance window
sleep 600

# Put system in maintenance mode
echo "Maintenance in progress" > /var/www/html/maintenance.html
nginx -s reload

# Perform maintenance tasks
systemctl stop observastack-backend
systemctl stop observastack-frontend

# Update system packages
apt update && apt upgrade -y

# Restart services
systemctl start observastack-backend
systemctl start observastack-frontend

# Remove maintenance mode
rm /var/www/html/maintenance.html
nginx -s reload

# Send completion notification
curl -X POST https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  -H 'Content-type: application/json' \
  --data '{"text":"ObservaStack maintenance completed successfully"}'
```

## Disaster Recovery

### Recovery Time Objectives

| Component | RTO | RPO | Recovery Method |
|-----------|-----|-----|-----------------|
| **Frontend** | 5 minutes | 0 | Load balancer failover |
| **Backend** | 10 minutes | 0 | Auto-scaling + health checks |
| **Database** | 30 minutes | 15 minutes | Streaming replication |
| **Monitoring** | 15 minutes | 5 minutes | Multi-region deployment |
| **Complete System** | 2 hours | 1 hour | Full site recovery |

### Disaster Recovery Plan

1. **Assessment Phase** (0-15 minutes)
   - Identify scope of outage
   - Activate incident response team
   - Communicate with stakeholders

2. **Immediate Response** (15-30 minutes)
   - Failover to secondary systems
   - Redirect traffic to backup site
   - Assess data integrity

3. **Recovery Phase** (30 minutes - 2 hours)
   - Restore services from backups
   - Validate system functionality
   - Monitor for issues

4. **Post-Recovery** (2+ hours)
   - Conduct post-mortem analysis
   - Update documentation
   - Implement improvements

## Compliance and Auditing

### Audit Logging

```python
# app/middleware/audit.py
import logging
from fastapi import Request
import json

audit_logger = logging.getLogger("audit")

class AuditMiddleware:
    async def __call__(self, request: Request, call_next):
        # Log request
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": getattr(request.state, "user_id", None),
            "method": request.method,
            "path": request.url.path,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent")
        }
        
        response = await call_next(request)
        
        # Log response
        audit_data.update({
            "status_code": response.status_code,
            "response_time": time.time() - start_time
        })
        
        audit_logger.info(json.dumps(audit_data))
        return response
```

### Data Retention Policies

```yaml
# Data retention configuration
retention_policies:
  logs:
    application_logs: 90d
    audit_logs: 7y
    access_logs: 30d
  
  metrics:
    high_resolution: 7d
    medium_resolution: 30d
    low_resolution: 1y
  
  traces:
    detailed_traces: 7d
    sampled_traces: 30d
  
  backups:
    daily_backups: 30d
    weekly_backups: 12w
    monthly_backups: 12m
```

## Next Steps

- [Review troubleshooting guide](../troubleshooting/common-issues.md) for operational issues
- [Set up monitoring](../user-guide/alerts.md) for proactive issue detection
- [Configure backup automation](ansible.md) with Ansible playbooks