# Kubernetes Deployment

Deploy ObservaStack on Kubernetes for scalable, cloud-native observability. This guide covers deployment using Helm charts with production-ready configurations.

## Prerequisites

- **Kubernetes**: Version 1.24+
- **Helm**: Version 3.8+
- **kubectl**: Configured for your cluster
- **Storage**: Persistent volume support
- **Ingress**: Ingress controller (nginx, traefik, etc.)

## Quick Start

```bash
# Add ObservaStack Helm repository
helm repo add observastack https://observastack.github.io/helm-charts
helm repo update

# Install ObservaStack
helm install observastack observastack/observastack \
  --namespace observastack \
  --create-namespace \
  --values values.yaml
```

## Configuration

### Basic Values File

```yaml
# values.yaml
global:
  domain: observastack.example.com
  storageClass: fast-ssd
  
frontend:
  replicaCount: 3
  image:
    repository: observastack/frontend
    tag: "1.0.0"
  
backend:
  replicaCount: 3
  image:
    repository: observastack/backend
    tag: "1.0.0"

prometheus:
  enabled: true
  retention: 30d
  storage: 100Gi

loki:
  enabled: true
  retention: 7d
  storage: 50Gi

grafana:
  enabled: true
  adminPassword: admin123

ingress:
  enabled: true
  className: nginx
  tls:
    enabled: true
    secretName: observastack-tls
```

## Production Configuration

### High Availability Setup

```yaml
# production-values.yaml
global:
  domain: observastack.company.com
  environment: production
  
# Frontend configuration
frontend:
  replicaCount: 5
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

# Backend configuration  
backend:
  replicaCount: 5
  resources:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: 2
      memory: 4Gi
      
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 15
    targetCPUUtilizationPercentage: 70

# Database configuration
postgresql:
  enabled: true
  auth:
    postgresPassword: secure-password
    database: observastack
  primary:
    persistence:
      enabled: true
      size: 100Gi
      storageClass: fast-ssd
  readReplicas:
    replicaCount: 2

# Redis configuration
redis:
  enabled: true
  auth:
    enabled: true
    password: secure-redis-password
  master:
    persistence:
      enabled: true
      size: 10Gi

# Prometheus configuration
prometheus:
  enabled: true
  server:
    retention: 30d
    persistentVolume:
      enabled: true
      size: 200Gi
      storageClass: fast-ssd
    replicaCount: 2
    
  alertmanager:
    enabled: true
    persistentVolume:
      enabled: true
      size: 10Gi

# Loki configuration
loki:
  enabled: true
  persistence:
    enabled: true
    size: 100Gi
    storageClass: fast-ssd
  config:
    limits_config:
      retention_period: 168h
    storage_config:
      aws:
        s3: s3://loki-storage-bucket
        region: us-west-2

# Tempo configuration
tempo:
  enabled: true
  persistence:
    enabled: true
    size: 50Gi
  config:
    storage:
      trace:
        backend: s3
        s3:
          bucket: tempo-traces-bucket
          region: us-west-2

# Grafana configuration
grafana:
  enabled: true
  adminPassword: secure-admin-password
  persistence:
    enabled: true
    size: 10Gi
  
  sidecar:
    dashboards:
      enabled: true
    datasources:
      enabled: true

# Ingress configuration
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  
  tls:
    enabled: true
    secretName: observastack-tls
    
# Security configuration
security:
  podSecurityPolicy:
    enabled: true
  networkPolicy:
    enabled: true
  serviceAccount:
    create: true
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/observastack-role
```

## Installation Steps

### 1. Prepare Namespace

```bash
# Create namespace
kubectl create namespace observastack

# Create secrets
kubectl create secret generic observastack-secrets \
  --from-literal=database-password=secure-db-password \
  --from-literal=redis-password=secure-redis-password \
  --from-literal=jwt-secret=secure-jwt-secret \
  --namespace observastack
```

### 2. Install Dependencies

```bash
# Install cert-manager for SSL certificates
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Install ingress controller (if not already installed)
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace
```

### 3. Deploy ObservaStack

```bash
# Install with production values
helm install observastack observastack/observastack \
  --namespace observastack \
  --values production-values.yaml \
  --wait --timeout=10m
```

## Monitoring and Observability

### ServiceMonitor for Prometheus

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: observastack-backend
  namespace: observastack
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: observastack-backend
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
```

### Custom Dashboards

```yaml
# dashboard-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: observastack-dashboard
  namespace: observastack
  labels:
    grafana_dashboard: "1"
data:
  observastack-overview.json: |
    {
      "dashboard": {
        "title": "ObservaStack Overview",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(http_requests_total{job=\"observastack-backend\"}[5m])"
              }
            ]
          }
        ]
      }
    }
```

## Scaling and Performance

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: observastack-backend-hpa
  namespace: observastack
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: observastack-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Pod Autoscaler

```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: observastack-backend-vpa
  namespace: observastack
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: observastack-backend
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: backend
      maxAllowed:
        cpu: 4
        memory: 8Gi
      minAllowed:
        cpu: 100m
        memory: 128Mi
```

## Security Configuration

### Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: observastack-network-policy
  namespace: observastack
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: observastack-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: observastack-frontend
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: postgresql
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app.kubernetes.io/name: redis
    ports:
    - protocol: TCP
      port: 6379
```

### Pod Security Standards

```yaml
# pod-security-policy.yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: observastack-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## Backup and Disaster Recovery

### Velero Backup Configuration

```yaml
# backup-schedule.yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: observastack-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  template:
    includedNamespaces:
    - observastack
    storageLocation: default
    volumeSnapshotLocations:
    - default
    ttl: 720h0m0s  # 30 days
```

### Database Backup CronJob

```yaml
# db-backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgresql-backup
  namespace: observastack
spec:
  schedule: "0 1 * * *"  # Daily at 1 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: postgres-backup
            image: postgres:15
            command:
            - /bin/bash
            - -c
            - |
              pg_dump -h postgresql -U observastack -d observastack | \
              gzip > /backup/observastack-$(date +%Y%m%d_%H%M%S).sql.gz
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: observastack-secrets
                  key: database-password
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

## Maintenance Operations

### Rolling Updates

```bash
# Update to new version
helm upgrade observastack observastack/observastack \
  --namespace observastack \
  --values production-values.yaml \
  --set backend.image.tag=1.1.0 \
  --set frontend.image.tag=1.1.0
```

### Database Migrations

```yaml
# migration-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: observastack-migration
  namespace: observastack
spec:
  template:
    spec:
      containers:
      - name: migration
        image: observastack/backend:1.1.0
        command: ["python", "-m", "alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: observastack-secrets
              key: database-url
      restartPolicy: Never
  backoffLimit: 3
```

## Troubleshooting

### Common Issues

#### Pod Startup Problems

```bash
# Check pod status
kubectl get pods -n observastack

# Describe problematic pod
kubectl describe pod <pod-name> -n observastack

# Check logs
kubectl logs <pod-name> -n observastack -f
```

#### Service Discovery Issues

```bash
# Test service connectivity
kubectl run debug --image=busybox -it --rm --restart=Never -- nslookup observastack-backend.observastack.svc.cluster.local

# Check service endpoints
kubectl get endpoints -n observastack
```

#### Storage Issues

```bash
# Check persistent volumes
kubectl get pv

# Check persistent volume claims
kubectl get pvc -n observastack

# Describe storage issues
kubectl describe pvc <pvc-name> -n observastack
```

### Debug Tools

```bash
# Port forward for local debugging
kubectl port-forward svc/observastack-backend 8000:8000 -n observastack

# Execute commands in pod
kubectl exec -it <pod-name> -n observastack -- /bin/bash

# Check resource usage
kubectl top pods -n observastack
kubectl top nodes
```

## Performance Optimization

### Resource Requests and Limits

```yaml
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2
    memory: 4Gi
```

### Node Affinity

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: node-type
          operator: In
          values:
          - high-memory
```

### Pod Disruption Budget

```yaml
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: observastack-backend-pdb
  namespace: observastack
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app.kubernetes.io/name: observastack-backend
```

## Multi-Cluster Setup

### Cluster Federation

```yaml
# cluster-config.yaml
clusters:
  - name: us-west-2
    endpoint: https://k8s-us-west-2.example.com
    region: us-west-2
  - name: eu-west-1
    endpoint: https://k8s-eu-west-1.example.com
    region: eu-west-1

federation:
  enabled: true
  prometheus:
    global_query_url: https://thanos-query.example.com
```

## Next Steps

- [Set up production monitoring](production-setup.md)
- [Configure Ansible deployment](ansible.md) for bare metal
- [Review troubleshooting guide](../troubleshooting/common-issues.md)