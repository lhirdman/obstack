# Dashboards

ObservaStack provides powerful dashboard capabilities through embedded Grafana panels, allowing you to create custom visualizations and monitor your systems effectively.

## Overview

Dashboard features include:

- **Embedded Grafana panels** with seamless integration
- **Multi-tenant dashboard isolation** for secure data separation
- **Custom branding** per tenant organization
- **Real-time data visualization** with automatic refresh
- **Interactive drill-down** capabilities across data sources

## Getting Started

### Accessing Dashboards

1. Navigate to **Dashboards** in the ObservaStack interface
2. Browse existing dashboards or create new ones
3. Click on any dashboard to view detailed metrics
4. Use the time range selector to adjust the viewing period

### Pre-built Dashboards

ObservaStack includes several pre-built dashboards:

#### System Overview
- **CPU, Memory, and Disk utilization** across all hosts
- **Network traffic** and bandwidth usage
- **System load** and performance metrics
- **Service health** and availability status

#### Application Performance
- **Response times** and latency percentiles
- **Request rates** and throughput metrics
- **Error rates** and failure analysis
- **Database performance** and query metrics

#### Infrastructure Monitoring
- **Container metrics** (Docker, Kubernetes)
- **Load balancer** performance and health
- **Storage utilization** and I/O metrics
- **Network connectivity** and latency

## Creating Custom Dashboards

### Dashboard Builder

Use the integrated dashboard builder:

1. Click **Create Dashboard** in the Dashboards section
2. Choose a template or start from scratch
3. Add panels using the panel editor
4. Configure data sources and queries
5. Customize visualization settings
6. Save and share your dashboard

### Panel Types

#### Time Series Graphs
```json
{
  "type": "timeseries",
  "title": "CPU Usage",
  "targets": [
    {
      "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
      "legendFormat": "CPU Usage %"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "min": 0,
      "max": 100
    }
  }
}
```

#### Single Stat Panels
```json
{
  "type": "stat",
  "title": "Total Requests",
  "targets": [
    {
      "expr": "sum(rate(http_requests_total[5m]))",
      "legendFormat": "Requests/sec"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "reqps",
      "color": {
        "mode": "thresholds"
      },
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 100},
          {"color": "red", "value": 500}
        ]
      }
    }
  }
}
```

#### Table Panels
```json
{
  "type": "table",
  "title": "Service Status",
  "targets": [
    {
      "expr": "up",
      "format": "table",
      "instant": true
    }
  ],
  "transformations": [
    {
      "id": "organize",
      "options": {
        "excludeByName": {
          "Time": true,
          "__name__": true
        },
        "renameByName": {
          "Value": "Status",
          "instance": "Instance",
          "job": "Service"
        }
      }
    }
  ]
}
```

### Advanced Visualizations

#### Heatmaps
```json
{
  "type": "heatmap",
  "title": "Response Time Distribution",
  "targets": [
    {
      "expr": "rate(http_request_duration_seconds_bucket[5m])",
      "format": "heatmap",
      "legendFormat": "{{le}}"
    }
  ],
  "heatmap": {
    "xAxis": {
      "show": true
    },
    "yAxis": {
      "show": true,
      "logBase": 2
    }
  }
}
```

#### Gauge Panels
```json
{
  "type": "gauge",
  "title": "Memory Usage",
  "targets": [
    {
      "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "min": 0,
      "max": 100,
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 70},
          {"color": "red", "value": 90}
        ]
      }
    }
  }
}
```

## Dashboard Configuration

### Variables and Templating

Create dynamic dashboards using variables:

```json
{
  "templating": {
    "list": [
      {
        "name": "service",
        "type": "query",
        "query": "label_values(up, job)",
        "refresh": 1,
        "includeAll": true,
        "multi": true
      },
      {
        "name": "instance",
        "type": "query",
        "query": "label_values(up{job=\"$service\"}, instance)",
        "refresh": 2,
        "includeAll": true,
        "multi": true
      }
    ]
  }
}
```

### Time Range Controls

Configure time range options:

```json
{
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {
    "refresh_intervals": ["5s", "10s", "30s", "1m", "5m", "15m", "30m", "1h"],
    "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"]
  }
}
```

### Auto-refresh Settings

Configure automatic dashboard refresh:

```json
{
  "refresh": "30s",
  "autoRefresh": true,
  "refreshOnLoad": true
}
```

## Multi-Tenant Dashboards

### Tenant Isolation

Dashboards are automatically filtered by tenant:

```json
{
  "targets": [
    {
      "expr": "cpu_usage{tenant_id=\"$__tenant_id\"}",
      "legendFormat": "CPU Usage"
    }
  ]
}
```

### Tenant Branding

Customize dashboard appearance per tenant:

```json
{
  "style": {
    "theme": "custom",
    "logo": "$__tenant_logo",
    "primaryColor": "$__tenant_primary_color",
    "secondaryColor": "$__tenant_secondary_color"
  }
}
```

### Shared Dashboards

Configure dashboard sharing permissions:

```json
{
  "permissions": [
    {
      "role": "Admin",
      "permission": "Edit"
    },
    {
      "role": "User",
      "permission": "View"
    },
    {
      "tenant": "shared",
      "permission": "View"
    }
  ]
}
```

## Dashboard Management

### Organizing Dashboards

#### Folders and Tags
- **Create folders** to organize related dashboards
- **Use tags** for easy searching and filtering
- **Set favorites** for quick access to important dashboards
- **Create playlists** for rotating dashboard displays

#### Dashboard Lists
```json
{
  "dashboardList": {
    "folders": [
      {
        "name": "Infrastructure",
        "dashboards": ["system-overview", "network-monitoring"]
      },
      {
        "name": "Applications",
        "dashboards": ["app-performance", "error-tracking"]
      }
    ],
    "tags": ["production", "monitoring", "alerts"]
  }
}
```

### Version Control

Track dashboard changes:

- **Version history** with change tracking
- **Rollback capabilities** to previous versions
- **Change annotations** with author and description
- **Export/import** functionality for backup and migration

### Dashboard Alerts

Create alerts based on dashboard panels:

```json
{
  "alert": {
    "name": "High CPU Alert",
    "message": "CPU usage is above 80%",
    "frequency": "10s",
    "conditions": [
      {
        "query": {
          "queryType": "",
          "refId": "A"
        },
        "reducer": {
          "type": "last",
          "params": []
        },
        "evaluator": {
          "params": [80],
          "type": "gt"
        }
      }
    ],
    "executionErrorState": "alerting",
    "noDataState": "no_data",
    "for": "5m"
  }
}
```

## Integration Features

### Drill-Down Navigation

Configure drill-down links between dashboards:

```json
{
  "links": [
    {
      "title": "Service Details",
      "url": "/d/service-details?var-service=$service&var-instance=$instance",
      "type": "dashboard"
    },
    {
      "title": "View Logs",
      "url": "/explore?left={\"datasource\":\"loki\",\"queries\":[{\"expr\":\"{service=\\\"$service\\\"}\"}]}",
      "type": "link"
    }
  ]
}
```

### Data Source Integration

Connect to multiple data sources:

```json
{
  "datasources": [
    {
      "name": "Prometheus",
      "type": "prometheus",
      "url": "http://prometheus:9090"
    },
    {
      "name": "Loki",
      "type": "loki",
      "url": "http://loki:3100"
    },
    {
      "name": "Tempo",
      "type": "tempo",
      "url": "http://tempo:3200"
    }
  ]
}
```

### External Integrations

Embed external content:

```json
{
  "type": "text",
  "title": "External Dashboard",
  "content": "<iframe src=\"https://external-dashboard.com/embed\" width=\"100%\" height=\"400px\"></iframe>"
}
```

## Performance Optimization

### Query Optimization

Optimize dashboard queries for better performance:

- **Use appropriate time ranges** to limit data scope
- **Implement query caching** for frequently accessed data
- **Use recording rules** for complex calculations
- **Optimize panel refresh rates** based on data update frequency

### Resource Management

Manage dashboard resource usage:

```json
{
  "performance": {
    "maxDataPoints": 1000,
    "queryTimeout": "30s",
    "cacheTimeout": "5m",
    "refreshRate": "30s"
  }
}
```

## Best Practices

### Dashboard Design

- **Keep it simple**: Focus on the most important metrics
- **Use consistent colors** and styling across panels
- **Provide context**: Include descriptions and units
- **Group related metrics** logically
- **Use appropriate visualizations** for different data types

### Performance Guidelines

- **Limit the number of panels** per dashboard (recommended: &lt;20)
- **Use appropriate time ranges** for your use case
- **Implement proper caching** strategies
- **Monitor dashboard load times** and optimize as needed

### Maintenance

- **Regular reviews**: Periodically review and update dashboards
- **Remove unused dashboards** to reduce clutter
- **Update queries** when metrics or labels change
- **Document dashboard purpose** and usage

## Troubleshooting

### Dashboard Loading Issues

- Check data source connectivity and health
- Verify query syntax and data availability
- Review browser console for JavaScript errors
- Check network connectivity and firewall rules

### Performance Problems

- Reduce the number of panels or time range
- Optimize queries and use recording rules
- Check system resources and scaling
- Review caching configuration

### Data Display Issues

- Verify data source configuration
- Check query syntax and metric names
- Review time range and data availability
- Validate panel configuration and field mappings

## Next Steps

- [Set up alerts](alerts.md) based on dashboard metrics
- [Configure insights](insights.md) for dashboard optimization
- [Learn about troubleshooting](../troubleshooting/common-issues.md) dashboard issues