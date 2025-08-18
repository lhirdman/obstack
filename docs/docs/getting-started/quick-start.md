# Quick Start

Get ObservaStack running in under 5 minutes with this quick start guide.

## 1. Prerequisites Check

Ensure you have Docker and Docker Compose installed:

```bash
# Check Docker version
docker --version
# Should show: Docker version 20.10.0 or higher

# Check Docker Compose version
docker compose version
# Should show: Docker Compose version v2.0.0 or higher
```

## 2. Clone and Start

```bash
# Clone the repository
git clone https://github.com/observastack/observastack.git
cd observastack/docker

# Initialize storage (first time only)
docker compose --profile init up mc && docker compose --profile init down

# Start ObservaStack
docker compose up -d
```

## 3. Access the Interface

Open your browser and go to: **http://localhost:3000**

- **Username**: `admin`
- **Password**: `admin`

## 4. Explore the Features

### Search Across All Data
1. Click on **Search** in the navigation
2. Try searching for: `error` or `status:500`
3. Switch between Logs, Metrics, and Traces tabs

### View Dashboards
1. Navigate to **Dashboards**
2. Explore pre-built dashboards for system metrics
3. Create custom dashboards using embedded Grafana panels

### Set Up Alerts
1. Go to **Alerts** section
2. View existing alert rules
3. Create new alerts based on your metrics

### Check Insights
1. Visit the **Insights** page
2. Review cost optimization recommendations
3. Analyze resource usage patterns

## 5. Generate Sample Data

To see ObservaStack in action with sample data:

```bash
# Generate sample logs
docker compose exec vector-aggregator \
  curl -X POST http://localhost:8686/logs \
  -H "Content-Type: application/json" \
  -d '{"message": "Sample error log", "level": "error", "service": "web-app"}'

# Generate sample metrics
docker compose exec prometheus \
  curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot
```

## 6. Next Steps

Now that ObservaStack is running:

### Configure Your Environment
- [Set up authentication](../user-guide/authentication.md) with your identity provider
- [Configure data sources](configuration.md) to ingest your application data
- [Customize dashboards](../user-guide/dashboards.md) for your specific needs

### Integrate Your Applications
- **Logs**: Configure your applications to send logs to Loki endpoint: `http://localhost:3100`
- **Metrics**: Point Prometheus to scrape your application metrics
- **Traces**: Configure OpenTelemetry to send traces to Tempo: `http://localhost:3200`

### Production Deployment
- Review the [Production Setup](../deployment/production-setup.md) guide
- Use [Ansible deployment](../deployment/ansible.md) for production environments
- Configure [high availability](../deployment/kubernetes.md) with Kubernetes

## Common First Steps

### Add Your First Data Source

1. **For Logs**: Configure your application to send logs to:
   ```
   Endpoint: http://localhost:3100/loki/api/v1/push
   Format: JSON
   ```

2. **For Metrics**: Add Prometheus scrape config:
   ```yaml
   scrape_configs:
     - job_name: 'my-app'
       static_configs:
         - targets: ['my-app:8080']
   ```

3. **For Traces**: Configure OpenTelemetry:
   ```yaml
   exporters:
     otlp:
       endpoint: http://localhost:3200
   ```

### Create Your First Dashboard

1. Navigate to **Dashboards** → **Create New**
2. Add panels for your key metrics
3. Save and share with your team

### Set Up Your First Alert

1. Go to **Alerts** → **Create Alert Rule**
2. Define conditions (e.g., error rate > 5%)
3. Configure notification channels

## Troubleshooting Quick Start

### Services Not Starting?
```bash
# Check service status
docker compose ps

# View logs for specific service
docker compose logs grafana
docker compose logs prometheus
```

### Can't Access Web Interface?
- Ensure port 3000 is not in use: `netstat -tlnp | grep 3000`
- Check firewall settings
- Verify Docker containers are running: `docker compose ps`

### No Data Showing?
- Wait 1-2 minutes for services to fully initialize
- Check that sample data generation completed successfully
- Verify time range in search filters

## Getting Help

- 📚 **Full Documentation**: Continue with [Configuration](configuration.md)
- 🔧 **Troubleshooting**: See [Common Issues](../troubleshooting/common-issues.md)
- 💬 **Community**: Join [GitHub Discussions](https://github.com/observastack/observastack/discussions)
- 🐛 **Issues**: Report bugs on [GitHub Issues](https://github.com/observastack/observastack/issues)