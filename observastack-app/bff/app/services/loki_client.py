"""Loki client for log search integration."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from ..models.search import (
    SearchQuery, SearchItem, SearchType, LogItem, LogLevel, SearchStats
)
from ..exceptions import SearchException


class LokiQueryResponse(BaseModel):
    """Loki query response model."""
    status: str
    data: Dict[str, Any]


class LokiClient:
    """Client for interacting with Loki log aggregation system."""
    
    def __init__(self, base_url: str = "http://localhost:3100", timeout: int = 30):
        """
        Initialize Loki client.
        
        Args:
            base_url: Loki server base URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def search_logs_stream(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ):
        """
        Stream logs from Loki with real-time results.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Yields:
            Tuple of (search items chunk, partial stats)
            
        Raises:
            SearchException: If search operation fails
        """
        try:
            # For streaming, we'll break the query into smaller time chunks
            chunk_duration = 300  # 5 minutes per chunk
            start_time = query.time_range.start
            end_time = query.time_range.end
            
            current_time = start_time
            chunk_size = min(query.limit // 4, 25)  # Smaller chunks for streaming
            
            while current_time < end_time:
                chunk_end = min(current_time + timedelta(seconds=chunk_duration), end_time)
                
                # Create chunk query
                chunk_query = query.model_copy()
                chunk_query.time_range.start = current_time
                chunk_query.time_range.end = chunk_end
                chunk_query.limit = chunk_size
                
                # Search this chunk
                items, stats = await self.search_logs(chunk_query, tenant_id)
                
                if items:
                    yield items, stats
                
                # Move to next chunk
                current_time = chunk_end
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)
                
        except Exception as e:
            raise SearchException(f"Loki streaming search error: {str(e)}") from e

    async def search_logs(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ) -> tuple[List[SearchItem], SearchStats]:
        """
        Search logs in Loki with tenant isolation.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            Tuple of (search items, search stats)
            
        Raises:
            SearchException: If search operation fails
        """
        try:
            # Build LogQL query with tenant isolation
            logql_query = self._build_logql_query(query, tenant_id)
            
            # Prepare query parameters
            params = {
                "query": logql_query,
                "start": int(query.time_range.start.timestamp() * 1_000_000_000),  # nanoseconds
                "end": int(query.time_range.end.timestamp() * 1_000_000_000),
                "limit": query.limit,
                "direction": "backward" if query.sort_order == "desc" else "forward"
            }
            
            # Execute query
            url = f"{self.base_url}/loki/api/v1/query_range"
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            loki_response = LokiQueryResponse(**response.json())
            
            if loki_response.status != "success":
                raise SearchException(f"Loki query failed: {loki_response.data}")
            
            # Convert to search items
            items = self._parse_loki_response(loki_response.data, tenant_id)
            
            # Generate stats
            stats = SearchStats(
                matched=len(items),
                scanned=len(items),  # Loki doesn't provide scanned count
                latency_ms=int(response.elapsed.total_seconds() * 1000),
                sources={"loki": len(items)}
            )
            
            return items, stats
            
        except httpx.HTTPError as e:
            raise SearchException(f"Loki request failed: {str(e)}") from e
        except Exception as e:
            raise SearchException(f"Loki search error: {str(e)}") from e
    
    def _build_logql_query(self, query: SearchQuery, tenant_id: str) -> str:
        """
        Build LogQL query string with tenant isolation.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            LogQL query string
        """
        # Start with tenant isolation
        logql_parts = [f'{{tenant_id="{tenant_id}"}}']
        
        # Add free text search if provided
        if query.free_text.strip():
            # Escape special characters and add regex search
            escaped_text = query.free_text.replace('"', '\\"')
            logql_parts.append(f'|~ "(?i).*{escaped_text}.*"')
        
        # Add filters
        for filter_item in query.filters:
            filter_clause = self._build_filter_clause(filter_item)
            if filter_clause:
                logql_parts.append(filter_clause)
        
        return " ".join(logql_parts)
    
    def _build_filter_clause(self, filter_item) -> str:
        """
        Build LogQL filter clause from search filter.
        
        Args:
            filter_item: Search filter
            
        Returns:
            LogQL filter clause
        """
        field = filter_item.field
        operator = filter_item.operator
        value = filter_item.value
        
        if operator == "equals":
            return f'| json | {field}="{value}"'
        elif operator == "contains":
            return f'| json | {field}=~".*{value}.*"'
        elif operator == "regex":
            return f'| json | {field}=~"{value}"'
        elif operator == "not_equals":
            return f'| json | {field}!="{value}"'
        elif operator == "exists":
            return f'| json | {field}!=""'
        else:
            # For range operators, we'd need more complex LogQL
            return ""
    
    def _parse_loki_response(
        self, 
        data: Dict[str, Any], 
        tenant_id: str
    ) -> List[SearchItem]:
        """
        Parse Loki response data into search items.
        
        Args:
            data: Loki response data
            tenant_id: Tenant ID
            
        Returns:
            List of search items
        """
        items = []
        
        # Loki returns results in data.result array
        for stream in data.get("result", []):
            labels = stream.get("stream", {})
            service = labels.get("service", labels.get("job", "unknown"))
            
            for entry in stream.get("values", []):
                timestamp_ns, log_line = entry
                
                # Convert nanosecond timestamp to datetime
                timestamp = datetime.fromtimestamp(int(timestamp_ns) / 1_000_000_000)
                
                # Try to parse log line as JSON for structured logs
                try:
                    log_data = json.loads(log_line)
                    message = log_data.get("message", log_line)
                    level_str = log_data.get("level", "info").lower()
                    fields = {k: v for k, v in log_data.items() 
                             if k not in ["message", "level", "timestamp"]}
                except (json.JSONDecodeError, AttributeError):
                    # Plain text log
                    message = log_line
                    level_str = "info"
                    fields = {}
                
                # Map log level
                try:
                    level = LogLevel(level_str)
                except ValueError:
                    level = LogLevel.INFO
                
                # Create log item
                log_item = LogItem(
                    message=message,
                    level=level,
                    labels=labels,
                    fields=fields
                )
                
                # Create search item
                search_item = SearchItem(
                    id=f"loki_{timestamp_ns}_{hash(log_line)}",
                    timestamp=timestamp,
                    source=SearchType.LOGS,
                    service=service,
                    content=log_item,
                    tenant_id=tenant_id
                )
                
                items.append(search_item)
        
        return items
    
    async def health_check(self) -> bool:
        """
        Check if Loki is healthy and reachable.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/ready"
            response = await self._client.get(url)
            return response.status_code == 200
        except Exception:
            return False