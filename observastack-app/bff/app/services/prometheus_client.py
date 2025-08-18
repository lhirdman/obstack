"""Prometheus client for metrics search integration."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from ..models.search import (
    SearchQuery, SearchItem, SearchType, MetricItem, MetricType, SearchStats
)
from ..exceptions import SearchException


class PrometheusQueryResponse(BaseModel):
    """Prometheus query response model."""
    status: str
    data: Dict[str, Any]
    errorType: Optional[str] = None
    error: Optional[str] = None


class PrometheusClient:
    """Client for interacting with Prometheus metrics system."""
    
    def __init__(self, base_url: str = "http://localhost:9090", timeout: int = 30):
        """
        Initialize Prometheus client.
        
        Args:
            base_url: Prometheus server base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def search_metrics_stream(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ):
        """
        Stream metrics from Prometheus with real-time results.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Yields:
            Tuple of (search items chunk, partial stats)
            
        Raises:
            SearchException: If search operation fails
        """
        try:
            # For streaming metrics, we'll query different metric families
            # and yield results as they come in
            
            # First, get available metric names
            metric_names = await self.get_metric_names(tenant_id)
            
            # Filter metric names based on free text search
            if query.free_text.strip():
                filtered_names = [name for name in metric_names 
                                if query.free_text.lower() in name.lower()]
            else:
                filtered_names = metric_names[:20]  # Limit to prevent overwhelming
            
            chunk_size = min(query.limit // len(filtered_names) if filtered_names else query.limit, 10)
            
            for metric_name in filtered_names:
                # Create specific query for this metric
                metric_query = query.model_copy()
                metric_query.free_text = metric_name
                metric_query.limit = chunk_size
                
                # Search this specific metric
                items, stats = await self.search_metrics(metric_query, tenant_id)
                
                if items:
                    yield items, stats
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.05)
                
        except Exception as e:
            raise SearchException(f"Prometheus streaming search error: {str(e)}") from e

    async def search_metrics(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ) -> tuple[List[SearchItem], SearchStats]:
        """
        Search metrics in Prometheus with tenant isolation.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            Tuple of (search items, search stats)
            
        Raises:
            SearchException: If search operation fails
        """
        try:
            # Build PromQL query with tenant isolation
            promql_query = self._build_promql_query(query, tenant_id)
            
            # Use query_range for time series data
            params = {
                "query": promql_query,
                "start": query.time_range.start.isoformat(),
                "end": query.time_range.end.isoformat(),
                "step": self._calculate_step(query.time_range.start, query.time_range.end)
            }
            
            # Execute query
            url = f"{self.base_url}/api/v1/query_range"
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            prom_response = PrometheusQueryResponse(**response.json())
            
            if prom_response.status != "success":
                error_msg = prom_response.error or "Unknown Prometheus error"
                raise SearchException(f"Prometheus query failed: {error_msg}")
            
            # Convert to search items
            items = self._parse_prometheus_response(prom_response.data, tenant_id)
            
            # Apply limit and offset
            total_items = len(items)
            start_idx = query.offset
            end_idx = start_idx + query.limit
            items = items[start_idx:end_idx]
            
            # Generate stats
            stats = SearchStats(
                matched=len(items),
                scanned=total_items,
                latency_ms=int(response.elapsed.total_seconds() * 1000),
                sources={"prometheus": len(items)}
            )
            
            return items, stats
            
        except httpx.HTTPError as e:
            raise SearchException(f"Prometheus request failed: {str(e)}") from e
        except Exception as e:
            raise SearchException(f"Prometheus search error: {str(e)}") from e
    
    def _build_promql_query(self, query: SearchQuery, tenant_id: str) -> str:
        """
        Build PromQL query string with tenant isolation.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            PromQL query string
        """
        # Start with tenant isolation
        tenant_filter = f'tenant_id="{tenant_id}"'
        
        # If free text search is provided, use it as metric name pattern
        if query.free_text.strip():
            # Use regex matching for metric names
            metric_pattern = f'{{__name__=~".*{query.free_text}.*",{tenant_filter}}}'
        else:
            # Get all metrics for tenant
            metric_pattern = f'{{{tenant_filter}}}'
        
        # Add filters as label matchers
        filter_clauses = []
        for filter_item in query.filters:
            filter_clause = self._build_filter_clause(filter_item)
            if filter_clause:
                filter_clauses.append(filter_clause)
        
        if filter_clauses:
            # Combine tenant filter with additional filters
            all_filters = [tenant_filter] + filter_clauses
            metric_pattern = f'{{{",".join(all_filters)}}}'
        
        return metric_pattern
    
    def _build_filter_clause(self, filter_item) -> str:
        """
        Build PromQL filter clause from search filter.
        
        Args:
            filter_item: Search filter
            
        Returns:
            PromQL filter clause
        """
        field = filter_item.field
        operator = filter_item.operator
        value = filter_item.value
        
        if operator == "equals":
            return f'{field}="{value}"'
        elif operator == "not_equals":
            return f'{field}!="{value}"'
        elif operator == "regex":
            return f'{field}=~"{value}"'
        elif operator == "contains":
            return f'{field}=~".*{value}.*"'
        else:
            # Range operators not directly supported in label matching
            return ""
    
    def _calculate_step(self, start: datetime, end: datetime) -> str:
        """
        Calculate appropriate step size for query range.
        
        Args:
            start: Start time
            end: End time
            
        Returns:
            Step size string (e.g., "1m", "5m")
        """
        duration = end - start
        total_seconds = duration.total_seconds()
        
        # Aim for ~100-200 data points
        if total_seconds <= 3600:  # 1 hour
            return "30s"
        elif total_seconds <= 86400:  # 1 day
            return "5m"
        elif total_seconds <= 604800:  # 1 week
            return "1h"
        else:
            return "6h"
    
    def _parse_prometheus_response(
        self, 
        data: Dict[str, Any], 
        tenant_id: str
    ) -> List[SearchItem]:
        """
        Parse Prometheus response data into search items.
        
        Args:
            data: Prometheus response data
            tenant_id: Tenant ID
            
        Returns:
            List of search items
        """
        items = []
        
        # Prometheus returns results in data.result array
        for series in data.get("result", []):
            metric_labels = series.get("metric", {})
            metric_name = metric_labels.get("__name__", "unknown_metric")
            service = metric_labels.get("service", metric_labels.get("job", "unknown"))
            
            # Determine metric type from name patterns
            metric_type = self._infer_metric_type(metric_name)
            
            # Process each value in the time series
            for value_pair in series.get("values", []):
                timestamp_unix, value_str = value_pair
                
                # Convert Unix timestamp to datetime
                timestamp = datetime.fromtimestamp(float(timestamp_unix))
                
                # Parse value
                try:
                    value = float(value_str)
                except (ValueError, TypeError):
                    continue  # Skip invalid values
                
                # Create metric item
                metric_item = MetricItem(
                    name=metric_name,
                    value=value,
                    unit=self._infer_unit(metric_name),
                    labels={k: v for k, v in metric_labels.items() 
                           if k not in ["__name__", "tenant_id"]},
                    type=metric_type
                )
                
                # Create search item
                search_item = SearchItem(
                    id=f"prometheus_{timestamp_unix}_{hash(metric_name)}_{hash(str(metric_labels))}",
                    timestamp=timestamp,
                    source=SearchType.METRICS,
                    service=service,
                    content=metric_item,
                    tenant_id=tenant_id
                )
                
                items.append(search_item)
        
        # Sort by timestamp (descending by default)
        items.sort(key=lambda x: x.timestamp, reverse=True)
        
        return items
    
    def _infer_metric_type(self, metric_name: str) -> MetricType:
        """
        Infer metric type from metric name patterns.
        
        Args:
            metric_name: Metric name
            
        Returns:
            Inferred metric type
        """
        name_lower = metric_name.lower()
        
        if any(suffix in name_lower for suffix in ["_total", "_count", "_created"]):
            return MetricType.COUNTER
        elif any(suffix in name_lower for suffix in ["_bucket", "_sum"]):
            return MetricType.HISTOGRAM
        elif "quantile" in name_lower:
            return MetricType.SUMMARY
        else:
            return MetricType.GAUGE
    
    def _infer_unit(self, metric_name: str) -> str:
        """
        Infer unit from metric name patterns.
        
        Args:
            metric_name: Metric name
            
        Returns:
            Inferred unit
        """
        name_lower = metric_name.lower()
        
        if any(keyword in name_lower for keyword in ["seconds", "duration", "time"]):
            return "seconds"
        elif any(keyword in name_lower for keyword in ["bytes", "size", "memory"]):
            return "bytes"
        elif any(keyword in name_lower for keyword in ["percent", "ratio", "rate"]):
            return "percent"
        elif "requests" in name_lower:
            return "requests"
        else:
            return ""
    
    async def health_check(self) -> bool:
        """
        Check if Prometheus is healthy and reachable.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/-/healthy"
            response = await self._client.get(url)
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_metric_names(self, tenant_id: str) -> List[str]:
        """
        Get list of available metric names for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List of metric names
        """
        try:
            url = f"{self.base_url}/api/v1/label/__name__/values"
            response = await self._client.get(url)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") == "success":
                return data.get("data", [])
            return []
        except Exception:
            return []