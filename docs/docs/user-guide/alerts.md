# Alerts

ObservaStack provides comprehensive alerting capabilities to help you stay informed about critical issues in your infrastructure and applications.

## Overview

The alerting system in ObservaStack includes:

- **Multi-source alerts** from Prometheus, Loki, and custom sources
- **Intelligent routing** based on severity and service
- **Escalation policies** for critical alerts
- **Notification channels** including email, Slack, PagerDuty, and webhooks
- **Alert correlation** to reduce noise and identify root causes

## Alert Types

### Metric-Based Alerts

Monitor metrics and trigger alerts based on thresholds:

```yaml
# High CPU usage alert
- alert: HighCPUUsage
  expr: cpu_usage > 80
  for: 5m
  labels:
    severity: warning
    service: infrastructure
  annotations:
    summary: "High CPU usage detected"
    description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"
```

### Log-Based Alerts

Create alerts based on log patterns:

```yaml
# Error rate alert
- alert: HighErrorRate
  expr: rate(log_entries{level="error"}[5m]) > 10
  for: 2m
  labels:
    severity: critical
    service: application
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }} errors/second"
```

### Trace-Based Alerts

Monitor distributed traces for performance issues:

```yaml
# High latency alert
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(trace_duration_bucket[5m])) > 2
  for: 3m
  labels:
    severity: warning
    service: api
  annotations:
    summary: "High latency detected"
    description: "95th percentile latency is {{ $value }}s"
```

## Creating Alerts

### Using the Web Interface

1. Navigate to **Alerts** → **Create Alert Rule**
2. Choose the alert type (Metric, Log, or Trace)
3. Define the query and conditions
4. Set thresholds and evaluation intervals
5. Configure labels and annotations
6. Choose notification channels
7. Save the alert rule

### Using Configuration Files

Create alert rules in YAML format:

```yaml
# alerts/application-alerts.yml
groups:
  - name: application.rules
    rules:
      - alert: ApplicationDown
        expr: up{job="my-application"} == 0
        for: 1m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "Application {{ $labels.instance }} is down"
          description: "Application has been down for more than 1 minute"
          runbook_url: "https://wiki.company.com/runbooks/app-down"

      - alert: HighMemoryUsage
        expr: memory_usage_percent > 90
        for: 5m
        labels:
          severity: warning
          team: infrastructure
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value }}%"
```

## Alert Routing

### Routing Rules

Configure how alerts are routed to different teams:

```yaml
# alertmanager.yml
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 0s
      repeat_interval: 5m
    
    - match:
        team: backend
      receiver: 'backend-team'
    
    - match:
        team: frontend
      receiver: 'frontend-team'
```

### Notification Channels

#### Email Notifications

```yaml
receivers:
  - name: 'email-alerts'
    email_configs:
      - to: 'alerts@company.com'
        from: 'observastack@company.com'
        smarthost: 'smtp.company.com:587'
        auth_username: 'observastack@company.com'
        auth_password: 'password'
        subject: '[ALERT] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Labels: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
          {{ end }}
```

#### Slack Integration

```yaml
receivers:
  - name: 'slack-alerts'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        title: 'ObservaStack Alert'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Description:* {{ .Annotations.description }}
          *Severity:* {{ .Labels.severity }}
          {{ end }}
```

#### PagerDuty Integration

```yaml
receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        severity: '{{ .CommonLabels.severity }}'
```

## Alert Management

### Alert States

Alerts can be in one of several states:

- **Inactive**: Condition is not met
- **Pending**: Condition is met but waiting for `for` duration
- **Firing**: Alert is active and notifications are being sent
- **Resolved**: Alert condition is no longer met

### Silencing Alerts

Temporarily silence alerts during maintenance:

```bash
# Silence alerts for maintenance window
curl -X POST http://localhost:9093/api/v1/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {
        "name": "instance",
        "value": "web-01",
        "isRegex": false
      }
    ],
    "startsAt": "2025-08-16T02:00:00Z",
    "endsAt": "2025-08-16T04:00:00Z",
    "createdBy": "admin",
    "comment": "Scheduled maintenance"
  }'
```

### Alert Inhibition

Prevent lower-priority alerts when higher-priority ones are firing:

```yaml
# Inhibit rules
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['instance', 'service']
```

## Advanced Features

### Alert Correlation

ObservaStack automatically correlates related alerts:

- **Service-based correlation**: Group alerts by service or application
- **Time-based correlation**: Identify alerts that occur together
- **Dependency correlation**: Link alerts based on service dependencies

### Alert Analytics

View alert trends and patterns:

- **Alert frequency**: How often alerts fire
- **Mean time to resolution**: Average time to resolve alerts
- **Alert distribution**: Breakdown by service, severity, and team
- **Escalation patterns**: How often alerts escalate

### Custom Alert Actions

Define custom actions for alert responses:

```yaml
# Custom webhook action
receivers:
  - name: 'custom-webhook'
    webhook_configs:
      - url: 'http://localhost:8080/webhook/alert'
        http_config:
          basic_auth:
            username: 'webhook_user'
            password: 'webhook_password'
```

## Best Practices

### Alert Design

- **Use meaningful names** that describe the problem
- **Include context** in alert descriptions
- **Set appropriate thresholds** to avoid false positives
- **Use labels** for routing and grouping
- **Include runbook links** for resolution steps

### Notification Strategy

- **Route by severity**: Critical alerts to on-call, warnings to team channels
- **Avoid alert fatigue**: Don't over-alert on non-critical issues
- **Use escalation**: Escalate unacknowledged critical alerts
- **Group related alerts**: Reduce noise by grouping similar alerts

### Testing Alerts

```bash
# Test alert rule syntax
promtool check rules alerts/application-alerts.yml

# Test alertmanager configuration
amtool config check alertmanager.yml

# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert"
    }
  }]'
```

## Troubleshooting

### Alerts Not Firing

- Check that the metric/log data exists
- Verify the alert rule syntax
- Ensure the evaluation interval is appropriate
- Check Prometheus/Alertmanager logs

### Missing Notifications

- Verify notification channel configuration
- Check routing rules and matchers
- Ensure the receiver is configured correctly
- Test notification channels independently

### Alert Fatigue

- Review alert thresholds and reduce false positives
- Implement proper alert grouping and inhibition
- Use different severity levels appropriately
- Consider alert correlation and deduplication

## Integration with Other Tools

### Grafana Integration

Link alerts to Grafana dashboards:

```yaml
annotations:
  dashboard_url: "http://grafana:3000/d/dashboard-id"
  panel_url: "http://grafana:3000/d/dashboard-id?panelId=1"
```

### Incident Management

Integrate with incident management tools:

- **ServiceNow**: Create incidents for critical alerts
- **Jira**: Create tickets for alert resolution tracking
- **Opsgenie**: Advanced alert routing and escalation

## Next Steps

- [Configure dashboards](dashboards.md) to visualize alert trends
- [Set up insights](insights.md) to analyze alert patterns
- [Learn about troubleshooting](../troubleshooting/common-issues.md) alert issues