"""Load tests for performance validation."""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
import statistics
from typing import List, Dict, Any


class TestPerformance:
    """Performance and load test cases."""

    @pytest.fixture
    def performance_client(self):
        """Test client optimized for performance testing."""
        from app.main import app
        return TestClient(app)

    @pytest.fixture
    def async_performance_client(self):
        """Async test client for concurrent testing."""
        from app.main import app
        return AsyncClient(app=app, base_url="http://test")

    def test_search_endpoint_response_time(self, performance_client, auth_headers):
        """Test search endpoint response time under normal load."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = {
                "items": [{"id": f"item-{i}", "timestamp": "2025-08-16T07:30:00Z"} for i in range(100)],
                "stats": {"matched": 100, "scanned": 1000, "latencyMs": 50, "sources": {"logs": 100}},
                "facets": []
            }
            
            response_times = []
            
            # Perform multiple requests to measure response time
            for _ in range(10):
                start_time = time.time()
                
                response = performance_client.post(
                    "/api/v1/search",
                    json={
                        "freeText": "performance test",
                        "type": "logs",
                        "tenantId": "test-tenant-456",
                        "limit": 100
                    },
                    headers=auth_headers
                )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                assert response.status_code == 200
                response_times.append(response_time)
            
            # Performance assertions
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            assert avg_response_time < 200, f"Average response time {avg_response_time}ms exceeds 200ms"
            assert max_response_time < 500, f"Max response time {max_response_time}ms exceeds 500ms"

    @pytest.mark.asyncio
    async def test_concurrent_search_requests(self, async_performance_client, auth_headers):
        """Test search endpoint under concurrent load."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = {
                "items": [{"id": "item-1", "timestamp": "2025-08-16T07:30:00Z"}],
                "stats": {"matched": 1, "scanned": 100, "latencyMs": 25, "sources": {"logs": 1}},
                "facets": []
            }
            
            # Create concurrent requests
            async def make_request(request_id: int):
                start_time = time.time()
                
                response = await async_performance_client.post(
                    "/api/v1/search",
                    json={
                        "freeText": f"concurrent test {request_id}",
                        "type": "logs",
                        "tenantId": "test-tenant-456"
                    },
                    headers=auth_headers
                )
                
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000
                }
            
            # Execute 20 concurrent requests
            tasks = [make_request(i) for i in range(20)]
            results = await asyncio.gather(*tasks)
            
            # Analyze results
            successful_requests = [r for r in results if r["status_code"] == 200]
            response_times = [r["response_time"] for r in successful_requests]
            
            assert len(successful_requests) == 20, "Not all concurrent requests succeeded"
            
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 300, f"Average concurrent response time {avg_response_time}ms exceeds 300ms"

    def test_memory_usage_under_load(self, performance_client, auth_headers):
        """Test memory usage under sustained load."""
        import psutil
        import os
        
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Large response to test memory handling
            large_response = {
                "items": [
                    {
                        "id": f"item-{i}",
                        "timestamp": "2025-08-16T07:30:00Z",
                        "content": {"message": "x" * 1000}  # 1KB per item
                    }
                    for i in range(1000)  # 1MB total
                ],
                "stats": {"matched": 1000, "scanned": 10000, "latencyMs": 100, "sources": {"logs": 1000}},
                "facets": []
            }
            
            mock_search.return_value = large_response
            
            # Get initial memory usage
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Make multiple requests with large responses
            for _ in range(10):
                response = performance_client.post(
                    "/api/v1/search",
                    json={
                        "freeText": "memory test",
                        "type": "logs",
                        "tenantId": "test-tenant-456",
                        "limit": 1000
                    },
                    headers=auth_headers
                )
                assert response.status_code == 200
            
            # Check memory usage after requests
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100, f"Memory increased by {memory_increase}MB, possible memory leak"

    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self, async_performance_client, auth_headers):
        """Test database connection pool under load."""
        with patch('app.api.v1.alerts.get_current_user') as mock_get_user, \
             patch('app.services.alert_service.AlertService.get_alerts') as mock_get_alerts:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["operator"]
            }
            
            mock_get_alerts.return_value = {
                "alerts": [{"id": f"alert-{i}", "title": f"Alert {i}"} for i in range(50)],
                "total": 50,
                "hasMore": False
            }
            
            # Simulate database queries with varying response times
            async def simulate_db_query():
                await asyncio.sleep(0.01)  # Simulate 10ms DB query
                return mock_get_alerts.return_value
            
            mock_get_alerts.side_effect = lambda *args, **kwargs: simulate_db_query()
            
            # Make concurrent requests that would use database connections
            async def make_db_request(request_id: int):
                start_time = time.time()
                
                response = await async_performance_client.get(
                    "/api/v1/alerts",
                    headers=auth_headers
                )
                
                end_time = time.time()
                return {
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000
                }
            
            # Execute 50 concurrent database requests
            tasks = [make_db_request(i) for i in range(50)]
            results = await asyncio.gather(*tasks)
            
            # All requests should succeed without connection pool exhaustion
            successful_requests = [r for r in results if r["status_code"] == 200]
            assert len(successful_requests) == 50, "Database connection pool may be exhausted"

    def test_cache_performance(self, performance_client, auth_headers):
        """Test caching performance and hit rates."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search, \
             patch('app.core.cache.get_cached_result') as mock_cache_get, \
             patch('app.core.cache.set_cached_result') as mock_cache_set:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            search_result = {
                "items": [{"id": "cached-item", "timestamp": "2025-08-16T07:30:00Z"}],
                "stats": {"matched": 1, "scanned": 100, "latencyMs": 25, "sources": {"logs": 1}},
                "facets": []
            }
            
            mock_search.return_value = search_result
            
            # First request - cache miss
            mock_cache_get.return_value = None
            
            start_time = time.time()
            response1 = performance_client.post(
                "/api/v1/search",
                json={
                    "freeText": "cache test",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            cache_miss_time = (time.time() - start_time) * 1000
            
            assert response1.status_code == 200
            mock_search.assert_called_once()
            mock_cache_set.assert_called_once()
            
            # Second request - cache hit
            mock_cache_get.return_value = search_result
            mock_search.reset_mock()
            
            start_time = time.time()
            response2 = performance_client.post(
                "/api/v1/search",
                json={
                    "freeText": "cache test",
                    "type": "logs",
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            cache_hit_time = (time.time() - start_time) * 1000
            
            assert response2.status_code == 200
            mock_search.assert_not_called()  # Should use cache
            
            # Cache hit should be significantly faster
            assert cache_hit_time < cache_miss_time * 0.5, "Cache hit not significantly faster than cache miss"

    @pytest.mark.asyncio
    async def test_rate_limiting_performance(self, async_performance_client, auth_headers):
        """Test rate limiting performance and accuracy."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.core.rate_limiter.is_rate_limited') as mock_rate_limit:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Configure rate limiting
            request_count = 0
            
            def rate_limit_check(*args, **kwargs):
                nonlocal request_count
                request_count += 1
                return request_count > 10  # Allow first 10 requests
            
            mock_rate_limit.side_effect = rate_limit_check
            
            # Make requests rapidly
            async def make_rapid_request(request_id: int):
                response = await async_performance_client.post(
                    "/api/v1/search",
                    json={
                        "freeText": f"rate limit test {request_id}",
                        "type": "logs",
                        "tenantId": "test-tenant-456"
                    },
                    headers=auth_headers
                )
                return response.status_code
            
            # Execute 20 rapid requests
            tasks = [make_rapid_request(i) for i in range(20)]
            status_codes = await asyncio.gather(*tasks)
            
            # First 10 should succeed, rest should be rate limited
            successful_requests = sum(1 for code in status_codes if code == 200)
            rate_limited_requests = sum(1 for code in status_codes if code == 429)
            
            assert successful_requests <= 10, "Rate limiting not working correctly"
            assert rate_limited_requests >= 10, "Rate limiting not blocking excess requests"

    def test_large_payload_performance(self, performance_client, auth_headers):
        """Test performance with large request payloads."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = {
                "items": [],
                "stats": {"matched": 0, "scanned": 0, "latencyMs": 10, "sources": {}},
                "facets": []
            }
            
            # Create large filter payload
            large_filters = [
                {
                    "field": f"field_{i}",
                    "operator": "equals",
                    "value": f"value_{i}" * 100  # Large value
                }
                for i in range(100)  # 100 filters
            ]
            
            start_time = time.time()
            
            response = performance_client.post(
                "/api/v1/search",
                json={
                    "freeText": "large payload test",
                    "type": "logs",
                    "filters": large_filters,
                    "tenantId": "test-tenant-456"
                },
                headers=auth_headers
            )
            
            response_time = (time.time() - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time < 1000, f"Large payload response time {response_time}ms exceeds 1000ms"

    @pytest.mark.asyncio
    async def test_error_handling_performance(self, async_performance_client, auth_headers):
        """Test error handling performance under load."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            # Simulate service errors
            mock_search.side_effect = Exception("Service unavailable")
            
            # Make multiple requests that will fail
            async def make_error_request(request_id: int):
                start_time = time.time()
                
                response = await async_performance_client.post(
                    "/api/v1/search",
                    json={
                        "freeText": f"error test {request_id}",
                        "type": "logs",
                        "tenantId": "test-tenant-456"
                    },
                    headers=auth_headers
                )
                
                end_time = time.time()
                return {
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000
                }
            
            # Execute concurrent error requests
            tasks = [make_error_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            
            # All should return 500 errors quickly
            error_responses = [r for r in results if r["status_code"] == 500]
            response_times = [r["response_time"] for r in error_responses]
            
            assert len(error_responses) == 10, "Not all requests returned expected error"
            
            avg_error_response_time = statistics.mean(response_times)
            assert avg_error_response_time < 100, f"Error response time {avg_error_response_time}ms too slow"

    def test_throughput_measurement(self, performance_client, auth_headers):
        """Measure API throughput (requests per second)."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = {
                "items": [{"id": "throughput-item"}],
                "stats": {"matched": 1, "scanned": 10, "latencyMs": 5, "sources": {"logs": 1}},
                "facets": []
            }
            
            # Measure throughput over 5 seconds
            start_time = time.time()
            end_time = start_time + 5  # 5 second test
            request_count = 0
            
            while time.time() < end_time:
                response = performance_client.post(
                    "/api/v1/search",
                    json={
                        "freeText": f"throughput test {request_count}",
                        "type": "logs",
                        "tenantId": "test-tenant-456"
                    },
                    headers=auth_headers
                )
                
                if response.status_code == 200:
                    request_count += 1
            
            actual_duration = time.time() - start_time
            throughput = request_count / actual_duration
            
            # Should handle at least 10 requests per second
            assert throughput >= 10, f"Throughput {throughput:.2f} req/s below minimum of 10 req/s"

    @pytest.mark.benchmark
    def test_search_endpoint_benchmark(self, benchmark, performance_client, auth_headers):
        """Benchmark search endpoint using pytest-benchmark."""
        with patch('app.api.v1.search.get_current_user') as mock_get_user, \
             patch('app.services.search_service.SearchService.search') as mock_search:
            
            mock_get_user.return_value = {
                "user_id": "test-user-123",
                "tenant_id": "test-tenant-456",
                "roles": ["user"]
            }
            
            mock_search.return_value = {
                "items": [{"id": "benchmark-item"}],
                "stats": {"matched": 1, "scanned": 10, "latencyMs": 5, "sources": {"logs": 1}},
                "facets": []
            }
            
            def search_request():
                return performance_client.post(
                    "/api/v1/search",
                    json={
                        "freeText": "benchmark test",
                        "type": "logs",
                        "tenantId": "test-tenant-456"
                    },
                    headers=auth_headers
                )
            
            # Benchmark the search request
            result = benchmark(search_request)
            assert result.status_code == 200