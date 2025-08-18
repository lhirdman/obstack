# Common Issues

This guide covers the most frequently encountered issues when deploying and using ObservaStack, along with their solutions.

## Installation Issues

### Docker Compose Startup Problems

#### Issue: Services fail to start

**Symptoms:**
```bash
docker compose ps
# Shows services in "Exit 1" or "Restarting" state
```

**Common Causes & Solutions:**

1. **Port Conflicts**
   ```bash
   # Check what's using the ports
   netstat -tlnp | grep -E ':(3000|8000|9090|3100|3200)'
   
   # Kill conflicting processes or change ports in docker-compose.yml
   sudo kill -9 <PID>
   ```

2. **Insufficient Resources**
   ```bash
   # Check available memory
   free -h
   # Minimum 8GB RAM required
   
   # Check disk space
   df -h
   # Minimum 20GB free space required
   ```

3. **Docker Daemon Issues**
   ```bash
   # Restart Docker daemon
   sudo systemctl restart docker
   
   # Check Docker status
   sudo systemctl status docker
   ```

#### Issue: MinIO initialization fails

**Symptoms:**
```bash
docker compose logs mc
# Error: "mc: <ERROR> Unable to initialize new config from the provided credentials."
```

**Solution:**
```bash
# Remove existing MinIO data
docker compose down
docker volume rm docker_minio_data

# Reinitialize
docker compose --profile init up mc && docker compose --profile init down
docker compose up -d
```

### Authentication Problems

#### Issue: Keycloak not accessible

**Symptoms:**
- Cannot access http://localhost:8080
- Login redirects fail

**Solutions:**

1. **Check Keycloak startup**
   ```bash
   # View Keycloak logs
   docker compose logs keycloak
   
   # Wait for startup message
   # "Keycloak 22.0.0 started in 45.123s"
   ```

2. **Database connection issues**
   ```bash
   # Check PostgreSQL status
   docker compose logs postgres
   
   # Verify database connectivity
   docker compose exec postgres psql -U keycloak -d keycloak -c "\dt"
   ```

3. **Reset Keycloak configuration**
   ```bash
   # Stop services
   docker compose stop keycloak postgres
   
   # Remove database volume
   docker volume rm docker_postgres_data
   
   # Restart services
   docker compose up -d postgres keycloak
   ```

## Application Issues

### Search Not Working

#### Issue: No search results returned

**Symptoms:**
- Search interface loads but returns empty results
- Error messages in search responses

**Diagnostic Steps:**

1. **Check data sources connectivity**
   ```bash
   # Test Prometheus
   curl http://localhost:9090/api/v1/query?query=up
   
   # Test Loki
   curl http://localhost:3100/ready
   
   # Test Tempo
   curl http://localhost:3200/ready
   ```

2. **Verify data ingestion**
   ```bash
   # Check if metrics are being scraped
   curl http://localhost:9090/api/v1/targets
   
   # Check Loki logs
   curl "http://localhost:3100/loki/api/v1/query_range?query={job=\"docker\"}&start=$(date -d '1 hour ago' +%s)000000000&end=$(date +%s)000000000"
   ```

3. **Check BFF API connectivity**
   ```bash
   # Test BFF health
   curl http://localhost:8000/health
   
   # Test search endpoint
   curl -X POST http://localhost:8000/api/v1/search \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <token>" \
     -d '{"freeText": "test", "type": "logs"}'
   ```

#### Issue: Authentication errors in API calls

**Symptoms:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Solutions:**

1. **Check JWT token validity**
   ```bash
   # Decode JWT token (replace <token> with actual token)
   echo "<token>" | cut -d. -f2 | base64 -d | jq
   
   # Check expiration time
   echo "<token>" | cut -d. -f2 | base64 -d | jq .exp
   ```

2. **Verify Keycloak configuration**
   ```bash
   # Check Keycloak realm configuration
   curl http://localhost:8080/realms/observastack/.well-known/openid_configuration
   ```

3. **Clear browser storage**
   ```javascript
   // In browser console
   localStorage.clear();
   sessionStorage.clear();
   location.reload();
   ```

### Dashboard Issues

#### Issue: Grafana panels not loading

**Symptoms:**
- Empty dashboard panels
- "Panel plugin not found" errors
- Grafana iframe not displaying

**Solutions:**

1. **Check Grafana status**
   ```bash
   # View Grafana logs
   docker compose logs grafana
   
   # Access Grafana directly
   curl http://localhost:3001/api/health
   ```

2. **Verify data source configuration**
   ```bash
   # Check Grafana data sources
   curl -u admin:admin http://localhost:3001/api/datasources
   ```

3. **Reset Grafana configuration**
   ```bash
   # Stop Grafana
   docker compose stop grafana
   
   # Remove Grafana data
   docker volume rm docker_grafana_data
   
   # Restart Grafana (will recreate with defaults)
   docker compose up -d grafana
   ```

## Performance Issues

### Slow Query Performance

#### Issue: Search queries taking too long

**Symptoms:**
- Search requests timeout
- High CPU usage on data source containers
- Slow dashboard loading

**Diagnostic Steps:**

1. **Check resource usage**
   ```bash
   # Monitor container resources
   docker stats --no-stream
   
   # Check system resources
   top
   iostat -x 1
   ```

2. **Analyze query patterns**
   ```bash
   # Check Prometheus query logs
   docker compose logs prometheus | grep "query"
   
   # Check Loki query performance
   curl "http://localhost:3100/metrics" | grep loki_request_duration
   ```

**Solutions:**

1. **Optimize query time ranges**
   - Limit search time ranges to necessary periods
   - Use appropriate step intervals for metrics queries

2. **Increase resource limits**
   ```yaml
   # In docker-compose.yml
   services:
     prometheus:
       deploy:
         resources:
           limits:
             memory: 4G
             cpus: '2.0'
   ```

3. **Configure retention policies**
   ```yaml
   # Reduce data retention
   prometheus:
     command:
       - '--storage.tsdb.retention.time=7d'
   
   loki:
     limits_config:
       retention_period: 72h
   ```

### High Memory Usage

#### Issue: Containers consuming excessive memory

**Solutions:**

1. **Configure JVM heap sizes**
   ```yaml
   # For Java-based services
   environment:
     - JAVA_OPTS=-Xmx2g -Xms1g
   ```

2. **Implement query result caching**
   ```python
   # In BFF configuration
   CACHE_TTL = 300  # 5 minutes
   REDIS_MAX_MEMORY = "1gb"
   ```

3. **Optimize data ingestion**
   ```toml
   # In vector configuration
   [sinks.loki]
   batch.max_bytes = 1048576  # 1MB batches
   batch.timeout_secs = 5
   ```

## Data Issues

### Missing Data

#### Issue: Expected logs/metrics not appearing

**Diagnostic Steps:**

1. **Check data source configuration**
   ```bash
   # Verify Prometheus targets
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'
   
   # Check Vector log ingestion
   docker compose logs vector-aggregator | grep ERROR
   ```

2. **Verify application instrumentation**
   ```bash
   # Check if application is exposing metrics
   curl http://your-app:8080/metrics
   
   # Verify log format compatibility
   docker compose logs your-app | head -10
   ```

**Solutions:**

1. **Fix Prometheus scrape configuration**
   ```yaml
   # In prometheus/prometheus.yml
   scrape_configs:
     - job_name: 'my-app'
       static_configs:
         - targets: ['my-app:8080']
       metrics_path: '/actuator/prometheus'  # Correct path
       scrape_interval: 30s
   ```

2. **Configure log shipping**
   ```yaml
   # In application docker-compose.yml
   services:
     my-app:
       logging:
         driver: "json-file"
         options:
           max-size: "100m"
           max-file: "3"
       labels:
         - "logging=promtail"
   ```

### Data Retention Issues

#### Issue: Old data not being cleaned up

**Solutions:**

1. **Configure retention policies**
   ```yaml
   # Prometheus retention
   prometheus:
     command:
       - '--storage.tsdb.retention.time=15d'
       - '--storage.tsdb.retention.size=10GB'
   
   # Loki retention
   loki:
     limits_config:
       retention_period: 168h  # 7 days
   ```

2. **Set up automated cleanup**
   ```bash
   #!/bin/bash
   # cleanup-old-data.sh
   
   # Clean Docker logs older than 7 days
   find /var/lib/docker/containers -name "*.log" -mtime +7 -delete
   
   # Clean temporary files
   docker system prune -f --volumes --filter "until=168h"
   ```

## Network Issues

### Service Communication Problems

#### Issue: Services cannot communicate with each other

**Symptoms:**
- Connection refused errors
- DNS resolution failures
- Timeout errors between services

**Solutions:**

1. **Check Docker network configuration**
   ```bash
   # List Docker networks
   docker network ls
   
   # Inspect network configuration
   docker network inspect docker_default
   ```

2. **Verify service discovery**
   ```bash
   # Test DNS resolution between containers
   docker compose exec observastack-bff nslookup prometheus
   docker compose exec observastack-bff ping -c 3 loki
   ```

3. **Check firewall rules**
   ```bash
   # Check iptables rules
   sudo iptables -L DOCKER-USER
   
   # Temporarily disable firewall for testing
   sudo ufw disable
   ```

### External Access Issues

#### Issue: Cannot access ObservaStack from external networks

**Solutions:**

1. **Configure port binding**
   ```yaml
   # In docker-compose.yml
   services:
     observastack-frontend:
       ports:
         - "0.0.0.0:3000:3000"  # Bind to all interfaces
   ```

2. **Set up reverse proxy**
   ```nginx
   # nginx.conf
   server {
       listen 80;
       server_name observastack.example.com;
       
       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## Debugging Tools

### Log Analysis

```bash
# Centralized log viewing
docker compose logs -f --tail=100

# Service-specific logs
docker compose logs -f observastack-bff
docker compose logs -f prometheus

# Search logs for errors
docker compose logs | grep -i error

# Export logs for analysis
docker compose logs > observastack-logs.txt
```

### Health Checks

```bash
#!/bin/bash
# health-check.sh

echo "=== ObservaStack Health Check ==="

# Check service status
echo "Service Status:"
docker compose ps

# Check API endpoints
echo -e "\nAPI Health Checks:"
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:9090/-/healthy
curl -s http://localhost:3100/ready

# Check resource usage
echo -e "\nResource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check disk space
echo -e "\nDisk Usage:"
df -h | grep -E "(Filesystem|/dev/)"
```

### Performance Monitoring

```bash
# Monitor container performance
docker stats

# Check system performance
htop

# Monitor network traffic
nethogs

# Analyze disk I/O
iotop
```

## Getting Help

### Collecting Debug Information

Before seeking help, collect the following information:

```bash
#!/bin/bash
# collect-debug-info.sh

DEBUG_DIR="observastack-debug-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEBUG_DIR"

# System information
uname -a > "$DEBUG_DIR/system-info.txt"
docker --version >> "$DEBUG_DIR/system-info.txt"
docker compose version >> "$DEBUG_DIR/system-info.txt"

# Service status
docker compose ps > "$DEBUG_DIR/service-status.txt"

# Logs
docker compose logs > "$DEBUG_DIR/all-logs.txt"

# Configuration
cp docker-compose.yml "$DEBUG_DIR/"
cp .env "$DEBUG_DIR/" 2>/dev/null || true

# Resource usage
docker stats --no-stream > "$DEBUG_DIR/resource-usage.txt"

# Network information
docker network ls > "$DEBUG_DIR/networks.txt"

echo "Debug information collected in: $DEBUG_DIR"
tar czf "$DEBUG_DIR.tar.gz" "$DEBUG_DIR"
```

### Support Channels

- 📖 **Documentation**: https://observastack.github.io/docs
- 💬 **GitHub Discussions**: https://github.com/observastack/observastack/discussions
- 🐛 **Bug Reports**: https://github.com/observastack/observastack/issues
- 📧 **Community Support**: community@observastack.io

### Creating Effective Bug Reports

Include the following information:

1. **Environment Details**
   - Operating system and version
   - Docker and Docker Compose versions
   - ObservaStack version

2. **Steps to Reproduce**
   - Exact commands run
   - Configuration files used
   - Expected vs actual behavior

3. **Debug Information**
   - Relevant log excerpts
   - Error messages
   - Service status output

4. **Troubleshooting Attempted**
   - Solutions already tried
   - Workarounds discovered

## Next Steps

- [Debugging Guide](debugging.md) - Advanced debugging techniques
- [Performance Tuning](performance.md) - Optimization strategies
- [Production Setup](../deployment/production-setup.md) - Production best practices