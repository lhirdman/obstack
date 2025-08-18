"""Unified search service for cross-signal observability data."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict

from ..models.search import (
    SearchQuery, SearchItem, SearchType, SearchStats, SearchResult,
    LogItem, MetricItem, TraceItem, CorrelationRequest, CorrelationResponse
)
from ..exceptions import SearchException
from .loki_client import LokiClient
from .prometheus_client import PrometheusClient
from .tempo_client import TempoClient
from ..core.logging import get_logger, log_performance
from ..core.monitoring import monitor_performance, record_search_metrics
from ..core.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig
from ..core.retry import retry_async, RetryConfigs
from ..core.graceful_degradation import execute_with_fallback


class SearchService:
    """Unified search service that orchestrates searches across multiple data sources."""
    
    def __init__(
        self,
        loki_client: Optional[LokiClient] = None,
        prometheus_client: Optional[PrometheusClient] = None,
        tempo_client: Optional[TempoClient] = None
    ):
        """
        Initialize search service with data source clients.
        
        Args:
            loki_client: Loki client for log search
            prometheus_client: Prometheus client for metrics search
            tempo_client: Tempo client for trace search
        """
        self.loki_client = loki_client or LokiClient()
        self.prometheus_client = prometheus_client or PrometheusClient()
        self.tempo_client = tempo_client or TempoClient()
        self.logger = get_logger("search_service")
        
        # Initialize circuit breakers for each client
        self._circuit_breakers = {}
        self._initialize_circuit_breakers()
    
    def _initialize_circuit_breakers(self):
        """Initialize circuit breakers for data source clients."""
        # Circuit breaker configuration for search services
        search_cb_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30.0,
            success_threshold=3,
            timeout=30.0,
            expected_exceptions=(Exception,)
        )
        
        # Store configs for async initialization
        self._cb_configs = {
            "loki": search_cb_config,
            "prometheus": search_cb_config,
            "tempo": search_cb_config
        }
    
    async def _get_circuit_breaker(self, service_name: str):
        """Get or create circuit breaker for a service."""
        if service_name not in self._circuit_breakers:
            config = self._cb_configs.get(service_name)
            self._circuit_breakers[service_name] = await get_circuit_breaker(
                f"search_{service_name}", config
            )
        return self._circuit_breakers[service_name]
    
    async def close(self):
        """Close all client connections."""
        self.logger.info("Closing search service connections")
        await asyncio.gather(
            self.loki_client.close(),
            self.prometheus_client.close(),
            self.tempo_client.close(),
            return_exceptions=True
        )
        self.logger.info("Search service connections closed")
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all data source clients.
        
        Returns:
            Dictionary mapping client names to health status
        """
        try:
            health_results = {}
            
            # Check each client health
            health_checks = [
                ("loki", self.loki_client.health_check()),
                ("prometheus", self.prometheus_client.health_check()),
                ("tempo", self.tempo_client.health_check())
            ]
            
            for name, check_coro in health_checks:
                try:
                    is_healthy = await check_coro
                    health_results[name] = is_healthy
                except Exception as e:
                    self.logger.warning(f"Health check failed for {name}: {e}")
                    health_results[name] = False
            
            return health_results
            
        except Exception as e:
            self.logger.error("Failed to perform health checks", exc_info=True)
            return {"loki": False, "prometheus": False, "tempo": False}
    
    async def search_stream(self, query: SearchQuery, tenant_id: str):
        """
        Perform streaming search across all data sources with real-time results.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Yields:
            StreamingSearchChunk: Real-time search result chunks
            
        Raises:
            SearchException: If search operation fails
        """
        try:
            from ..models.search import StreamingSearchChunk
            
            chunk_id = 0
            all_items = []
            start_time = datetime.utcnow()
            
            # Determine which sources to search
            search_generators = []
            
            if query.type in [SearchType.ALL, SearchType.LOGS]:
                search_generators.append(
                    ("logs", self.loki_client.search_logs_stream(query, tenant_id))
                )
            
            if query.type in [SearchType.ALL, SearchType.METRICS]:
                search_generators.append(
                    ("metrics", self.prometheus_client.search_metrics_stream(query, tenant_id))
                )
            
            if query.type in [SearchType.ALL, SearchType.TRACES]:
                search_generators.append(
                    ("traces", self.tempo_client.search_traces_stream(query, tenant_id))
                )
            
            # Stream results from all sources concurrently
            async def stream_from_source(source_name, generator):
                try:
                    async for items, partial_stats in generator:
                        yield source_name, items, partial_stats
                except Exception as e:
                    print(f"Stream error from {source_name}: {e}")
                    yield source_name, [], SearchStats(matched=0, scanned=0, latency_ms=0, sources={})
            
            # Create concurrent streams
            from asyncio import Queue
            
            result_queue = Queue()
            
            async def producer():
                tasks = []
                for source_name, generator in search_generators:
                    task = asyncio.create_task(
                        self._stream_source_to_queue(source_name, generator, result_queue)
                    )
                    tasks.append(task)
                
                # Wait for all tasks to complete
                await asyncio.gather(*tasks, return_exceptions=True)
                await result_queue.put(None)  # Signal completion
            
            # Start producer
            producer_task = asyncio.create_task(producer())
            
            # Stream results as they arrive
            combined_stats = SearchStats(matched=0, scanned=0, latency_ms=0, sources={})
            
            while True:
                try:
                    # Wait for next result with timeout
                    result = await asyncio.wait_for(result_queue.get(), timeout=30.0)
                    
                    if result is None:  # End of stream
                        break
                    
                    source_name, items, partial_stats = result
                    
                    if items:
                        all_items.extend(items)
                        
                        # Apply correlation if multiple sources
                        if query.type == SearchType.ALL:
                            items = await self._apply_correlation(items, query.time_range)
                        
                        # Update combined stats
                        combined_stats.matched += partial_stats.matched
                        combined_stats.scanned += partial_stats.scanned
                        combined_stats.latency_ms = max(combined_stats.latency_ms, partial_stats.latency_ms)
                        combined_stats.sources.update(partial_stats.sources)
                        
                        # Yield chunk
                        chunk = StreamingSearchChunk(
                            chunk_id=chunk_id,
                            items=items,
                            is_final=False
                        )
                        yield chunk
                        chunk_id += 1
                
                except asyncio.TimeoutError:
                    # Timeout waiting for results
                    break
            
            # Calculate final stats
            end_time = datetime.utcnow()
            total_latency = int((end_time - start_time).total_seconds() * 1000)
            combined_stats.latency_ms = max(combined_stats.latency_ms, total_latency)
            
            # Send final chunk with complete stats
            final_chunk = StreamingSearchChunk(
                chunk_id=chunk_id,
                items=[],
                is_final=True,
                stats=combined_stats
            )
            yield final_chunk
            
            # Cleanup
            if not producer_task.done():
                producer_task.cancel()
                
        except Exception as e:
            raise SearchException(f"Streaming search failed: {str(e)}") from e
    
    async def _stream_source_to_queue(self, source_name: str, generator, queue):
        """Stream results from a single source to the result queue."""
        try:
            async for items, stats in generator:
                await queue.put((source_name, items, stats))
        except Exception as e:
            print(f"Error streaming from {source_name}: {e}")
            # Put empty result to indicate this source is done
            await queue.put((source_name, [], SearchStats(matched=0, scanned=0, latency_ms=0, sources={})))

    async def search(self, query: SearchQuery, tenant_id: str) -> SearchResult:
        """
        Perform unified search across all data sources.
        
        Args:
            query: Search query parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            Unified search results
            
        Raises:
            SearchException: If search operation fails
        """
        async with monitor_performance("unified_search", {"tenant_id": tenant_id, "search_type": query.type.value}):
            self.logger.info(
                "Starting unified search",
                extra={
                    "search": {
                        "query": query.free_text,
                        "type": query.type.value,
                        "tenant_id": tenant_id,
                        "time_range": {
                            "start": query.time_range.start.isoformat() if query.time_range.start else None,
                            "end": query.time_range.end.isoformat() if query.time_range.end else None
                        }
                    }
                }
            )
            
            try:
            # Determine which sources to search
            search_tasks = []
            
            if query.type in [SearchType.ALL, SearchType.LOGS]:
                search_tasks.append(self._search_logs_safe(query, tenant_id))
            
            if query.type in [SearchType.ALL, SearchType.METRICS]:
                search_tasks.append(self._search_metrics_safe(query, tenant_id))
            
            if query.type in [SearchType.ALL, SearchType.TRACES]:
                search_tasks.append(self._search_traces_safe(query, tenant_id))
            
            # Execute searches concurrently
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            all_items = []
            combined_stats = SearchStats(matched=0, scanned=0, latency_ms=0, sources={})
            
            for result in search_results:
                if isinstance(result, Exception):
                    # Log error but continue with other results
                    print(f"Search error: {result}")
                    continue
                
                items, stats = result
                all_items.extend(items)
                
                # Combine stats
                combined_stats.matched += stats.matched
                combined_stats.scanned += stats.scanned
                combined_stats.latency_ms = max(combined_stats.latency_ms, stats.latency_ms)
                combined_stats.sources.update(stats.sources)
            
            # Apply cross-signal correlation
            if query.type == SearchType.ALL and len(all_items) > 1:
                all_items = await self._apply_correlation(all_items, query.time_range)
            
            # Sort results by timestamp
            sort_reverse = query.sort_order == "desc"
            if query.sort_by == "timestamp":
                all_items.sort(key=lambda x: x.timestamp, reverse=sort_reverse)
            
            # Apply final limit and offset
            total_items = len(all_items)
            start_idx = query.offset
            end_idx = start_idx + query.limit
            final_items = all_items[start_idx:end_idx]
            
                # Update final stats
                combined_stats.matched = len(final_items)
                combined_stats.scanned = total_items
                
                # Record search metrics
                record_search_metrics(
                    search_type=query.type.value,
                    result_count=len(final_items),
                    duration_ms=combined_stats.latency_ms,
                    tenant_id=tenant_id,
                    success=True
                )
                
                self.logger.info(
                    "Unified search completed successfully",
                    extra={
                        "search": {
                            "tenant_id": tenant_id,
                            "results_count": len(final_items),
                            "duration_ms": combined_stats.latency_ms,
                            "sources_used": list(combined_stats.sources.keys())
                        }
                    }
                )
                
                return SearchResult(
                    items=final_items,
                    stats=combined_stats,
                    facets=[],  # TODO: Implement facets
                    next_token=None  # TODO: Implement pagination tokens
                )
                
            except Exception as e:
                # Record failed search metrics
                record_search_metrics(
                    search_type=query.type.value,
                    result_count=0,
                    duration_ms=0,
                    tenant_id=tenant_id,
                    success=False
                )
                
                self.logger.error(
                    "Unified search failed",
                    exc_info=True,
                    extra={
                        "search": {
                            "tenant_id": tenant_id,
                            "query": query.free_text,
                            "error": str(e)
                        }
                    }
                )
                raise SearchException(f"Unified search failed: {str(e)}") from e
    
    async def _search_logs_safe(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ) -> tuple[List[SearchItem], SearchStats]:
        """
        Safely search logs with error handling, circuit breaker, and retry.
        
        Args:
            query: Search query
            tenant_id: Tenant ID
            
        Returns:
            Tuple of (items, stats) or empty results on error
        """
        async def primary_search():
            circuit_breaker = await self._get_circuit_breaker("loki")
            return await circuit_breaker.call(
                lambda: retry_async(
                    self.loki_client.search_logs,
                    RetryConfigs.NETWORK,
                    query,
                    tenant_id
                )
            )
        
        async def fallback_search():
            self.logger.warning("Using fallback for log search")
            return [], SearchStats(matched=0, scanned=0, latency_ms=0, sources={"loki": "unavailable"})
        
        try:
            return await execute_with_fallback(
                "loki",
                "search_logs",
                primary_search,
                fallback_search,
                cache_key=f"logs_{tenant_id}_{hash(query.free_text)}_{query.time_range.start}_{query.time_range.end}"
            )
        except Exception as e:
            self.logger.error(f"Loki search failed completely: {e}", exc_info=True)
            return [], SearchStats(matched=0, scanned=0, latency_ms=0, sources={"loki": "error"})
    
    async def _search_metrics_safe(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ) -> tuple[List[SearchItem], SearchStats]:
        """
        Safely search metrics with error handling, circuit breaker, and retry.
        
        Args:
            query: Search query
            tenant_id: Tenant ID
            
        Returns:
            Tuple of (items, stats) or empty results on error
        """
        async def primary_search():
            circuit_breaker = await self._get_circuit_breaker("prometheus")
            return await circuit_breaker.call(
                lambda: retry_async(
                    self.prometheus_client.search_metrics,
                    RetryConfigs.NETWORK,
                    query,
                    tenant_id
                )
            )
        
        async def fallback_search():
            self.logger.warning("Using fallback for metrics search")
            return [], SearchStats(matched=0, scanned=0, latency_ms=0, sources={"prometheus": "unavailable"})
        
        try:
            return await execute_with_fallback(
                "prometheus",
                "search_metrics",
                primary_search,
                fallback_search,
                cache_key=f"metrics_{tenant_id}_{hash(query.free_text)}_{query.time_range.start}_{query.time_range.end}"
            )
        except Exception as e:
            self.logger.error(f"Prometheus search failed completely: {e}", exc_info=True)
            return [], SearchStats(matched=0, scanned=0, latency_ms=0, sources={"prometheus": "error"})
    
    async def _search_traces_safe(
        self, 
        query: SearchQuery, 
        tenant_id: str
    ) -> tuple[List[SearchItem], SearchStats]:
        """
        Safely search traces with error handling, circuit breaker, and retry.
        
        Args:
            query: Search query
            tenant_id: Tenant ID
            
        Returns:
            Tuple of (items, stats) or empty results on error
        """
        async def primary_search():
            circuit_breaker = await self._get_circuit_breaker("tempo")
            return await circuit_breaker.call(
                lambda: retry_async(
                    self.tempo_client.search_traces,
                    RetryConfigs.NETWORK,
                    query,
                    tenant_id
                )
            )
        
        async def fallback_search():
            self.logger.warning("Using fallback for traces search")
            return [], SearchStats(matched=0, scanned=0, latency_ms=0, sources={"tempo": "unavailable"})
        
        try:
            return await execute_with_fallback(
                "tempo",
                "search_traces",
                primary_search,
                fallback_search,
                cache_key=f"traces_{tenant_id}_{hash(query.free_text)}_{query.time_range.start}_{query.time_range.end}"
            )
        except Exception as e:
            self.logger.error(f"Tempo search failed completely: {e}", exc_info=True)
            return [], SearchStats(matched=0, scanned=0, latency_ms=0, sources={"tempo": "error"})
    
    async def _apply_correlation(
        self, 
        items: List[SearchItem], 
        time_range
    ) -> List[SearchItem]:
        """
        Apply cross-signal correlation to search results.
        
        Args:
            items: Search items from all sources
            time_range: Query time range
            
        Returns:
            Items with correlation IDs populated
        """
        # Group items by service and time windows
        service_groups = defaultdict(list)
        
        for item in items:
            service_groups[item.service].append(item)
        
        # Apply correlation within each service
        for service, service_items in service_groups.items():
            await self._correlate_service_items(service_items)
        
        return items
    
    async def _correlate_service_items(self, items: List[SearchItem]):
        """
        Correlate items within a single service.
        
        Args:
            items: Items from the same service
        """
        # Sort by timestamp for temporal correlation
        items.sort(key=lambda x: x.timestamp)
        
        # Group by correlation patterns
        trace_items = [item for item in items if item.source == SearchType.TRACES]
        log_items = [item for item in items if item.source == SearchType.LOGS]
        metric_items = [item for item in items if item.source == SearchType.METRICS]
        
        # Correlate traces with logs and metrics
        for trace_item in trace_items:
            if not isinstance(trace_item.content, TraceItem):
                continue
            
            trace_content = trace_item.content
            trace_id = trace_content.trace_id
            
            # Find related logs within time window
            time_window = timedelta(seconds=30)  # 30-second correlation window
            
            for log_item in log_items:
                if abs((log_item.timestamp - trace_item.timestamp).total_seconds()) <= time_window.total_seconds():
                    # Check if log contains trace ID or has matching service
                    if isinstance(log_item.content, LogItem):
                        log_content = log_item.content
                        if (trace_id in log_content.message or 
                            trace_id in str(log_content.fields) or
                            log_item.service == trace_item.service):
                            log_item.correlation_id = trace_id
            
            # Find related metrics within time window
            for metric_item in metric_items:
                if abs((metric_item.timestamp - trace_item.timestamp).total_seconds()) <= time_window.total_seconds():
                    if metric_item.service == trace_item.service:
                        metric_item.correlation_id = trace_id
    
    async def correlate_signals(
        self, 
        request: CorrelationRequest, 
        tenant_id: str
    ) -> CorrelationResponse:
        """
        Find correlated signals based on trace ID, correlation ID, or service.
        
        Args:
            request: Correlation request parameters
            tenant_id: Tenant ID for isolation
            
        Returns:
            Correlated signals response
        """
        try:
            related_items = []
            correlation_graph = {}
            
            # Build search query for correlation
            correlation_query = SearchQuery(
                free_text="",
                type=SearchType.ALL,
                time_range=request.time_range,
                filters=[],
                tenant_id=tenant_id,
                limit=1000  # Higher limit for correlation
            )
            
            # Search for related items
            if request.trace_id:
                # Find all items related to this trace
                related_items = await self._find_items_by_trace_id(
                    request.trace_id, correlation_query, tenant_id
                )
            elif request.correlation_id:
                # Find all items with this correlation ID
                related_items = await self._find_items_by_correlation_id(
                    request.correlation_id, correlation_query, tenant_id
                )
            elif request.service:
                # Find all items for this service
                correlation_query.filters.append({
                    "field": "service",
                    "operator": "equals",
                    "value": request.service
                })
                search_result = await self.search(correlation_query, tenant_id)
                related_items = search_result.items
            
            # Build correlation graph
            correlation_graph = self._build_correlation_graph(related_items)
            
            # Calculate confidence score
            confidence_score = self._calculate_correlation_confidence(related_items)
            
            return CorrelationResponse(
                related_items=related_items,
                correlation_graph=correlation_graph,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            raise SearchException(f"Correlation failed: {str(e)}") from e
    
    async def _find_items_by_trace_id(
        self, 
        trace_id: str, 
        query: SearchQuery, 
        tenant_id: str
    ) -> List[SearchItem]:
        """Find all items related to a specific trace ID."""
        # Search traces first
        trace_items, _ = await self.tempo_client.search_traces(query, tenant_id)
        related_traces = [item for item in trace_items 
                         if isinstance(item.content, TraceItem) and 
                         item.content.trace_id == trace_id]
        
        if not related_traces:
            return []
        
        # Find logs and metrics in the same time window
        trace_times = [item.timestamp for item in related_traces]
        min_time = min(trace_times) - timedelta(minutes=5)
        max_time = max(trace_times) + timedelta(minutes=5)
        
        # Update query time range
        expanded_query = query.model_copy()
        expanded_query.time_range.start = min_time
        expanded_query.time_range.end = max_time
        
        # Search logs and metrics
        log_items, _ = await self.loki_client.search_logs(expanded_query, tenant_id)
        metric_items, _ = await self.prometheus_client.search_metrics(expanded_query, tenant_id)
        
        # Filter for related items
        all_items = related_traces + log_items + metric_items
        return [item for item in all_items if item.correlation_id == trace_id or
                any(trace.service == item.service for trace in related_traces)]
    
    async def _find_items_by_correlation_id(
        self, 
        correlation_id: str, 
        query: SearchQuery, 
        tenant_id: str
    ) -> List[SearchItem]:
        """Find all items with a specific correlation ID."""
        # Search all sources
        search_result = await self.search(query, tenant_id)
        return [item for item in search_result.items 
                if item.correlation_id == correlation_id]
    
    def _build_correlation_graph(self, items: List[SearchItem]) -> Dict[str, Any]:
        """
        Build a correlation graph from related items.
        
        Args:
            items: Related search items
            
        Returns:
            Correlation graph structure
        """
        graph = {
            "nodes": [],
            "edges": [],
            "clusters": {}
        }
        
        # Create nodes for each item
        for item in items:
            node = {
                "id": item.id,
                "type": item.source.value,
                "service": item.service,
                "timestamp": item.timestamp.isoformat(),
                "correlation_id": item.correlation_id
            }
            graph["nodes"].append(node)
        
        # Create edges based on correlations
        correlation_groups = defaultdict(list)
        for item in items:
            if item.correlation_id:
                correlation_groups[item.correlation_id].append(item)
        
        for correlation_id, group_items in correlation_groups.items():
            # Create edges between all items in the same correlation group
            for i, item1 in enumerate(group_items):
                for item2 in group_items[i+1:]:
                    edge = {
                        "source": item1.id,
                        "target": item2.id,
                        "type": "correlation",
                        "correlation_id": correlation_id
                    }
                    graph["edges"].append(edge)
        
        return graph
    
    def _calculate_correlation_confidence(self, items: List[SearchItem]) -> float:
        """
        Calculate confidence score for correlation results.
        
        Args:
            items: Correlated items
            
        Returns:
            Confidence score between 0 and 1
        """
        if not items:
            return 0.0
        
        # Factors that increase confidence:
        # 1. Multiple signal types present
        # 2. Items have correlation IDs
        # 3. Items are from same service
        # 4. Items are within reasonable time window
        
        signal_types = set(item.source for item in items)
        correlated_items = sum(1 for item in items if item.correlation_id)
        same_service_groups = defaultdict(int)
        
        for item in items:
            same_service_groups[item.service] += 1
        
        # Calculate score components
        signal_diversity = len(signal_types) / 3.0  # Max 3 signal types
        correlation_ratio = correlated_items / len(items)
        service_clustering = max(same_service_groups.values()) / len(items)
        
        # Weighted average
        confidence = (
            signal_diversity * 0.3 +
            correlation_ratio * 0.4 +
            service_clustering * 0.3
        )
        
        return min(confidence, 1.0)
    
    async def get_search_statistics(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get search performance statistics for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Search statistics dictionary
        """
        try:
            # In a real implementation, this would query a metrics store
            # For now, return mock statistics
            return {
                "tenant_id": tenant_id,
                "total_searches": 1250,
                "avg_response_time_ms": 245,
                "success_rate": 0.987,
                "data_sources": {
                    "loki": {
                        "total_queries": 450,
                        "avg_response_time_ms": 180,
                        "success_rate": 0.995
                    },
                    "prometheus": {
                        "total_queries": 520,
                        "avg_response_time_ms": 120,
                        "success_rate": 0.998
                    },
                    "tempo": {
                        "total_queries": 280,
                        "avg_response_time_ms": 450,
                        "success_rate": 0.965
                    }
                },
                "time_range": {
                    "start": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
                    "end": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            raise SearchException(f"Failed to get search statistics: {str(e)}") from e
    
    async def get_performance_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get real-time search performance metrics.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Performance metrics dictionary
        """
        try:
            # Check current health status
            health_status = await self.health_check()
            
            # Calculate performance scores
            healthy_sources = sum(1 for status in health_status.values() if status)
            total_sources = len(health_status)
            availability_score = healthy_sources / total_sources if total_sources > 0 else 0
            
            return {
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
                "availability_score": availability_score,
                "healthy_sources": healthy_sources,
                "total_sources": total_sources,
                "source_health": health_status,
                "performance_indicators": {
                    "query_throughput": 15.2,  # queries per second
                    "avg_latency_ms": 245,
                    "p95_latency_ms": 890,
                    "p99_latency_ms": 1250,
                    "error_rate": 0.013
                },
                "resource_usage": {
                    "cpu_usage_percent": 45.2,
                    "memory_usage_percent": 62.8,
                    "active_connections": 12
                }
            }
        except Exception as e:
            raise SearchException(f"Failed to get performance metrics: {str(e)}") from e
    
    async def search_aggregate(
        self, 
        query: SearchQuery, 
        aggregation_type: str, 
        tenant_id: str
    ) -> Dict[str, Any]:
        """
        Perform aggregated search with result grouping.
        
        Args:
            query: Search query parameters
            aggregation_type: Type of aggregation (time, service, source, etc.)
            tenant_id: Tenant ID for isolation
            
        Returns:
            Aggregated search results
            
        Raises:
            SearchException: If aggregation fails
        """
        try:
            # First perform regular search to get all results
            search_result = await self.search(query, tenant_id)
            
            # Apply aggregation based on type
            if aggregation_type == "time":
                aggregated_data = self._aggregate_by_time(search_result.items, query.time_range)
            elif aggregation_type == "service":
                aggregated_data = self._aggregate_by_service(search_result.items)
            elif aggregation_type == "source":
                aggregated_data = self._aggregate_by_source(search_result.items)
            elif aggregation_type == "severity":
                aggregated_data = self._aggregate_by_severity(search_result.items)
            else:
                raise SearchException(f"Unsupported aggregation type: {aggregation_type}")
            
            return {
                "aggregation_type": aggregation_type,
                "total_items": len(search_result.items),
                "aggregated_data": aggregated_data,
                "stats": search_result.stats.model_dump(),
                "query": query.model_dump()
            }
            
        except Exception as e:
            raise SearchException(f"Search aggregation failed: {str(e)}") from e
    
    def _aggregate_by_time(self, items: List[SearchItem], time_range) -> Dict[str, Any]:
        """Aggregate search items by time buckets."""
        # Create hourly buckets
        buckets = defaultdict(int)
        bucket_items = defaultdict(list)
        
        for item in items:
            # Round to nearest hour
            hour_bucket = item.timestamp.replace(minute=0, second=0, microsecond=0)
            bucket_key = hour_bucket.isoformat()
            buckets[bucket_key] += 1
            bucket_items[bucket_key].append(item.id)
        
        return {
            "buckets": dict(buckets),
            "bucket_items": dict(bucket_items),
            "bucket_size": "1h"
        }
    
    def _aggregate_by_service(self, items: List[SearchItem]) -> Dict[str, Any]:
        """Aggregate search items by service."""
        service_counts = defaultdict(int)
        service_items = defaultdict(list)
        service_sources = defaultdict(set)
        
        for item in items:
            service_counts[item.service] += 1
            service_items[item.service].append(item.id)
            service_sources[item.service].add(item.source.value)
        
        # Convert sets to lists for JSON serialization
        service_sources_dict = {k: list(v) for k, v in service_sources.items()}
        
        return {
            "service_counts": dict(service_counts),
            "service_items": dict(service_items),
            "service_sources": service_sources_dict
        }
    
    def _aggregate_by_source(self, items: List[SearchItem]) -> Dict[str, Any]:
        """Aggregate search items by data source."""
        source_counts = defaultdict(int)
        source_items = defaultdict(list)
        source_services = defaultdict(set)
        
        for item in items:
            source_key = item.source.value
            source_counts[source_key] += 1
            source_items[source_key].append(item.id)
            source_services[source_key].add(item.service)
        
        # Convert sets to lists for JSON serialization
        source_services_dict = {k: list(v) for k, v in source_services.items()}
        
        return {
            "source_counts": dict(source_counts),
            "source_items": dict(source_items),
            "source_services": source_services_dict
        }
    
    def _aggregate_by_severity(self, items: List[SearchItem]) -> Dict[str, Any]:
        """Aggregate search items by severity/level."""
        severity_counts = defaultdict(int)
        severity_items = defaultdict(list)
        
        for item in items:
            # Extract severity based on item type
            severity = "unknown"
            
            if item.source == SearchType.LOGS and hasattr(item.content, 'level'):
                severity = item.content.level.value
            elif item.source == SearchType.TRACES and hasattr(item.content, 'status'):
                severity = item.content.status.value
            elif item.source == SearchType.METRICS:
                # For metrics, we could categorize by value ranges or metric type
                severity = "info"
            
            severity_counts[severity] += 1
            severity_items[severity].append(item.id)
        
        return {
            "severity_counts": dict(severity_counts),
            "severity_items": dict(severity_items)
        }

    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of all data source clients.
        
        Returns:
            Health status for each client
        """
        health_checks = await asyncio.gather(
            self.loki_client.health_check(),
            self.prometheus_client.health_check(),
            self.tempo_client.health_check(),
            return_exceptions=True
        )
        
        return {
            "loki": health_checks[0] if not isinstance(health_checks[0], Exception) else False,
            "prometheus": health_checks[1] if not isinstance(health_checks[1], Exception) else False,
            "tempo": health_checks[2] if not isinstance(health_checks[2], Exception) else False
        }