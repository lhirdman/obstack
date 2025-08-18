"""Circuit breaker pattern implementation for resilient service calls."""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Generic, Awaitable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from .logging import get_logger

logger = get_logger("circuit_breaker")

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: float = 60.0  # Seconds to wait before trying again
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: float = 30.0  # Request timeout in seconds
    expected_exceptions: tuple = (Exception,)  # Exceptions that count as failures


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation for protecting against cascading failures.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker for logging
            config: Configuration options
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        logger.info(f"Circuit breaker '{name}' initialized", extra={
            "circuit_breaker": {
                "name": name,
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout": self.config.recovery_timeout,
                    "success_threshold": self.config.success_threshold,
                    "timeout": self.config.timeout
                }
            }
        })
    
    async def call(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            TimeoutError: If function times out
            Exception: Original function exceptions
        """
        async with self._lock:
            self.stats.total_requests += 1
            
            # Check if circuit should transition states
            await self._check_state_transition()
            
            # Reject if circuit is open
            if self.stats.state == CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker '{self.name}' is open, rejecting request",
                    extra={
                        "circuit_breaker": {
                            "name": self.name,
                            "state": self.stats.state.value,
                            "failure_count": self.stats.failure_count
                        }
                    }
                )
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
        
        # Execute the function with timeout
        try:
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout
            )
            
            # Record success
            await self._record_success()
            return result
            
        except asyncio.TimeoutError as e:
            await self._record_failure()
            logger.warning(
                f"Circuit breaker '{self.name}' request timed out",
                extra={
                    "circuit_breaker": {
                        "name": self.name,
                        "timeout": self.config.timeout,
                        "error": str(e)
                    }
                }
            )
            raise TimeoutError(f"Request timed out after {self.config.timeout}s") from e
            
        except self.config.expected_exceptions as e:
            await self._record_failure()
            logger.warning(
                f"Circuit breaker '{self.name}' request failed",
                exc_info=True,
                extra={
                    "circuit_breaker": {
                        "name": self.name,
                        "error_type": type(e).__name__,
                        "error": str(e)
                    }
                }
            )
            raise
    
    @asynccontextmanager
    async def protect(self):
        """
        Context manager for protecting code blocks.
        
        Usage:
            async with circuit_breaker.protect():
                result = await some_operation()
        """
        async with self._lock:
            self.stats.total_requests += 1
            
            # Check if circuit should transition states
            await self._check_state_transition()
            
            # Reject if circuit is open
            if self.stats.state == CircuitState.OPEN:
                raise CircuitBreakerError(f"Circuit breaker '{self.name}' is open")
        
        try:
            yield
            await self._record_success()
        except self.config.expected_exceptions:
            await self._record_failure()
            raise
    
    async def _check_state_transition(self):
        """Check if circuit breaker should change state."""
        now = datetime.utcnow()
        
        if self.stats.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if (self.stats.last_failure_time and 
                (now - self.stats.last_failure_time).total_seconds() >= self.config.recovery_timeout):
                
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.success_count = 0
                
                logger.info(
                    f"Circuit breaker '{self.name}' transitioning to half-open",
                    extra={
                        "circuit_breaker": {
                            "name": self.name,
                            "previous_state": "open",
                            "new_state": "half_open",
                            "recovery_timeout": self.config.recovery_timeout
                        }
                    }
                )
        
        elif self.stats.state == CircuitState.HALF_OPEN:
            # Check if we should close (enough successes)
            if self.stats.success_count >= self.config.success_threshold:
                self.stats.state = CircuitState.CLOSED
                self.stats.failure_count = 0
                self.stats.success_count = 0
                
                logger.info(
                    f"Circuit breaker '{self.name}' closing after successful recovery",
                    extra={
                        "circuit_breaker": {
                            "name": self.name,
                            "previous_state": "half_open",
                            "new_state": "closed",
                            "success_threshold": self.config.success_threshold
                        }
                    }
                )
    
    async def _record_success(self):
        """Record a successful operation."""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.total_successes += 1
            self.stats.last_success_time = datetime.utcnow()
            
            # Reset failure count on success in closed state
            if self.stats.state == CircuitState.CLOSED:
                self.stats.failure_count = 0
    
    async def _record_failure(self):
        """Record a failed operation."""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = datetime.utcnow()
            
            # Check if we should open the circuit
            if (self.stats.state == CircuitState.CLOSED and 
                self.stats.failure_count >= self.config.failure_threshold):
                
                self.stats.state = CircuitState.OPEN
                
                logger.error(
                    f"Circuit breaker '{self.name}' opening due to failures",
                    extra={
                        "circuit_breaker": {
                            "name": self.name,
                            "previous_state": "closed",
                            "new_state": "open",
                            "failure_count": self.stats.failure_count,
                            "failure_threshold": self.config.failure_threshold
                        }
                    }
                )
            
            elif (self.stats.state == CircuitState.HALF_OPEN):
                # Any failure in half-open state reopens the circuit
                self.stats.state = CircuitState.OPEN
                self.stats.success_count = 0
                
                logger.warning(
                    f"Circuit breaker '{self.name}' reopening after half-open failure",
                    extra={
                        "circuit_breaker": {
                            "name": self.name,
                            "previous_state": "half_open",
                            "new_state": "open"
                        }
                    }
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "total_requests": self.stats.total_requests,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            "failure_rate": self.stats.total_failures / max(self.stats.total_requests, 1),
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    async def reset(self):
        """Reset circuit breaker to closed state."""
        async with self._lock:
            self.stats.state = CircuitState.CLOSED
            self.stats.failure_count = 0
            self.stats.success_count = 0
            
            logger.info(
                f"Circuit breaker '{self.name}' manually reset",
                extra={
                    "circuit_breaker": {
                        "name": self.name,
                        "state": "closed"
                    }
                }
            )


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def get_breaker(
        self, 
        name: str, 
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker.
        
        Args:
            name: Circuit breaker name
            config: Configuration (only used for new breakers)
            
        Returns:
            Circuit breaker instance
        """
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    async def reset_all(self):
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            await breaker.reset()


# Global registry instance
circuit_breaker_registry = CircuitBreakerRegistry()


async def get_circuit_breaker(
    name: str, 
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """
    Get a circuit breaker from the global registry.
    
    Args:
        name: Circuit breaker name
        config: Configuration for new breakers
        
    Returns:
        Circuit breaker instance
    """
    return await circuit_breaker_registry.get_breaker(name, config)