# Ansible Deployment

Ansible provides a robust, automated way to deploy ObservaStack in production environments. This guide covers the complete deployment process using our Ansible playbooks.

## Overview

The Ansible deployment includes:

- **Multi-node setup** with high availability
- **Service configuration** and management
- **SSL/TLS certificate** management
- **Backup and monitoring** setup
- **Rolling updates** and maintenance

## Prerequisites

### System Requirements

#### Control Node (Ansible Host)
- **Ansible**: Version 2.9+
- **Python**: 3.8+
- **SSH access** to target hosts
- **Git**: For cloning the repository

#### Target Hosts
- **Operating System**: Ubuntu 20.04+, CentOS 8+, or RHEL 8+
- **Memory**: 16GB+ RAM per node
- **CPU**: 8+ cores per node
- **Storage**: 100GB+ available disk space
- **Network**: Reliable network connectivity between nodes

### Network Requirements

| Service | Port | Protocol | Description |
|---------|------|----------|-------------|
| SSH | 22 | TCP | Ansible management |
| HTTP | 80 | TCP | Web interface (redirects to HTTPS) |
| HTTPS | 443 | TCP | Secure web interface |
| Prometheus | 9090 | TCP | Metrics collection |
| Grafana | 3000 | TCP | Dashboard access |
| Loki | 3100 | TCP | Log ingestion |
| Tempo | 3200 | TCP | Trace ingestion |

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/observastack/observastack.git
cd observastack/install/ansible
```

### 2. Install Ansible Dependencies

```bash
# Install Ansible
pip install ansible

# Install required collections
ansible-galaxy collection install -r requirements.yml

# Install required roles
ansible-galaxy role install -r requirements.yml
```

### 3. Configure Inventory

Create your inventory file:

```bash
cp inventories/example/hosts.ini inventories/production/hosts.ini
```

Edit the inventory file:

```ini
# inventories/production/hosts.ini

[observastack_frontend]
web-01 ansible_host=10.0.1.10 ansible_user=ubuntu
web-02 ansible_host=10.0.1.11 ansible_user=ubuntu

[observastack_backend]
api-01 ansible_host=10.0.1.20 ansible_user=ubuntu
api-02 ansible_host=10.0.1.21 ansible_user=ubuntu

[prometheus]
prom-01 ansible_host=10.0.1.30 ansible_user=ubuntu
prom-02 ansible_host=10.0.1.31 ansible_user=ubuntu

[loki]
loki-01 ansible_host=10.0.1.40 ansible_user=ubuntu
loki-02 ansible_host=10.0.1.41 ansible_user=ubuntu

[tempo]
tempo-01 ansible_host=10.0.1.50 ansible_user=ubuntu

[grafana]
grafana-01 ansible_host=10.0.1.60 ansible_user=ubuntu

[keycloak]
auth-01 ansible_host=10.0.1.70 ansible_user=ubuntu

[postgresql]
db-01 ansible_host=10.0.1.80 ansible_user=ubuntu

[redis]
cache-01 ansible_host=10.0.1.90 ansible_user=ubuntu

[load_balancer]
lb-01 ansible_host=10.0.1.100 ansible_user=ubuntu

# Group variables
[observastack:children]
observastack_frontend
observastack_backend
prometheus
loki
tempo
grafana
keycloak
postgresql
redis
load_balancer

[observastack:vars]
# Common variables
ansible_ssh_private_key_file=~/.ssh/observastack-key
ansible_python_interpreter=/usr/bin/python3
```

### 4. Configure Variables

Edit group variables:

```yaml
# inventories/production/group_vars/all.yml

# Domain and SSL configuration
domain_name: observastack.example.com
ssl_enabled: true
ssl_cert_path: /etc/ssl/certs/observastack.crt
ssl_key_path: /etc/ssl/private/observastack.key

# Database configuration
postgresql_version: 15
postgresql_databases:
  - name: observastack
    owner: observastack
  - name: keycloak
    owner: keycloak

postgresql_users:
  - name: observastack
    password: "{{ vault_observastack_db_password }}"
    priv: "observastack:ALL"
  - name: keycloak
    password: "{{ vault_keycloak_db_password }}"
    priv: "keycloak:ALL"

# Redis configuration
redis_version: 7
redis_password: "{{ vault_redis_password }}"
redis_maxmemory: 2gb

# ObservaStack application
observastack_version: latest
observastack_environment: production

# Authentication
keycloak_admin_user: admin
keycloak_admin_password: "{{ vault_keycloak_admin_password }}"

# Monitoring retention
prometheus_retention: 30d
loki_retention: 7d
tempo_retention: 24h

# Backup configuration
backup_enabled: true
backup_schedule: "0 2 * * *"  # Daily at 2 AM
backup_retention_days: 30
backup_s3_bucket: observastack-backups
```

### 5. Secure Secrets with Ansible Vault

Create encrypted variables:

```bash
# Create vault file
ansible-vault create inventories/production/group_vars/vault.yml
```

Add sensitive variables:

```yaml
# vault.yml (encrypted)
vault_observastack_db_password: your-secure-db-password
vault_keycloak_db_password: your-secure-keycloak-password
vault_keycloak_admin_password: your-secure-admin-password
vault_redis_password: your-secure-redis-password
vault_jwt_secret_key: your-secure-jwt-secret
vault_backup_s3_access_key: your-s3-access-key
vault_backup_s3_secret_key: your-s3-secret-key
```

## Deployment Process

### 1. Prepare Hosts

```bash
# Test connectivity
ansible -i inventories/production/hosts.ini all -m ping

# Prepare hosts (install Python, update packages)
ansible-playbook -i inventories/production/hosts.ini playbooks/prepare.yml
```

### 2. Deploy Infrastructure

```bash
# Deploy database and supporting services
ansible-playbook -i inventories/production/hosts.ini playbooks/infrastructure.yml --ask-vault-pass
```

### 3. Deploy ObservaStack

```bash
# Deploy main application
ansible-playbook -i inventories/production/hosts.ini playbooks/observastack.yml --ask-vault-pass
```

### 4. Configure Load Balancer

```bash
# Set up load balancer and SSL termination
ansible-playbook -i inventories/production/hosts.ini playbooks/load-balancer.yml --ask-vault-pass
```

### 5. Complete Installation

```bash
# Run complete installation (all playbooks)
ansible-playbook -i inventories/production/hosts.ini playbooks/install.yml --ask-vault-pass
```

## Playbook Structure

### Main Playbooks

```
playbooks/
├── install.yml              # Complete installation
├── prepare.yml              # Host preparation
├── infrastructure.yml       # Database, Redis, etc.
├── observastack.yml        # Main application
├── load-balancer.yml       # Load balancer setup
├── monitoring.yml          # Monitoring stack
├── backup.yml              # Backup configuration
└── update.yml              # Rolling updates
```

### Role Structure

```
roles/
├── common/                 # Common system setup
├── postgresql/            # PostgreSQL database
├── redis/                 # Redis cache
├── keycloak/             # Authentication service
├── prometheus/           # Metrics collection
├── loki/                 # Log aggregation
├── tempo/                # Distributed tracing
├── grafana/              # Visualization
├── observastack-frontend/ # React frontend
├── observastack-backend/  # FastAPI backend
├── nginx/                # Load balancer
└── backup/               # Backup system
```

## Configuration Examples

### Prometheus Configuration

```yaml
# roles/prometheus/templates/prometheus.yml.j2
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: '{{ cluster_name }}'
    environment: '{{ observastack_environment }}'

rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: 
{% for host in groups['prometheus'] %}
        - '{{ hostvars[host]['ansible_default_ipv4']['address'] }}:9090'
{% endfor %}

  - job_name: 'observastack-backend'
    static_configs:
      - targets:
{% for host in groups['observastack_backend'] %}
        - '{{ hostvars[host]['ansible_default_ipv4']['address'] }}:8000'
{% endfor %}

  - job_name: 'node-exporter'
    static_configs:
      - targets:
{% for host in groups['observastack'] %}
        - '{{ hostvars[host]['ansible_default_ipv4']['address'] }}:9100'
{% endfor %}

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - 'localhost:9093'
```

### Nginx Load Balancer

```nginx
# roles/nginx/templates/observastack.conf.j2
upstream observastack_frontend {
{% for host in groups['observastack_frontend'] %}
    server {{ hostvars[host]['ansible_default_ipv4']['address'] }}:3000;
{% endfor %}
}

upstream observastack_backend {
{% for host in groups['observastack_backend'] %}
    server {{ hostvars[host]['ansible_default_ipv4']['address'] }}:8000;
{% endfor %}
}

server {
    listen 80;
    server_name {{ domain_name }};
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name {{ domain_name }};

    ssl_certificate {{ ssl_cert_path }};
    ssl_certificate_key {{ ssl_key_path }};
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    location / {
        proxy_pass http://observastack_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://observastack_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /grafana/ {
        proxy_pass http://{{ hostvars[groups['grafana'][0]]['ansible_default_ipv4']['address'] }}:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service Template

```ini
# roles/observastack-backend/templates/observastack-backend.service.j2
[Unit]
Description=ObservaStack Backend API
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=observastack
Group=observastack
WorkingDirectory=/opt/observastack/backend
Environment=PATH=/opt/observastack/backend/.venv/bin
ExecStart=/opt/observastack/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

# Environment variables
Environment=OBSERVASTACK_ENV={{ observastack_environment }}
Environment=DATABASE_URL=postgresql://observastack:{{ vault_observastack_db_password }}@{{ hostvars[groups['postgresql'][0]]['ansible_default_ipv4']['address'] }}/observastack
Environment=REDIS_URL=redis://:{{ vault_redis_password }}@{{ hostvars[groups['redis'][0]]['ansible_default_ipv4']['address'] }}:6379/0
Environment=KEYCLOAK_URL=http://{{ hostvars[groups['keycloak'][0]]['ansible_default_ipv4']['address'] }}:8080
Environment=PROMETHEUS_URL=http://{{ hostvars[groups['prometheus'][0]]['ansible_default_ipv4']['address'] }}:9090
Environment=LOKI_URL=http://{{ hostvars[groups['loki'][0]]['ansible_default_ipv4']['address'] }}:3100
Environment=TEMPO_URL=http://{{ hostvars[groups['tempo'][0]]['ansible_default_ipv4']['address'] }}:3200

[Install]
WantedBy=multi-user.target
```

## High Availability Setup

### Database Clustering

```yaml
# PostgreSQL streaming replication
postgresql_streaming_replication:
  enabled: true
  primary_host: "{{ groups['postgresql'][0] }}"
  replica_hosts: "{{ groups['postgresql'][1:] }}"
  replication_user: replicator
  replication_password: "{{ vault_replication_password }}"
```

### Load Balancer Redundancy

```yaml
# HAProxy + Keepalived for load balancer HA
haproxy_enabled: true
keepalived_enabled: true
virtual_ip: 10.0.1.200

haproxy_backend_servers:
  - name: web-01
    address: "{{ hostvars['web-01']['ansible_default_ipv4']['address'] }}"
    port: 3000
  - name: web-02
    address: "{{ hostvars['web-02']['ansible_default_ipv4']['address'] }}"
    port: 3000
```

### Prometheus Federation

```yaml
# Prometheus federation for scalability
prometheus_federation:
  enabled: true
  global_prometheus: "{{ groups['prometheus'][0] }}"
  shard_prometheus: "{{ groups['prometheus'][1:] }}"
```

## Maintenance Operations

### Rolling Updates

```bash
# Update ObservaStack to new version
ansible-playbook -i inventories/production/hosts.ini playbooks/update.yml \
  --extra-vars "observastack_version=1.2.0" \
  --ask-vault-pass
```

### Backup Operations

```bash
# Manual backup
ansible-playbook -i inventories/production/hosts.ini playbooks/backup.yml \
  --tags manual \
  --ask-vault-pass

# Restore from backup
ansible-playbook -i inventories/production/hosts.ini playbooks/restore.yml \
  --extra-vars "backup_date=2025-08-15" \
  --ask-vault-pass
```

### Health Checks

```bash
# Check service health
ansible-playbook -i inventories/production/hosts.ini playbooks/health-check.yml
```

## Monitoring and Alerting

### Service Monitoring

```yaml
# Prometheus alerting rules
groups:
  - name: observastack.rules
    rules:
      - alert: ObservaStackDown
        expr: up{job="observastack-backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "ObservaStack backend is down"
          description: "ObservaStack backend on {{ $labels.instance }} has been down for more than 1 minute"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 90% on {{ $labels.instance }}"
```

### Log Aggregation

```yaml
# Centralized logging with rsyslog
rsyslog_config:
  - name: observastack
    facility: local0
    target: "{{ hostvars[groups['loki'][0]]['ansible_default_ipv4']['address'] }}"
    port: 514
    protocol: udp
```

## Security Configuration

### Firewall Rules

```yaml
# UFW firewall configuration
ufw_rules:
  - rule: allow
    port: 22
    proto: tcp
    src: "{{ management_network }}"
  - rule: allow
    port: 443
    proto: tcp
  - rule: allow
    port: 80
    proto: tcp
  - rule: deny
    direction: incoming
    proto: any
```

### SSL Certificate Management

```yaml
# Let's Encrypt certificate
letsencrypt_enabled: true
letsencrypt_email: admin@example.com
letsencrypt_domains:
  - "{{ domain_name }}"
  - "grafana.{{ domain_name }}"
  - "prometheus.{{ domain_name }}"
```

## Troubleshooting

### Common Issues

#### SSH Connection Problems

```bash
# Test SSH connectivity
ansible -i inventories/production/hosts.ini all -m ping -vvv

# Check SSH key permissions
chmod 600 ~/.ssh/observastack-key
```

#### Service Startup Failures

```bash
# Check service status on specific host
ansible -i inventories/production/hosts.ini web-01 -m systemd -a "name=observastack-frontend state=started"

# View service logs
ansible -i inventories/production/hosts.ini web-01 -m shell -a "journalctl -u observastack-frontend -n 50"
```

#### Database Connection Issues

```bash
# Test database connectivity
ansible -i inventories/production/hosts.ini api-01 -m postgresql_ping -a "host={{ hostvars[groups['postgresql'][0]]['ansible_default_ipv4']['address'] }} port=5432 user=observastack password={{ vault_observastack_db_password }}"
```

### Debug Mode

```bash
# Run playbook with debug output
ansible-playbook -i inventories/production/hosts.ini playbooks/install.yml \
  --ask-vault-pass \
  -vvv
```

### Validation Scripts

```bash
# Validate deployment
ansible-playbook -i inventories/production/hosts.ini playbooks/validate.yml
```

## Performance Tuning

### System Optimization

```yaml
# Kernel parameters for high-performance systems
sysctl_config:
  net.core.somaxconn: 65535
  net.ipv4.tcp_max_syn_backlog: 65535
  vm.swappiness: 1
  vm.dirty_ratio: 15
  vm.dirty_background_ratio: 5
```

### Application Tuning

```yaml
# ObservaStack performance settings
observastack_backend_workers: "{{ ansible_processor_vcpus }}"
observastack_backend_max_connections: 1000
observastack_frontend_pm2_instances: "{{ ansible_processor_vcpus }}"
```

## Next Steps

- [Configure Kubernetes deployment](kubernetes.md) for container orchestration
- [Set up production monitoring](production-setup.md) for operational excellence
- [Review troubleshooting guide](../troubleshooting/common-issues.md) for common issues