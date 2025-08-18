# API Reference

ObservaStack provides a comprehensive REST API for programmatic access to all platform features. This reference covers all available endpoints, request/response formats, and authentication requirements.

## Base URL and Versioning

```
Base URL: http://localhost:8000/api/v1
Content-Type: application/json
```

All API endpoints are versioned and require authentication via JWT tokens.

## Authentication

### Obtaining Access Tokens

<span class="api-method api-method--post">POST</span> `/auth/login`

Authenticate and receive a JWT access token.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Token Refresh

<span class="api-method api-method--post">POST</span> `/auth/refresh`

Refresh an expired access token using a refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Using Tokens

Include the access token in the Authorization header:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Search API

### Unified Search

<span class="api-method api-method--post">POST</span> `/search`

Perform unified search across logs, metrics, and traces.

**Request Body:**
```json
{
  "freeText": "error",
  "type": "logs",
  "timeRange": {
    "start": "2025-08-16T00:00:00Z",
    "end": "2025-08-16T23:59:59Z"
  },
  "filters": {
    "service": ["web-app", "api-gateway"],
    "level": ["error", "warning"]
  },
  "limit": 100,
  "offset": 0
}
```

**Response:**
```json
{
  "items": [
    {
      "id": "log-123",
      "timestamp": "2025-08-16T10:30:00Z",
      "message": "Database connection error",
      "level": "error",
      "service": "web-app",
      "source": "logs"
    }
  ],
  "stats": {
    "total": 1,
    "logs": 1,
    "metrics": 0,
    "traces": 0
  },
  "facets": {
    "service": {
      "web-app": 1
    },
    "level": {
      "error": 1
    }
  }
}
```

### Log Search

<span class="api-method api-method--post">POST</span> `/search/logs`

Search specifically in log data.

**Request Body:**
```json
{
  "query": "level:error AND service:web-app",
  "timeRange": {
    "start": "2025-08-16T00:00:00Z",
    "end": "2025-08-16T23:59:59Z"
  },
  "limit": 100
}
```

### Metric Search

<span class="api-method api-method--post">POST</span> `/search/metrics`

Query metric data with PromQL.

**Request Body:**
```json
{
  "query": "rate(http_requests_total[5m])",
  "timeRange": {
    "start": "2025-08-16T00:00:00Z",
    "end": "2025-08-16T23:59:59Z"
  },
  "step": "30s"
}
```

### Trace Search

<span class="api-method api-method--post">POST</span> `/search/traces`

Search distributed traces.

**Request Body:**
```json
{
  "serviceName": "web-app",
  "operationName": "GET /api/users",
  "minDuration": "100ms",
  "maxDuration": "5s",
  "timeRange": {
    "start": "2025-08-16T00:00:00Z",
    "end": "2025-08-16T23:59:59Z"
  }
}
```

## Alerts API

### List Alerts

<span class="api-method api-method--get">GET</span> `/alerts`

Retrieve active alerts for the current tenant.

**Query Parameters:**
- `status` (optional): Filter by alert status (active, resolved, silenced)
- `severity` (optional): Filter by severity (critical, warning, info)
- `service` (optional): Filter by service name

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert-123",
      "name": "HighCPUUsage",
      "status": "firing",
      "severity": "warning",
      "service": "web-app",
      "message": "CPU usage is 85%",
      "startsAt": "2025-08-16T10:00:00Z",
      "endsAt": null,
      "labels": {
        "instance": "web-01",
        "job": "web-app"
      },
      "annotations": {
        "summary": "High CPU usage detected",
        "description": "CPU usage is 85% on web-01"
      }
    }
  ],
  "total": 1
}
```

### Create Alert Rule

<span class="api-method api-method--post">POST</span> `/alerts/rules`

Create a new alert rule.

**Request Body:**
```json
{
  "name": "HighMemoryUsage",
  "expr": "memory_usage_percent > 90",
  "for": "5m",
  "labels": {
    "severity": "critical",
    "team": "infrastructure"
  },
  "annotations": {
    "summary": "High memory usage on {{ $labels.instance }}",
    "description": "Memory usage is {{ $value }}%"
  }
}
```

### Silence Alert

<span class="api-method api-method--post">POST</span> `/alerts/silences`

Create an alert silence.

**Request Body:**
```json
{
  "matchers": [
    {
      "name": "alertname",
      "value": "HighCPUUsage",
      "isRegex": false
    }
  ],
  "startsAt": "2025-08-16T12:00:00Z",
  "endsAt": "2025-08-16T14:00:00Z",
  "comment": "Scheduled maintenance",
  "createdBy": "admin"
}
```

## Dashboards API

### List Dashboards

<span class="api-method api-method--get">GET</span> `/dashboards`

Get all dashboards accessible to the current user.

**Response:**
```json
{
  "dashboards": [
    {
      "id": "dashboard-123",
      "title": "System Overview",
      "description": "High-level system metrics",
      "tags": ["infrastructure", "overview"],
      "folder": "Infrastructure",
      "url": "/d/dashboard-123",
      "created": "2025-08-16T09:00:00Z",
      "updated": "2025-08-16T10:00:00Z"
    }
  ]
}
```

### Get Dashboard

<span class="api-method api-method--get">GET</span> `/dashboards/{id}`

Retrieve a specific dashboard configuration.

**Response:**
```json
{
  "dashboard": {
    "id": "dashboard-123",
    "title": "System Overview",
    "panels": [
      {
        "id": 1,
        "title": "CPU Usage",
        "type": "timeseries",
        "targets": [
          {
            "expr": "100 - (avg(irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    }
  }
}
```

### Create Dashboard

<span class="api-method api-method--post">POST</span> `/dashboards`

Create a new dashboard.

**Request Body:**
```json
{
  "title": "My Custom Dashboard",
  "description": "Custom metrics dashboard",
  "tags": ["custom", "metrics"],
  "folder": "Custom",
  "dashboard": {
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## Insights API

### Get Insights

<span class="api-method api-method--get">GET</span> `/insights`

Retrieve insights and recommendations.

**Query Parameters:**
- `category` (optional): Filter by category (cost, performance, security)
- `timeRange` (optional): Time range for analysis

**Response:**
```json
{
  "insights": [
    {
      "id": "insight-123",
      "category": "cost",
      "type": "storage_optimization",
      "title": "Reduce log retention period",
      "description": "Logs older than 7 days account for 60% of storage costs",
      "impact": "high",
      "effort": "low",
      "savings": {
        "amount": 1200,
        "currency": "USD",
        "period": "monthly"
      },
      "recommendation": "Reduce log retention from 30 days to 7 days for non-critical services"
    }
  ]
}
```

### Get Cost Analysis

<span class="api-method api-method--get">GET</span> `/insights/cost`

Get detailed cost analysis and optimization recommendations.

**Response:**
```json
{
  "totalCost": {
    "amount": 5000,
    "currency": "USD",
    "period": "monthly"
  },
  "breakdown": {
    "storage": 2000,
    "compute": 2500,
    "network": 500
  },
  "trends": {
    "growth": 0.15,
    "period": "monthly"
  },
  "recommendations": [
    {
      "type": "storage_optimization",
      "savings": 600,
      "description": "Optimize data retention policies"
    }
  ]
}
```

## User Management API

### Get Current User

<span class="api-method api-method--get">GET</span> `/user/profile`

Get current user profile information.

**Response:**
```json
{
  "user": {
    "id": "user-123",
    "username": "john.doe",
    "email": "john.doe@company.com",
    "firstName": "John",
    "lastName": "Doe",
    "tenantId": "acme-corp",
    "roles": ["observastack-user"],
    "permissions": ["search", "view_dashboards"],
    "lastLogin": "2025-08-16T09:00:00Z"
  }
}
```

### Update User Profile

<span class="api-method api-method--put">PUT</span> `/user/profile`

Update current user profile.

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@company.com",
  "preferences": {
    "theme": "dark",
    "timezone": "UTC",
    "language": "en"
  }
}
```

## Admin API

### List Users (Admin Only)

<span class="api-method api-method--get">GET</span> `/admin/users`

List all users (requires admin role).

**Response:**
```json
{
  "users": [
    {
      "id": "user-123",
      "username": "john.doe",
      "email": "john.doe@company.com",
      "tenantId": "acme-corp",
      "roles": ["observastack-user"],
      "active": true,
      "created": "2025-08-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### List Tenants (Admin Only)

<span class="api-method api-method--get">GET</span> `/admin/tenants`

List all tenants (requires admin role).

**Response:**
```json
{
  "tenants": [
    {
      "id": "acme-corp",
      "name": "ACME Corporation",
      "domain": "acme.com",
      "active": true,
      "userCount": 25,
      "created": "2025-08-01T00:00:00Z"
    }
  ]
}
```

## Health and Status API

### Health Check

<span class="api-method api-method--get">GET</span> `/health`

Check system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-16T10:30:00Z",
  "checks": {
    "database": "healthy",
    "prometheus": "healthy",
    "loki": "healthy",
    "tempo": "healthy",
    "keycloak": "healthy",
    "redis": "healthy"
  },
  "version": "1.0.0"
}
```

### System Status

<span class="api-method api-method--get">GET</span> `/status`

Get detailed system status information.

**Response:**
```json
{
  "system": {
    "uptime": "72h30m15s",
    "version": "1.0.0",
    "environment": "production"
  },
  "metrics": {
    "activeUsers": 150,
    "requestsPerSecond": 45.2,
    "averageResponseTime": "120ms"
  },
  "resources": {
    "cpuUsage": 65.5,
    "memoryUsage": 78.2,
    "diskUsage": 45.8
  }
}
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "timeRange.start",
        "message": "Start time cannot be in the future"
      }
    ],
    "timestamp": "2025-08-16T10:30:00Z",
    "requestId": "req-123456"
  }
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Authentication**: 5 requests per minute
- **Search**: 20 requests per minute
- **General API**: 100 requests per minute

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1692123456
```

## SDK and Client Libraries

### Python SDK

```python
from observastack import ObservaStackClient

client = ObservaStackClient(
    base_url="http://localhost:8000",
    token="your-jwt-token"
)

# Search logs
results = client.search.logs(
    query="level:error",
    time_range={"start": "2025-08-16T00:00:00Z", "end": "2025-08-16T23:59:59Z"}
)

# Get alerts
alerts = client.alerts.list(status="firing")

# Create dashboard
dashboard = client.dashboards.create({
    "title": "My Dashboard",
    "panels": [...]
})
```

### JavaScript SDK

```javascript
import { ObservaStackClient } from '@observastack/client';

const client = new ObservaStackClient({
  baseURL: 'http://localhost:8000',
  token: 'your-jwt-token'
});

// Search logs
const results = await client.search.logs({
  query: 'level:error',
  timeRange: {
    start: '2025-08-16T00:00:00Z',
    end: '2025-08-16T23:59:59Z'
  }
});

// Get alerts
const alerts = await client.alerts.list({ status: 'firing' });
```

## OpenAPI Specification

The complete API specification is available in OpenAPI 3.0 format:

- **Interactive Documentation**: http://localhost:8000/docs
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **ReDoc Documentation**: http://localhost:8000/redoc

## Next Steps

- [Learn about authentication](../user-guide/authentication.md)
- [Explore the architecture](architecture.md)
- [Set up development environment](contributing.md)