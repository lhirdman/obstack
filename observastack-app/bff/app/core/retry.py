"""Retry mechanism with exponential backoff and jitter."""

import asyncio
import random
import time
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar, Awaitable, Type, Union, Tuple
from dataclasses import dataclass
from functools import wraps

from .logging import get_logger, log_performance

logger = get_logger("retry")

T = TypeVar('T')


@dataclass
class RetryConfig:
    """Configuration for retry mechanism."""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0  # Exponential backoff base
    jitter: bool = True  # Add random jitter to delays
    backoff_factor: float = 1.0  # Additional backoff multiplier
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""
    
    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(f"Retry exhausted after {attempts} attempts. Last error: {last_exception}")


class RetryStats:
    """Statistics for retry operations."""
    
    def __init__(self):
        self.total_attempts = 0
        self.successful_attempts = 0
        self.failed_attempts = 0
        self.total_delay = 0.0
        self.last_attempt_time: Optional[datetime] = None


async def retry_async(
    func: Callable[..., Awaitable[T]],
    config: Optional[RetryConfig] = None,
    *args,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        config: Retry configuration
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        RetryExhaustedError: If all retry attempts fail
    """
    config = config or RetryConfig()
    stats = RetryStats()
    
    last_exception = None
    
    for attempt in range(1, config.max_attempts + 1):
        stats.total_attempts += 1
        stats.last_attempt_time = datetime.utcnow()
        
        try:
            logger.debug(
                f"Retry attempt {attempt}/{config.max_attempts}",
                extra={
                    "retry": {
                        "function": func.__name__,
                        "attempt": attempt,
                        "max_attempts": config.max_attempts
                    }
                }
            )
            
            start_time = time.time()
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            stats.successful_attempts += 1
            
            if attempt > 1:
                logger.info(
                    f"Retry succeeded on attempt {attempt}",
                    extra={
                        "retry": {
                            "function": func.__name__,
                            "attempt": attempt,
                            "duration_ms": duration_ms,
                            "total_delay": stats.total_delay
                        }
                    }
                )
            
            return result
            
        except config.retryable_exceptions as e:
            last_exception = e
            stats.failed_attempts += 1
            
            logger.warning(
                f"Retry attempt {attempt} failed: {e}",
                extra={
                    "retry": {
                        "function": func.__name__,
                        "attempt": attempt,
                        "max_attempts": config.max_attempts,
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                }
            )
            
            # Don't delay after the last attempt
            if attempt < config.max_attempts:
                delay = calculate_delay(attempt, config)
                stats.total_delay += delay
                
                logger.debug(
                    f"Waiting {delay:.2f}s before retry attempt {attempt + 1}",
                    extra={
                        "retry": {
                            "function": func.__name__,
                            "delay_seconds": delay,
                            "next_attempt": attempt + 1
                        }
                    }
                )
                
                await asyncio.sleep(delay)
        
        except Exception as e:
            # Non-retryable exception
            logger.error(
                f"Non-retryable exception in {func.__name__}: {e}",
                exc_info=True,
                extra={
                    "retry": {
                        "function": func.__name__,
                        "attempt": attempt,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "retryable": False
                    }
                }
            )
            raise
    
    # All attempts exhausted
    logger.error(
        f"All retry attempts exhausted for {func.__name__}",
        extra={
            "retry": {
                "function": func.__name__,
                "total_attempts": stats.total_attempts,
                "total_delay": stats.total_delay,
                "last_error": str(last_exception)
            }
        }
    )
    
    raise RetryExhaustedError(config.max_attempts, last_exception)


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay for retry attempt using exponential backoff with jitter.
    
    Args:
        attempt: Current attempt number (1-based)
        config: Retry configuration
        
    Returns:
        Delay in seconds
    """
    # Exponential backoff: base_delay * (exponential_base ^ (attempt - 1))
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    
    # Apply backoff factor
    delay *= config.backoff_factor
    
    # Cap at max delay
    delay = min(delay, config.max_delay)
    
    # Add jitter to prevent thundering herd
    if config.jitter:
        # Add random jitter up to 25% of the delay
        jitter_amount = delay * 0.25
        delay += random.uniform(-jitter_amount, jitter_amount)
        
        # Ensure delay is not negative
        delay = max(delay, 0.1)
    
    return delay


def retry_decorator(config: Optional[RetryConfig] = None):
    """
    Decorator for adding retry logic to async functions.
    
    Args:
        config: Retry configuration
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await retry_async(func, config, *args, **kwargs)
        return wrapper
    return decorator


class RetryableClient:
    """Base class for clients that need retry functionality."""
    
    def __init__(self, name: str, retry_config: Optional[RetryConfig] = None):
        """
        Initialize retryable client.
        
        Args:
            name: Client name for logging
            retry_config: Retry configuration
        """
        self.name = name
        self.retry_config = retry_config or RetryConfig()
        self.logger = get_logger(f"retry.{name}")
    
    async def execute_with_retry(
        self,
        operation: str,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Operation name for logging
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        self.logger.debug(f"Executing {operation} with retry")
        
        try:
            result = await retry_async(func, self.retry_config, *args, **kwargs)
            
            self.logger.debug(f"Successfully executed {operation}")
            return result
            
        except RetryExhaustedError as e:
            self.logger.error(
                f"Failed to execute {operation} after {e.attempts} attempts",
                extra={
                    "operation": operation,
                    "client": self.name,
                    "attempts": e.attempts,
                    "last_error": str(e.last_exception)
                }
            )
            raise


# Predefined retry configurations for common scenarios
class RetryConfigs:
    """Predefined retry configurations for common scenarios."""
    
    # Quick operations (API calls, database queries)
    QUICK = RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=True
    )
    
    # Standard operations (file operations, network requests)
    STANDARD = RetryConfig(
        max_attempts=5,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True
    )
    
    # Long operations (data processing, external service calls)
    LONG = RetryConfig(
        max_attempts=7,
        base_delay=2.0,
        max_delay=120.0,
        exponential_base=1.5,
        jitter=True
    )
    
    # Critical operations (must succeed eventually)
    CRITICAL = RetryConfig(
        max_attempts=10,
        base_delay=1.0,
        max_delay=300.0,
        exponential_base=1.2,
        jitter=True
    )
    
    # Network operations (prone to transient failures)
    NETWORK = RetryConfig(
        max_attempts=5,
        base_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=True,
        retryable_exceptions=(
            ConnectionError,
            TimeoutError,
            OSError,
            Exception  # Catch-all for network issues
        )
    )


# Convenience functions for common retry patterns
async def retry_network_call(func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
    """Retry a network call with network-specific configuration."""
    return await retry_async(func, RetryConfigs.NETWORK, *args, **kwargs)


async def retry_critical_operation(func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
    """Retry a critical operation that must eventually succeed."""
    return await retry_async(func, RetryConfigs.CRITICAL, *args, **kwargs)


async def retry_quick_operation(func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
    """Retry a quick operation with minimal delays."""
    return await retry_async(func, RetryConfigs.QUICK, *args, **kwargs)