"""Tests for resilience mechanisms (circuit breaker, retry, graceful degradation)."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

from app.core.circuit_breaker import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState, CircuitBreakerError
)
from app.core.retry import (
    retry_async, RetryConfig, RetryExhaustedError, calculate_delay
)
from app.core.graceful_degradation import (
    GracefulDegradationManager, ServiceLevel, FallbackConfig
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1.0,
            success_threshold=2,
            timeout=0.5
        )
        return CircuitBreaker("test_service", config)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self, circuit_breaker):
        """Test circuit breaker in closed state."""
        async def successful_operation():
            return "success"
        
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"
        assert circuit_breaker.stats.state == CircuitState.CLOSED
        assert circuit_breaker.stats.success_count == 1
        assert circuit_breaker.stats.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_on_failures(self, circuit_breaker):
        """Test circuit breaker opens after threshold failures."""
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # First 2 failures should not open the circuit
        for i in range(2):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
            assert circuit_breaker.stats.state == CircuitState.CLOSED
        
        # Third failure should open the circuit
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_operation)
        assert circuit_breaker.stats.state == CircuitState.OPEN
        assert circuit_breaker.stats.failure_count == 3
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_when_open(self, circuit_breaker):
        """Test circuit breaker rejects calls when open."""
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
        
        assert circuit_breaker.stats.state == CircuitState.OPEN
        
        # Should reject immediately
        with pytest.raises(CircuitBreakerError):
            await circuit_breaker.call(failing_operation)
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_half_open_transition(self, circuit_breaker):
        """Test circuit breaker transitions to half-open after timeout."""
        async def failing_operation():
            raise Exception("Service unavailable")
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_operation)
        
        assert circuit_breaker.stats.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Next call should transition to half-open
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_operation)
        
        # Should be back to open after failure in half-open
        assert circuit_breaker.stats.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_successes(self, circuit_breaker):
        """Test circuit breaker closes after successful operations in half-open."""
        call_count = 0
        
        async def intermittent_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception("Service unavailable")
            return "success"
        
        # Open the circuit
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(intermittent_operation)
        
        assert circuit_breaker.stats.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Successful operations should close the circuit
        for i in range(2):  # success_threshold = 2
            result = await circuit_breaker.call(intermittent_operation)
            assert result == "success"
        
        assert circuit_breaker.stats.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_timeout(self, circuit_breaker):
        """Test circuit breaker handles timeouts."""
        async def slow_operation():
            await asyncio.sleep(1.0)  # Longer than timeout
            return "success"
        
        with pytest.raises(TimeoutError):
            await circuit_breaker.call(slow_operation)
        
        assert circuit_breaker.stats.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_context_manager(self, circuit_breaker):
        """Test circuit breaker context manager."""
        async with circuit_breaker.protect():
            # Should not raise any exception
            pass
        
        assert circuit_breaker.stats.success_count == 1
        
        # Test with exception
        with pytest.raises(Exception):
            async with circuit_breaker.protect():
                raise Exception("Test error")
        
        assert circuit_breaker.stats.failure_count == 1


class TestRetryMechanism:
    """Test retry mechanism functionality."""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test retry succeeds on first attempt."""
        async def successful_operation():
            return "success"
        
        config = RetryConfig(max_attempts=3)
        result = await retry_async(successful_operation, config)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry succeeds after initial failures."""
        call_count = 0
        
        async def intermittent_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        config = RetryConfig(max_attempts=5, base_delay=0.1)
        result = await retry_async(intermittent_operation, config)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Test retry exhaustion after max attempts."""
        async def always_failing_operation():
            raise Exception("Permanent failure")
        
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        
        with pytest.raises(RetryExhaustedError) as exc_info:
            await retry_async(always_failing_operation, config)
        
        assert exc_info.value.attempts == 3
        assert "Permanent failure" in str(exc_info.value.last_exception)
    
    @pytest.mark.asyncio
    async def test_retry_non_retryable_exception(self):
        """Test non-retryable exceptions are not retried."""
        class NonRetryableError(Exception):
            pass
        
        async def operation_with_non_retryable_error():
            raise NonRetryableError("Should not retry")
        
        config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            retryable_exceptions=(ValueError,)  # Only ValueError is retryable
        )
        
        with pytest.raises(NonRetryableError):
            await retry_async(operation_with_non_retryable_error, config)
    
    def test_calculate_delay(self):
        """Test delay calculation with exponential backoff."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False
        )
        
        # Test exponential backoff
        assert calculate_delay(1, config) == 1.0  # 1.0 * (2^0)
        assert calculate_delay(2, config) == 2.0  # 1.0 * (2^1)
        assert calculate_delay(3, config) == 4.0  # 1.0 * (2^2)
        assert calculate_delay(4, config) == 8.0  # 1.0 * (2^3)
        
        # Test max delay cap
        assert calculate_delay(5, config) == 10.0  # Capped at max_delay
    
    def test_calculate_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=True
        )
        
        # With jitter, delay should vary but be in reasonable range
        delays = [calculate_delay(2, config) for _ in range(10)]
        
        # All delays should be positive
        assert all(delay > 0 for delay in delays)
        
        # Should have some variation (not all the same)
        assert len(set(delays)) > 1


class TestGracefulDegradation:
    """Test graceful degradation functionality."""
    
    @pytest.fixture
    def degradation_manager(self):
        """Create a degradation manager for testing."""
        return GracefulDegradationManager()
    
    @pytest.mark.asyncio
    async def test_service_registration(self, degradation_manager):
        """Test service registration."""
        await degradation_manager.register_service("test_service")
        
        assert "test_service" in degradation_manager.services
        service = degradation_manager.services["test_service"]
        assert service.name == "test_service"
        assert service.level == ServiceLevel.FULL
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_success(self, degradation_manager):
        """Test successful execution without fallback."""
        await degradation_manager.register_service("test_service")
        
        async def primary_operation():
            return "primary_result"
        
        async def fallback_operation():
            return "fallback_result"
        
        result = await degradation_manager.execute_with_fallback(
            "test_service",
            "test_operation",
            primary_operation,
            fallback_operation
        )
        
        assert result == "primary_result"
    
    @pytest.mark.asyncio
    async def test_execute_with_fallback_failure(self, degradation_manager):
        """Test fallback execution when primary fails."""
        await degradation_manager.register_service("test_service")
        
        async def failing_primary():
            raise Exception("Primary failed")
        
        async def fallback_operation():
            return "fallback_result"
        
        result = await degradation_manager.execute_with_fallback(
            "test_service",
            "test_operation",
            failing_primary,
            fallback_operation
        )
        
        assert result == "fallback_result"
        assert degradation_manager.services["test_service"].fallback_active
    
    @pytest.mark.asyncio
    async def test_caching_mechanism(self, degradation_manager):
        """Test result caching and retrieval."""
        await degradation_manager.register_service("test_service")
        
        call_count = 0
        
        async def primary_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "cached_result"
            raise Exception("Should use cache")
        
        # First call should succeed and cache result
        result1 = await degradation_manager.execute_with_fallback(
            "test_service",
            "test_operation",
            primary_operation,
            cache_key="test_cache_key"
        )
        assert result1 == "cached_result"
        
        # Force service to unavailable
        await degradation_manager.force_service_level("test_service", ServiceLevel.UNAVAILABLE)
        
        # Second call should return cached result
        result2 = await degradation_manager.execute_with_fallback(
            "test_service",
            "test_operation",
            primary_operation,
            cache_key="test_cache_key"
        )
        assert result2 == "cached_result"
        assert call_count == 1  # Primary function called only once
    
    @pytest.mark.asyncio
    async def test_mock_data_generation(self, degradation_manager):
        """Test mock data generation when all else fails."""
        await degradation_manager.register_service("test_service")
        
        async def failing_operation():
            raise Exception("Always fails")
        
        # Force service to unavailable
        await degradation_manager.force_service_level("test_service", ServiceLevel.UNAVAILABLE)
        
        result = await degradation_manager.execute_with_fallback(
            "test_service",
            "search_operation",
            failing_operation
        )
        
        # Should return mock search data
        assert isinstance(result, dict)
        assert "items" in result
        assert result["items"] == []
    
    def test_system_status(self, degradation_manager):
        """Test system status reporting."""
        # Add some services
        asyncio.run(degradation_manager.register_service("service1"))
        asyncio.run(degradation_manager.register_service("service2"))
        
        # Force different service levels
        asyncio.run(degradation_manager.force_service_level("service1", ServiceLevel.FULL))
        asyncio.run(degradation_manager.force_service_level("service2", ServiceLevel.DEGRADED))
        
        status = degradation_manager.get_system_status()
        
        assert status["overall_level"] == ServiceLevel.DEGRADED.value
        assert "service1" in status["services"]
        assert "service2" in status["services"]
        assert status["services"]["service1"]["level"] == ServiceLevel.FULL.value
        assert status["services"]["service2"]["level"] == ServiceLevel.DEGRADED.value


class TestIntegration:
    """Integration tests for resilience mechanisms."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry(self):
        """Test circuit breaker working with retry mechanism."""
        from app.core.circuit_breaker import CircuitBreakerConfig, get_circuit_breaker
        from app.core.retry import retry_async, RetryConfig
        
        # Create circuit breaker
        cb_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.5)
        circuit_breaker = await get_circuit_breaker("integration_test", cb_config)
        
        call_count = 0
        
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 5:  # Fail first 5 calls
                raise Exception("Service error")
            return "success"
        
        # Retry with circuit breaker protection
        retry_config = RetryConfig(max_attempts=3, base_delay=0.1)
        
        # First retry attempt should fail and open circuit breaker
        with pytest.raises(RetryExhaustedError):
            await retry_async(
                lambda: circuit_breaker.call(flaky_operation),
                retry_config
            )
        
        # Circuit should be open now
        stats = circuit_breaker.get_stats()
        assert stats["state"] == "open"
        
        # Wait for circuit breaker recovery
        await asyncio.sleep(0.6)
        
        # Should eventually succeed after circuit breaker recovers
        result = await retry_async(
            lambda: circuit_breaker.call(flaky_operation),
            retry_config
        )
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_full_resilience_stack(self):
        """Test complete resilience stack integration."""
        from app.core.graceful_degradation import GracefulDegradationManager
        from app.core.circuit_breaker import CircuitBreakerConfig
        
        manager = GracefulDegradationManager()
        
        # Register service with circuit breaker
        cb_config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.5)
        await manager.register_service("resilient_service", circuit_breaker_config=cb_config)
        
        call_count = 0
        
        async def unreliable_primary():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise Exception("Primary service error")
            return "primary_success"
        
        async def reliable_fallback():
            return "fallback_success"
        
        # First few calls should use fallback due to primary failures
        for i in range(2):
            result = await manager.execute_with_fallback(
                "resilient_service",
                "test_operation",
                unreliable_primary,
                reliable_fallback,
                cache_key=f"test_key_{i}"
            )
            assert result == "fallback_success"
        
        # Wait for circuit breaker recovery
        await asyncio.sleep(0.6)
        
        # Eventually should succeed with primary
        result = await manager.execute_with_fallback(
            "resilient_service",
            "test_operation",
            unreliable_primary,
            reliable_fallback
        )
        assert result == "primary_success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])