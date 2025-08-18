# Extending ObservaStack

ObservaStack is designed to be extensible and customizable. This guide covers how to add new features, integrate with external systems, and customize the platform for your specific needs.

## Extension Points

ObservaStack provides several extension points:

- **Data Source Integrations**: Add support for new observability tools
- **Authentication Providers**: Integrate with different identity systems
- **Notification Channels**: Add new alert notification methods
- **Dashboard Widgets**: Create custom visualization components
- **API Extensions**: Add new endpoints and functionality
- **Plugins**: Develop modular extensions

## Data Source Integration

### Adding a New Data Source

To integrate a new data source (e.g., Elasticsearch, InfluxDB):

#### 1. Create Client Interface

```python
# app/services/elasticsearch_client.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import httpx

class DataSourceClient(ABC):
    @abstractmethod
    async def query(self, query: str, time_range: dict) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass

class ElasticsearchClient(DataSourceClient):
    def __init__(self, url: str, username: str = None, password: str = None):
        self.url = url
        self.auth = (username, password) if username and password else None
        self.client = httpx.AsyncClient()
    
    async def query(self, query: str, time_range: dict) -> List[Dict[str, Any]]:
        """Execute Elasticsearch query."""
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"query_string": {"query": query}},
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": time_range["start"],
                                    "lte": time_range["end"]
                                }
                            }
                        }
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": 1000
        }
        
        response = await self.client.post(
            f"{self.url}/_search",
            json=search_body,
            auth=self.auth
        )
        response.raise_for_status()
        
        data = response.json()
        return [hit["_source"] for hit in data["hits"]["hits"]]
    
    async def health_check(self) -> bool:
        """Check Elasticsearch cluster health."""
        try:
            response = await self.client.get(f"{self.url}/_cluster/health")
            return response.status_code == 200
        except Exception:
            return False
```

#### 2. Update Search Service

```python
# app/services/search_service.py
from .elasticsearch_client import ElasticsearchClient

class SearchService:
    def __init__(
        self,
        loki_client: LokiClient,
        prometheus_client: PrometheusClient,
        elasticsearch_client: ElasticsearchClient = None
    ):
        self.loki = loki_client
        self.prometheus = prometheus_client
        self.elasticsearch = elasticsearch_client
    
    async def search(self, query: SearchQuery, tenant_id: str) -> SearchResults:
        """Search across all configured data sources."""
        results = []
        
        # Search Loki
        if self.loki:
            loki_results = await self._search_loki(query, tenant_id)
            results.extend(loki_results)
        
        # Search Elasticsearch
        if self.elasticsearch and query.type in ["logs", "all"]:
            es_results = await self._search_elasticsearch(query, tenant_id)
            results.extend(es_results)
        
        return SearchResults(
            items=results,
            stats=self._calculate_stats(results)
        )
    
    async def _search_elasticsearch(self, query: SearchQuery, tenant_id: str) -> List[Dict]:
        """Search Elasticsearch with tenant filtering."""
        # Add tenant filter to query
        tenant_query = f"({query.free_text}) AND tenant_id:{tenant_id}"
        
        raw_results = await self.elasticsearch.query(
            tenant_query,
            {
                "start": query.time_range.start,
                "end": query.time_range.end
            }
        )
        
        # Transform to standard format
        return [
            {
                "id": result.get("_id", ""),
                "timestamp": result.get("@timestamp"),
                "message": result.get("message", ""),
                "level": result.get("level", "info"),
                "service": result.get("service", "unknown"),
                "source": "elasticsearch"
            }
            for result in raw_results
        ]
```

#### 3. Configuration

```python
# app/core/config.py
class Settings(BaseSettings):
    # Existing settings...
    
    # Elasticsearch configuration
    elasticsearch_enabled: bool = False
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_username: str = ""
    elasticsearch_password: str = ""
```

#### 4. Dependency Injection

```python
# app/api/dependencies.py
from app.services.elasticsearch_client import ElasticsearchClient

async def get_elasticsearch_client() -> ElasticsearchClient:
    if not settings.elasticsearch_enabled:
        return None
    
    return ElasticsearchClient(
        url=settings.elasticsearch_url,
        username=settings.elasticsearch_username,
        password=settings.elasticsearch_password
    )

async def get_search_service(
    loki_client: LokiClient = Depends(get_loki_client),
    prometheus_client: PrometheusClient = Depends(get_prometheus_client),
    elasticsearch_client: ElasticsearchClient = Depends(get_elasticsearch_client)
) -> SearchService:
    return SearchService(loki_client, prometheus_client, elasticsearch_client)
```

## Authentication Provider Integration

### Adding LDAP Authentication

```python
# app/auth/ldap_provider.py
import ldap3
from typing import Optional
from app.models.user import User
from app.auth.base import AuthProvider

class LDAPAuthProvider(AuthProvider):
    def __init__(self, server_url: str, base_dn: str, user_dn_template: str):
        self.server_url = server_url
        self.base_dn = base_dn
        self.user_dn_template = user_dn_template
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user against LDAP."""
        try:
            server = ldap3.Server(self.server_url)
            user_dn = self.user_dn_template.format(username=username)
            
            conn = ldap3.Connection(server, user_dn, password)
            if not conn.bind():
                return None
            
            # Search for user attributes
            conn.search(
                search_base=self.base_dn,
                search_filter=f"(uid={username})",
                attributes=['cn', 'mail', 'ou']
            )
            
            if not conn.entries:
                return None
            
            entry = conn.entries[0]
            
            return User(
                username=username,
                email=str(entry.mail),
                first_name=str(entry.cn).split()[0],
                last_name=str(entry.cn).split()[-1],
                tenant_id=self._map_ou_to_tenant(str(entry.ou))
            )
            
        except Exception as e:
            logger.error(f"LDAP authentication failed: {e}")
            return None
    
    def _map_ou_to_tenant(self, ou: str) -> str:
        """Map LDAP organizational unit to tenant ID."""
        ou_tenant_mapping = {
            "engineering": "eng-tenant",
            "sales": "sales-tenant",
            "support": "support-tenant"
        }
        return ou_tenant_mapping.get(ou.lower(), "default")
```

## Custom Notification Channels

### Adding Microsoft Teams Integration

```python
# app/services/teams_notifier.py
import httpx
from typing import Dict, Any
from app.models.alert import Alert
from app.services.base_notifier import BaseNotifier

class TeamsNotifier(BaseNotifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.client = httpx.AsyncClient()
    
    async def send_notification(self, alert: Alert, context: Dict[str, Any] = None):
        """Send alert notification to Microsoft Teams."""
        
        # Determine color based on severity
        color_map = {
            "critical": "FF0000",  # Red
            "warning": "FFA500",   # Orange
            "info": "0078D4"       # Blue
        }
        
        color = color_map.get(alert.severity, "808080")
        
        # Create Teams message card
        message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"ObservaStack Alert: {alert.name}",
            "sections": [
                {
                    "activityTitle": f"🚨 {alert.name}",
                    "activitySubtitle": f"Severity: {alert.severity.upper()}",
                    "facts": [
                        {"name": "Service", "value": alert.service},
                        {"name": "Status", "value": alert.status},
                        {"name": "Started", "value": alert.starts_at.isoformat()},
                        {"name": "Message", "value": alert.message}
                    ],
                    "markdown": True
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View in ObservaStack",
                    "targets": [
                        {
                            "os": "default",
                            "uri": f"{context.get('base_url', '')}/alerts/{alert.id}"
                        }
                    ]
                }
            ]
        }
        
        response = await self.client.post(
            self.webhook_url,
            json=message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            raise Exception(f"Teams notification failed: {response.text}")
```

### Register Notification Channel

```python
# app/services/notification_service.py
from app.services.teams_notifier import TeamsNotifier

class NotificationService:
    def __init__(self):
        self.channels = {}
    
    def register_channel(self, name: str, notifier: BaseNotifier):
        """Register a new notification channel."""
        self.channels[name] = notifier
    
    async def send_alert(self, alert: Alert, channels: List[str]):
        """Send alert to specified channels."""
        for channel_name in channels:
            if channel_name in self.channels:
                try:
                    await self.channels[channel_name].send_notification(alert)
                except Exception as e:
                    logger.error(f"Failed to send to {channel_name}: {e}")

# Initialize notification service
notification_service = NotificationService()

# Register built-in channels
notification_service.register_channel("email", EmailNotifier())
notification_service.register_channel("slack", SlackNotifier())

# Register custom channels
if settings.teams_webhook_url:
    notification_service.register_channel(
        "teams", 
        TeamsNotifier(settings.teams_webhook_url)
    )
```

## Custom Dashboard Widgets

### Creating a Custom React Component

```typescript
// src/components/widgets/CustomMetricWidget.tsx
import React, { useEffect, useState } from 'react';
import { useApiClient } from '../../hooks/useApiClient';

interface CustomMetricWidgetProps {
  title: string;
  metricQuery: string;
  timeRange: TimeRange;
  refreshInterval?: number;
}

export function CustomMetricWidget({
  title,
  metricQuery,
  timeRange,
  refreshInterval = 30000
}: CustomMetricWidgetProps) {
  const [data, setData] = useState<MetricData | null>(null);
  const [loading, setLoading] = useState(true);
  const apiClient = useApiClient();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const result = await apiClient.search.metrics({
          query: metricQuery,
          timeRange
        });
        setData(result);
      } catch (error) {
        console.error('Failed to fetch metric data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Set up auto-refresh
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [metricQuery, timeRange, refreshInterval]);

  if (loading) {
    return <div className="widget-loading">Loading...</div>;
  }

  if (!data || data.length === 0) {
    return <div className="widget-no-data">No data available</div>;
  }

  const latestValue = data[data.length - 1]?.value || 0;

  return (
    <div className="custom-metric-widget">
      <h3 className="widget-title">{title}</h3>
      <div className="metric-value">
        {latestValue.toFixed(2)}
      </div>
      <div className="metric-trend">
        {/* Add trend visualization */}
      </div>
    </div>
  );
}
```

### Widget Registry

```typescript
// src/components/widgets/WidgetRegistry.ts
import { ComponentType } from 'react';
import { CustomMetricWidget } from './CustomMetricWidget';
import { LogCountWidget } from './LogCountWidget';
import { AlertSummaryWidget } from './AlertSummaryWidget';

export interface WidgetDefinition {
  type: string;
  name: string;
  component: ComponentType<any>;
  defaultProps?: Record<string, any>;
  configSchema?: Record<string, any>;
}

export class WidgetRegistry {
  private widgets = new Map<string, WidgetDefinition>();

  constructor() {
    // Register built-in widgets
    this.register({
      type: 'custom-metric',
      name: 'Custom Metric',
      component: CustomMetricWidget,
      defaultProps: {
        refreshInterval: 30000
      },
      configSchema: {
        title: { type: 'string', required: true },
        metricQuery: { type: 'string', required: true },
        refreshInterval: { type: 'number', default: 30000 }
      }
    });

    this.register({
      type: 'log-count',
      name: 'Log Count',
      component: LogCountWidget
    });
  }

  register(definition: WidgetDefinition) {
    this.widgets.set(definition.type, definition);
  }

  get(type: string): WidgetDefinition | undefined {
    return this.widgets.get(type);
  }

  getAll(): WidgetDefinition[] {
    return Array.from(this.widgets.values());
  }
}

export const widgetRegistry = new WidgetRegistry();
```

## API Extensions

### Adding Custom Endpoints

```python
# app/api/v1/custom.py
from fastapi import APIRouter, Depends, HTTPException
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/custom", tags=["custom"])

@router.get("/system-health")
async def get_system_health(current_user: User = Depends(get_current_user)):
    """Get comprehensive system health information."""
    
    # Check various system components
    health_checks = {
        "database": await check_database_health(),
        "prometheus": await check_prometheus_health(),
        "loki": await check_loki_health(),
        "disk_space": await check_disk_space(),
        "memory_usage": await check_memory_usage()
    }
    
    overall_status = "healthy" if all(health_checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": health_checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/bulk-export")
async def bulk_export_data(
    export_request: BulkExportRequest,
    current_user: User = Depends(get_current_user)
):
    """Export large amounts of data for analysis."""
    
    # Validate user permissions
    if not await rbac.can_export_data(current_user):
        raise HTTPException(403, "Insufficient permissions for data export")
    
    # Start background export job
    job_id = await start_export_job(export_request, current_user.tenant_id)
    
    return {
        "job_id": job_id,
        "status": "started",
        "estimated_completion": datetime.utcnow() + timedelta(minutes=30)
    }

@router.get("/export-status/{job_id}")
async def get_export_status(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get status of export job."""
    
    job = await get_export_job(job_id, current_user.tenant_id)
    if not job:
        raise HTTPException(404, "Export job not found")
    
    return {
        "job_id": job_id,
        "status": job.status,
        "progress": job.progress,
        "download_url": job.download_url if job.status == "completed" else None
    }
```

### Custom Middleware

```python
# app/middleware/custom_logging.py
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class DetailedLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request details
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log response details
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration": duration,
                "response_size": response.headers.get("content-length", 0)
            }
        )
        
        # Add custom headers
        response.headers["X-Response-Time"] = str(duration)
        response.headers["X-Request-ID"] = request.headers.get("X-Request-ID", "unknown")
        
        return response
```

## Plugin System

### Plugin Interface

```python
# app/plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ObservaStackPlugin(ABC):
    """Base class for ObservaStack plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    def get_api_routes(self) -> List[Any]:
        """Return additional API routes provided by this plugin."""
        return []
    
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        """Return dashboard widgets provided by this plugin."""
        return []
```

### Example Plugin

```python
# plugins/custom_analytics/plugin.py
from app.plugins.base import ObservaStackPlugin
from fastapi import APIRouter
from typing import Dict, Any, List

class CustomAnalyticsPlugin(ObservaStackPlugin):
    @property
    def name(self) -> str:
        return "custom-analytics"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def initialize(self, config: Dict[str, Any]) -> None:
        self.analytics_endpoint = config.get("analytics_endpoint")
        self.api_key = config.get("api_key")
        
        # Initialize analytics client
        self.client = AnalyticsClient(self.analytics_endpoint, self.api_key)
    
    async def cleanup(self) -> None:
        if hasattr(self, 'client'):
            await self.client.close()
    
    def get_api_routes(self) -> List[Any]:
        router = APIRouter(prefix="/analytics", tags=["analytics"])
        
        @router.get("/usage-stats")
        async def get_usage_stats():
            return await self.client.get_usage_statistics()
        
        @router.post("/track-event")
        async def track_event(event_data: dict):
            return await self.client.track_event(event_data)
        
        return [router]
    
    def get_dashboard_widgets(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "usage-chart",
                "name": "Usage Analytics",
                "component": "UsageAnalyticsWidget",
                "config_schema": {
                    "time_range": {"type": "string", "default": "24h"},
                    "metric_type": {"type": "string", "default": "requests"}
                }
            }
        ]
```

### Plugin Manager

```python
# app/plugins/manager.py
import importlib
import os
from typing import Dict, List
from app.plugins.base import ObservaStackPlugin

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, ObservaStackPlugin] = {}
    
    async def load_plugins(self, plugin_dir: str = "plugins"):
        """Load all plugins from the plugin directory."""
        
        if not os.path.exists(plugin_dir):
            return
        
        for plugin_name in os.listdir(plugin_dir):
            plugin_path = os.path.join(plugin_dir, plugin_name)
            
            if os.path.isdir(plugin_path) and os.path.exists(
                os.path.join(plugin_path, "plugin.py")
            ):
                try:
                    # Import plugin module
                    spec = importlib.util.spec_from_file_location(
                        f"{plugin_name}.plugin",
                        os.path.join(plugin_path, "plugin.py")
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find plugin class
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, ObservaStackPlugin) and 
                            attr != ObservaStackPlugin):
                            
                            plugin_instance = attr()
                            await self._register_plugin(plugin_instance)
                            break
                
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {e}")
    
    async def _register_plugin(self, plugin: ObservaStackPlugin):
        """Register a plugin instance."""
        
        # Load plugin configuration
        config = await self._load_plugin_config(plugin.name)
        
        # Initialize plugin
        await plugin.initialize(config)
        
        # Register plugin
        self.plugins[plugin.name] = plugin
        
        logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
    
    def get_plugin(self, name: str) -> ObservaStackPlugin:
        """Get a plugin by name."""
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> List[ObservaStackPlugin]:
        """Get all loaded plugins."""
        return list(self.plugins.values())
    
    async def cleanup_plugins(self):
        """Cleanup all plugins."""
        for plugin in self.plugins.values():
            try:
                await plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up plugin {plugin.name}: {e}")

# Global plugin manager instance
plugin_manager = PluginManager()
```

## Configuration Management

### Environment-Specific Configuration

```python
# app/core/config.py
from typing import Dict, Any
import yaml
import os

class ExtendedSettings(BaseSettings):
    # Plugin configuration
    plugins_enabled: bool = True
    plugins_directory: str = "plugins"
    
    # Custom data sources
    custom_data_sources: Dict[str, Any] = {}
    
    # Custom notification channels
    custom_notifications: Dict[str, Any] = {}
    
    def load_custom_config(self, config_file: str = "custom_config.yml"):
        """Load custom configuration from YAML file."""
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                custom_config = yaml.safe_load(f)
                
                # Update settings with custom config
                for key, value in custom_config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
```

## Testing Extensions

### Plugin Testing

```python
# tests/test_plugins.py
import pytest
from app.plugins.manager import PluginManager
from plugins.custom_analytics.plugin import CustomAnalyticsPlugin

@pytest.mark.asyncio
async def test_plugin_loading():
    manager = PluginManager()
    plugin = CustomAnalyticsPlugin()
    
    config = {
        "analytics_endpoint": "http://localhost:8080",
        "api_key": "test-key"
    }
    
    await plugin.initialize(config)
    
    assert plugin.name == "custom-analytics"
    assert plugin.version == "1.0.0"
    
    # Test API routes
    routes = plugin.get_api_routes()
    assert len(routes) > 0
    
    # Test dashboard widgets
    widgets = plugin.get_dashboard_widgets()
    assert len(widgets) > 0
    
    await plugin.cleanup()
```

## Best Practices

### Extension Development

- **Follow the plugin interface** for consistency
- **Handle errors gracefully** and provide meaningful error messages
- **Document your extensions** thoroughly
- **Write comprehensive tests** for all functionality
- **Use dependency injection** for better testability

### Performance Considerations

- **Implement caching** for expensive operations
- **Use async/await** for I/O operations
- **Monitor resource usage** of extensions
- **Implement proper cleanup** to prevent memory leaks

### Security Guidelines

- **Validate all inputs** from external systems
- **Use proper authentication** for external API calls
- **Implement rate limiting** for external requests
- **Follow the principle of least privilege**

## Next Steps

- [Review the architecture](architecture.md) to understand extension points
- [Check the API reference](api-reference.md) for available interfaces
- [Set up your development environment](contributing.md) to start building extensions