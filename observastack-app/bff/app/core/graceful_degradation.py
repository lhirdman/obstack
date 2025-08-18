"""Graceful degradation system for handling service unavailability."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, TypeVar, Awaitable, Union
from dataclasses import dataclass, field
from enum import Enum

from .logging import get_logger
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerError

logger = get_logger("graceful_degradation")

T = TypeVar('T')


class ServiceLevel(Enum):
    """Service availability levels."""
    FULL = "full"              # All features available
    DEGRADED = "degraded"      # Some features unavailable
    MINIMAL = "minimal"        # Only core features available
    UNAVAILABLE = "unavailable"  # Service completely unavailable


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior."""
    enable_cache: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    enable_mock_data: bool = True
    enable_partial_results: bool = True
    timeout_seconds: float = 30.0
    max_retries: int = 3


@dataclass
class ServiceStatus:
    """Status of a service or feature."""
    name: str
    level: ServiceLevel
    last_check: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    fallback_active: bool = False
    metrics: Dict[str, Any] = field(default_factory=dict)


class GracefulDegradationManager:
    """Manager for graceful service degradation."""
    
    def __init__(self):
        self.services: Dict[str, ServiceStatus] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.fallback_cache: Dict[str, Any] = {}
        self.config = FallbackConfig()
        self._lock = asyncio.Lock()
    
    async def register_service(
        self,
        name: str,
        health_check: Optional[Callable[[], Awaitable[bool]]] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Register a service for degradation management.
        
        Args:
            name: Service name
            health_check: Optional health check function
            circuit_breaker_config: Circuit breaker configuration
        """
        async with self._lock:
            self.services[name] = ServiceStatus(name=name, level=ServiceLevel.FULL)
            
            # Create circuit breaker for the service
            if circuit_breaker_config:
                self.circuit_breakers[name] = CircuitBreaker(
                    name=f"service_{name}",
                    config=circuit_breaker_config
                )
            
            logger.info(f"Registered service '{name}' for graceful degradation")
    
    async def check_service_health(self, name: str) -> ServiceLevel:
        """
        Check the health of a specific service.
        
        Args:
            name: Service name
            
        Returns:
            Current service level
        """
        if name not in self.services:
            logger.warning(f"Service '{name}' not registered")
            return ServiceLevel.UNAVAILABLE
        
        service = self.services[name]
        
        try:
            # Check circuit breaker status
            if name in self.circuit_breakers:
                breaker = self.circuit_breakers[name]
                stats = breaker.get_stats()
                
                if stats["state"] == "open":
                    service.level = ServiceLevel.UNAVAILABLE
                    service.error_message = "Circuit breaker is open"
                elif stats["state"] == "half_open":
                    service.level = ServiceLevel.DEGRADED
                    service.error_message = "Circuit breaker is testing recovery"
                else:
                    # Circuit is closed, service should be healthy
                    if stats["failure_rate"] > 0.5:  # More than 50% failure rate
                        service.level = ServiceLevel.DEGRADED
                        service.error_message = f"High failure rate: {stats['failure_rate']:.2%}"
                    else:
                        service.level = ServiceLevel.FULL
                        service.error_message = None
            
            service.last_check = datetime.utcnow()
            
            logger.debug(
                f"Service '{name}' health check: {service.level.value}",
                extra={
                    "service": {
                        "name": name,
                        "level": service.level.value,
                        "error": service.error_message
                    }
                }
            )
            
            return service.level
            
        except Exception as e:
            service.level = ServiceLevel.UNAVAILABLE
            service.error_message = str(e)
            service.last_check = datetime.utcnow()
            
            logger.error(
                f"Health check failed for service '{name}': {e}",
                exc_info=True,
                extra={"service": name}
            )
            
            return ServiceLevel.UNAVAILABLE
    
    async def execute_with_fallback(
        self,
        service_name: str,
        operation: str,
        primary_func: Callable[..., Awaitable[T]],
        fallback_func: Optional[Callable[..., Awaitable[T]]] = None,
        cache_key: Optional[str] = None,
        *args,
        **kwargs
    ) -> T:
        """
        Execute an operation with fallback mechanisms.
        
        Args:
            service_name: Name of the service
            operation: Operation name for logging
            primary_func: Primary function to execute
            fallback_func: Fallback function if primary fails
            cache_key: Cache key for storing/retrieving results
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Operation result
        """
        service_level = await self.check_service_health(service_name)
        
        # Try to get cached result first if service is degraded
        if (service_level in [ServiceLevel.DEGRADED, ServiceLevel.UNAVAILABLE] and 
            cache_key and self.config.enable_cache):
            
            cached_result = await self._get_cached_result(cache_key)
            if cached_result is not None:
                logger.info(
                    f"Returning cached result for {operation} due to service degradation",
                    extra={
                        "service": service_name,
                        "operation": operation,
                        "cache_key": cache_key,
                        "service_level": service_level.value
                    }
                )
                return cached_result
        
        # Try primary function if service is available
        if service_level in [ServiceLevel.FULL, ServiceLevel.DEGRADED]:
            try:
                # Use circuit breaker if available
                if service_name in self.circuit_breakers:
                    breaker = self.circuit_breakers[service_name]
                    result = await breaker.call(primary_func, *args, **kwargs)
                else:
                    result = await primary_func(*args, **kwargs)
                
                # Cache successful result
                if cache_key and self.config.enable_cache:
                    await self._cache_result(cache_key, result)
                
                # Update service status on success
                if service_name in self.services:
                    self.services[service_name].fallback_active = False
                
                return result
                
            except (CircuitBreakerError, Exception) as e:
                logger.warning(
                    f"Primary function failed for {operation}: {e}",
                    extra={
                        "service": service_name,
                        "operation": operation,
                        "error": str(e)
                    }
                )
                
                # Mark service as using fallback
                if service_name in self.services:
                    self.services[service_name].fallback_active = True
        
        # Try fallback function
        if fallback_func:
            try:
                logger.info(
                    f"Executing fallback for {operation}",
                    extra={
                        "service": service_name,
                        "operation": operation,
                        "service_level": service_level.value
                    }
                )
                
                result = await fallback_func(*args, **kwargs)
                
                # Cache fallback result with shorter TTL
                if cache_key and self.config.enable_cache:
                    await self._cache_result(cache_key, result, ttl=60)  # 1 minute TTL
                
                return result
                
            except Exception as e:
                logger.error(
                    f"Fallback function also failed for {operation}: {e}",
                    exc_info=True,
                    extra={
                        "service": service_name,
                        "operation": operation
                    }
                )
        
        # Try cached result as last resort
        if cache_key and self.config.enable_cache:
            cached_result = await self._get_cached_result(cache_key, ignore_ttl=True)
            if cached_result is not None:
                logger.warning(
                    f"Returning stale cached result for {operation} as last resort",
                    extra={
                        "service": service_name,
                        "operation": operation,
                        "cache_key": cache_key
                    }
                )
                return cached_result
        
        # Generate mock data if enabled
        if self.config.enable_mock_data:
            mock_result = await self._generate_mock_result(service_name, operation)
            if mock_result is not None:
                logger.warning(
                    f"Returning mock data for {operation}",
                    extra={
                        "service": service_name,
                        "operation": operation
                    }
                )
                return mock_result
        
        # All fallback mechanisms exhausted
        raise Exception(f"All fallback mechanisms exhausted for {service_name}.{operation}")
    
    async def _get_cached_result(self, cache_key: str, ignore_ttl: bool = False) -> Optional[Any]:
        """Get result from cache."""
        if cache_key not in self.fallback_cache:
            return None
        
        cached_item = self.fallback_cache[cache_key]
        
        if not ignore_ttl:
            # Check if cache entry is still valid
            age = (datetime.utcnow() - cached_item["timestamp"]).total_seconds()
            if age > self.config.cache_ttl_seconds:
                # Remove expired entry
                del self.fallback_cache[cache_key]
                return None
        
        return cached_item["data"]
    
    async def _cache_result(self, cache_key: str, result: Any, ttl: Optional[int] = None):
        """Cache a result."""
        self.fallback_cache[cache_key] = {
            "data": result,
            "timestamp": datetime.utcnow(),
            "ttl": ttl or self.config.cache_ttl_seconds
        }
        
        # Clean up old cache entries (simple cleanup)
        if len(self.fallback_cache) > 1000:  # Limit cache size
            # Remove oldest 10% of entries
            sorted_items = sorted(
                self.fallback_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            
            for key, _ in sorted_items[:100]:
                del self.fallback_cache[key]
    
    async def _generate_mock_result(self, service_name: str, operation: str) -> Optional[Any]:
        """Generate mock data for an operation."""
        # This is a simple mock data generator
        # In a real implementation, you might have more sophisticated mock data
        
        mock_data_templates = {
            "search": {
                "items": [],
                "stats": {
                    "matched": 0,
                    "scanned": 0,
                    "latency_ms": 0,
                    "sources": {}
                },
                "facets": [],
                "next_token": None
            },
            "alerts": {
                "alerts": [],
                "total": 0
            },
            "metrics": {
                "data": [],
                "status": "success"
            },
            "health": {
                "status": "degraded",
                "message": f"Service {service_name} is temporarily unavailable"
            }
        }
        
        # Try to match operation to a template
        for template_key, template_data in mock_data_templates.items():
            if template_key in operation.lower():
                return template_data
        
        # Default empty response
        return {"status": "unavailable", "message": "Service temporarily unavailable"}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        service_levels = [service.level for service in self.services.values()]
        
        if not service_levels:
            overall_level = ServiceLevel.FULL
        elif all(level == ServiceLevel.FULL for level in service_levels):
            overall_level = ServiceLevel.FULL
        elif all(level == ServiceLevel.UNAVAILABLE for level in service_levels):
            overall_level = ServiceLevel.UNAVAILABLE
        elif any(level == ServiceLevel.UNAVAILABLE for level in service_levels):
            overall_level = ServiceLevel.DEGRADED
        else:
            overall_level = ServiceLevel.DEGRADED
        
        return {
            "overall_level": overall_level.value,
            "services": {
                name: {
                    "level": service.level.value,
                    "last_check": service.last_check.isoformat(),
                    "error_message": service.error_message,
                    "fallback_active": service.fallback_active
                }
                for name, service in self.services.items()
            },
            "circuit_breakers": {
                name: breaker.get_stats()
                for name, breaker in self.circuit_breakers.items()
            },
            "cache_size": len(self.fallback_cache),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def force_service_level(self, service_name: str, level: ServiceLevel):
        """Force a service to a specific level (for testing)."""
        if service_name in self.services:
            self.services[service_name].level = level
            self.services[service_name].last_check = datetime.utcnow()
            
            logger.info(
                f"Forced service '{service_name}' to level '{level.value}'",
                extra={
                    "service": service_name,
                    "forced_level": level.value
                }
            )


# Global degradation manager instance
degradation_manager = GracefulDegradationManager()


# Convenience functions
async def execute_with_fallback(
    service_name: str,
    operation: str,
    primary_func: Callable[..., Awaitable[T]],
    fallback_func: Optional[Callable[..., Awaitable[T]]] = None,
    cache_key: Optional[str] = None,
    *args,
    **kwargs
) -> T:
    """Execute an operation with fallback mechanisms."""
    return await degradation_manager.execute_with_fallback(
        service_name, operation, primary_func, fallback_func, cache_key, *args, **kwargs
    )


async def register_service_for_degradation(
    name: str,
    health_check: Optional[Callable[[], Awaitable[bool]]] = None,
    circuit_breaker_config: Optional[CircuitBreakerConfig] = None
):
    """Register a service for graceful degradation."""
    await degradation_manager.register_service(name, health_check, circuit_breaker_config)