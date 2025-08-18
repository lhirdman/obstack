# Search

ObservaStack provides a unified search interface that allows you to query logs, metrics, and traces from a single location.

## Overview

The search functionality in ObservaStack enables you to:

- Search across multiple data sources simultaneously
- Filter results by time range, service, and other attributes
- Correlate events across logs, metrics, and traces
- Save and share search queries
- Export search results for further analysis

## Getting Started

### Basic Search

1. Navigate to the **Search** page in ObservaStack
2. Enter your search query in the search box
3. Select the data type (Logs, Metrics, Traces, or All)
4. Choose your time range
5. Click **Search** to execute the query

### Search Syntax

ObservaStack supports various search syntaxes depending on the data source:

#### Log Search
```
# Simple text search
error

# Field-based search
level:error service:web-app

# Regular expressions
message:/timeout.*connection/

# Time-based search
@timestamp:[now-1h TO now]
```

#### Metric Search
```
# Metric name search
cpu_usage

# Label-based search
cpu_usage{instance="web-01"}

# Aggregation queries
rate(http_requests_total[5m])
```

#### Trace Search
```
# Service name search
service.name:web-app

# Operation search
operation.name:GET /api/users

# Duration search
duration:>1s
```

## Advanced Features

### Cross-Signal Correlation

ObservaStack automatically correlates related events across different data sources:

- **Trace to Logs**: Click on a trace span to see related log entries
- **Logs to Metrics**: View metric trends for the time period of log events
- **Metrics to Traces**: Drill down from metric anomalies to related traces

### Saved Searches

Save frequently used searches for quick access:

1. Execute a search query
2. Click **Save Search**
3. Provide a name and description
4. Choose sharing permissions (private, team, or public)

### Search Filters

Use filters to narrow down search results:

- **Time Range**: Absolute or relative time ranges
- **Services**: Filter by specific services or applications
- **Severity**: Filter logs by severity level
- **Status Codes**: Filter by HTTP status codes
- **Custom Labels**: Filter by any custom labels or tags

## Search Tips

### Performance Optimization

- **Use specific time ranges** to reduce query scope
- **Include service filters** when searching across multiple services
- **Use indexed fields** for faster query performance
- **Limit result count** for large datasets

### Query Examples

#### Finding Errors
```
# All errors in the last hour
level:error AND @timestamp:[now-1h TO now]

# Errors from specific service
level:error AND service:payment-service

# HTTP 5xx errors
status_code:[500 TO 599]
```

#### Performance Analysis
```
# Slow requests (traces)
duration:>2s AND service.name:api-gateway

# High CPU usage (metrics)
cpu_usage > 80

# Memory leaks (logs)
message:"OutOfMemoryError" OR message:"memory leak"
```

#### Security Monitoring
```
# Failed login attempts
message:"authentication failed" OR message:"login failed"

# Suspicious activity
source_ip:NOT (10.0.0.0/8 OR 192.168.0.0/16)

# SQL injection attempts
message:/SELECT.*FROM.*WHERE/i
```

## Integration with Dashboards

Search results can be used to create dashboard panels:

1. Execute a search query
2. Click **Add to Dashboard**
3. Choose an existing dashboard or create a new one
4. Configure the panel visualization

## API Access

Search functionality is also available via REST API:

```bash
# Search logs
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "freeText": "error",
    "type": "logs",
    "timeRange": {
      "start": "2025-08-16T00:00:00Z",
      "end": "2025-08-16T23:59:59Z"
    }
  }'
```

## Troubleshooting

### No Results Returned

- Verify the time range includes the expected data
- Check that the search syntax is correct
- Ensure you have permissions to access the data
- Verify that data is being ingested properly

### Slow Search Performance

- Reduce the time range of your search
- Add more specific filters to narrow results
- Check system resource usage
- Consider optimizing data retention policies

## Next Steps

- [Set up alerts](alerts.md) based on search queries
- [Create dashboards](dashboards.md) with search results
- [Configure data sources](../getting-started/configuration.md) for better search performance