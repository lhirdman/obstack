"""Tempo client for trace search integration."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from ..models.search import (
    SearchQuery, SearchItem, SearchType, TraceItem, TraceStatus, SearchStats
)
from ..exceptions import SearchException


class TempoSearchResponse(BaseModel):
    """Tempo search response model."""
    traces: List[Dict[str, Any]]
    metrics: Dict[str, Any]


class TempoClient:
    """Client for interacting with Tempo distributed tracing system."""
    
    def __init__(self, base_url: str = "http://localhost:3200", timeout: int = 30):
        """
        Initialize Tempo client.
        
        Args:
            base_url: Tempo server base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def search_traces_stream(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ):
        """
        Stream traces from Tempo with real-time results.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Yields:
            Tuple of (search items chunk, partial stats)
            
        Raises:
            SearchException: If search operation fails
        """
        try:
            # For streaming traces, we'll break the query into smaller time chunks
            # since Tempo searches can be expensive
            chunk_duration = 600  # 10 minutes per chunk
            start_time = query.time_range.start
            end_time = query.time_range.end
            
            current_time = start_time
            chunk_size = min(query.limit // 3, 20)  # Smaller chunks for traces
            
            while current_time < end_time:
                chunk_end = min(current_time + timedelta(seconds=chunk_duration), end_time)
                
                # Create chunk query
                chunk_query = query.model_copy()
                chunk_query.time_range.start = current_time
                chunk_query.time_range.end = chunk_end
                chunk_query.limit = chunk_size
                
                # Search this chunk
                items, stats = await self.search_traces(chunk_query, tenant_id)
                
                if items:
                    yield items, stats
                
                # Move to next chunk
                current_time = chunk_end
                
                # Longer delay for traces as they're more expensive to query
                await asyncio.sleep(0.2)
                
        except Exception as e:
            raise SearchException(f"Tempo streaming search error: {str(e)}") from e

    async def search_traces(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ) -> tuple[List[SearchItem], SearchStats]:
        """
        Search traces in Tempo with tenant isolation.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            Tuple of (search items, search stats)
            
        Raises:
            SearchException: If search operation fails
        """
        try:
            # Build search parameters
            search_params = self._build_search_params(query, tenant_id)
            
            # Execute search
            url = f"{self.base_url}/api/search"
            response = await self._client.get(url, params=search_params)
            response.raise_for_status()
            
            # Parse response
            search_data = response.json()
            
            # Convert to search items
            items = await self._parse_tempo_response(search_data, tenant_id)
            
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
                sources={"tempo": len(items)}
            )
            
            return items, stats
            
        except httpx.HTTPError as e:
            raise SearchException(f"Tempo request failed: {str(e)}") from e
        except Exception as e:
            raise SearchException(f"Tempo search error: {str(e)}") from e
    
    def _build_search_params(self, query: SearchQuery, tenant_id: str) -> Dict[str, Any]:
        """
        Build Tempo search parameters with tenant isolation.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            Search parameters dictionary
        """
        params = {
            "start": int(query.time_range.start.timestamp()),
            "end": int(query.time_range.end.timestamp()),
            "limit": min(query.limit, 1000),  # Tempo has limits
        }
        
        # Add tenant isolation
        params["tags"] = f"tenant.id={tenant_id}"
        
        # Add service filter if specified in free text
        if query.free_text.strip():
            # Try to parse as service name or operation name
            text = query.free_text.strip()
            if "service:" in text:
                service_name = text.split("service:")[1].strip()
                params["service.name"] = service_name
            elif "operation:" in text:
                operation_name = text.split("operation:")[1].strip()
                params["name"] = operation_name
            else:
                # General text search in span attributes
                params["q"] = text
        
        # Add filters as tag searches
        for filter_item in query.filters:
            filter_param = self._build_filter_param(filter_item)
            if filter_param:
                key, value = filter_param
                if "tags" in params:
                    params["tags"] += f" {key}={value}"
                else:
                    params["tags"] = f"{key}={value}"
        
        return params
    
    def _build_filter_param(self, filter_item) -> Optional[tuple[str, str]]:
        """
        Build Tempo filter parameter from search filter.
        
        Args:
            filter_item: Search filter
            
        Returns:
            Tuple of (key, value) or None
        """
        field = filter_item.field
        operator = filter_item.operator
        value = filter_item.value
        
        # Map common fields to Tempo tag names
        field_mapping = {
            "service": "service.name",
            "operation": "name",
            "status": "status.code",
            "error": "error",
            "http_method": "http.method",
            "http_status": "http.status_code",
            "user_id": "user.id"
        }
        
        tempo_field = field_mapping.get(field, field)
        
        if operator in ["equals", "contains"]:
            return (tempo_field, str(value))
        else:
            # Tempo search is limited in filter operators
            return None
    
    async def _parse_tempo_response(
        self, 
        data: Dict[str, Any], 
        tenant_id: str
    ) -> List[SearchItem]:
        """
        Parse Tempo response data into search items.
        
        Args:
            data: Tempo response data
            tenant_id: Tenant ID
            
        Returns:
            List of search items
        """
        items = []
        
        # Tempo returns traces in 'traces' array
        for trace_summary in data.get("traces", []):
            trace_id = trace_summary.get("traceID")
            if not trace_id:
                continue
            
            # Get detailed trace data
            try:
                trace_details = await self._get_trace_details(trace_id)
                if trace_details:
                    trace_items = self._parse_trace_details(trace_details, tenant_id)
                    items.extend(trace_items)
                else:
                    # If no details available, create item from summary
                    summary_item = self._create_item_from_summary(trace_summary, tenant_id)
                    if summary_item:
                        items.append(summary_item)
            except Exception:
                # If we can't get details, create item from summary
                summary_item = self._create_item_from_summary(trace_summary, tenant_id)
                if summary_item:
                    items.append(summary_item)
        
        # Sort by timestamp (descending by default)
        items.sort(key=lambda x: x.timestamp, reverse=True)
        
        return items
    
    async def _get_trace_details(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed trace information by trace ID.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace details or None if not found
        """
        try:
            url = f"{self.base_url}/api/traces/{trace_id}"
            response = await self._client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
    
    def _parse_trace_details(
        self, 
        trace_data: Dict[str, Any], 
        tenant_id: str
    ) -> List[SearchItem]:
        """
        Parse detailed trace data into search items.
        
        Args:
            trace_data: Detailed trace data
            tenant_id: Tenant ID
            
        Returns:
            List of search items (one per span)
        """
        items = []
        
        # Tempo trace format varies, handle common structures
        batches = trace_data.get("batches", [])
        if not batches and "spans" in trace_data:
            # Direct spans format
            batches = [{"spans": trace_data["spans"]}]
        
        for batch in batches:
            resource = batch.get("resource", {})
            service_name = self._extract_service_name(resource)
            
            for span in batch.get("spans", []):
                span_item = self._create_span_item(span, service_name, tenant_id)
                if span_item:
                    items.append(span_item)
        
        return items
    
    def _extract_service_name(self, resource: Dict[str, Any]) -> str:
        """
        Extract service name from resource attributes.
        
        Args:
            resource: Resource attributes
            
        Returns:
            Service name
        """
        attributes = resource.get("attributes", [])
        for attr in attributes:
            if attr.get("key") == "service.name":
                return attr.get("value", {}).get("stringValue", "unknown")
        return "unknown"
    
    def _create_span_item(
        self, 
        span: Dict[str, Any], 
        service_name: str, 
        tenant_id: str
    ) -> Optional[SearchItem]:
        """
        Create search item from span data.
        
        Args:
            span: Span data
            service_name: Service name
            tenant_id: Tenant ID
            
        Returns:
            Search item or None
        """
        try:
            # Extract span information
            trace_id = span.get("traceId", "")
            span_id = span.get("spanId", "")
            operation_name = span.get("name", "unknown")
            
            # Calculate duration (in microseconds)
            start_time_ns = int(span.get("startTimeUnixNano", 0))
            end_time_ns = int(span.get("endTimeUnixNano", 0))
            duration_us = (end_time_ns - start_time_ns) // 1000  # Convert nanoseconds to microseconds
            
            # Convert start time to datetime
            timestamp = datetime.fromtimestamp(start_time_ns / 1_000_000_000)
            
            # Extract status
            status_info = span.get("status", {})
            status_code = status_info.get("code", 0)
            trace_status = TraceStatus.OK if status_code == 1 else TraceStatus.ERROR
            
            # Extract tags from attributes
            tags = {}
            for attr in span.get("attributes", []):
                key = attr.get("key", "")
                value_obj = attr.get("value", {})
                if "stringValue" in value_obj:
                    tags[key] = value_obj["stringValue"]
                elif "intValue" in value_obj:
                    tags[key] = str(value_obj["intValue"])
                elif "boolValue" in value_obj:
                    tags[key] = str(value_obj["boolValue"])
            
            # Get parent span ID
            parent_span_id = span.get("parentSpanId") or None
            
            # Create trace item
            trace_item = TraceItem(
                trace_id=trace_id,
                span_id=span_id,
                operation_name=operation_name,
                duration=duration_us,
                status=trace_status,
                tags=tags,
                parent_span_id=parent_span_id
            )
            
            # Create search item
            search_item = SearchItem(
                id=f"tempo_{trace_id}_{span_id}",
                timestamp=timestamp,
                source=SearchType.TRACES,
                service=service_name,
                content=trace_item,
                correlation_id=trace_id,  # Use trace_id for correlation
                tenant_id=tenant_id
            )
            
            return search_item
            
        except Exception:
            return None
    
    def _create_item_from_summary(
        self, 
        trace_summary: Dict[str, Any], 
        tenant_id: str
    ) -> Optional[SearchItem]:
        """
        Create search item from trace summary when details are unavailable.
        
        Args:
            trace_summary: Trace summary data
            tenant_id: Tenant ID
            
        Returns:
            Search item or None
        """
        try:
            trace_id = trace_summary.get("traceID", "")
            root_service = trace_summary.get("rootServiceName", "unknown")
            root_trace_name = trace_summary.get("rootTraceName", "unknown")
            
            # Use start time from summary
            start_time_unix = trace_summary.get("startTimeUnixNano", 0)
            timestamp = datetime.fromtimestamp(int(start_time_unix) / 1_000_000_000)
            
            # Calculate duration
            duration_ms = trace_summary.get("durationMs", 0)
            duration_us = int(duration_ms * 1000)
            
            # Create trace item
            trace_item = TraceItem(
                trace_id=trace_id,
                span_id="root",  # Placeholder for root span
                operation_name=root_trace_name,
                duration=duration_us,
                status=TraceStatus.OK,  # Default status
                tags={}
            )
            
            # Create search item
            search_item = SearchItem(
                id=f"tempo_summary_{trace_id}",
                timestamp=timestamp,
                source=SearchType.TRACES,
                service=root_service,
                content=trace_item,
                correlation_id=trace_id,
                tenant_id=tenant_id
            )
            
            return search_item
            
        except Exception:
            return None
    
    async def health_check(self) -> bool:
        """
        Check if Tempo is healthy and reachable.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/ready"
            response = await self._client.get(url)
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_trace_by_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific trace by ID.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace data or None if not found
        """
        return await self._get_trace_details(trace_id)