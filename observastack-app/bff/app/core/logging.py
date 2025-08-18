"""Structured logging configuration for ObservaStack BFF."""

import json
import logging
import logging.config
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

from .config import get_settings

# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id
        
        # Add tenant context if available
        tenant_id = tenant_id_var.get()
        if tenant_id:
            log_entry["tenant_id"] = tenant_id
        
        # Add user context if available
        user_id = user_id_var.get()
        if user_id:
            log_entry["user_id"] = user_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'message'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    """Plain text formatter for development."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as plain text with context."""
        # Get context information
        correlation_id = correlation_id_var.get()
        tenant_id = tenant_id_var.get()
        user_id = user_id_var.get()
        
        # Build context string
        context_parts = []
        if correlation_id:
            context_parts.append(f"corr_id={correlation_id[:8]}")
        if tenant_id:
            context_parts.append(f"tenant={tenant_id}")
        if user_id:
            context_parts.append(f"user={user_id}")
        
        context_str = f"[{', '.join(context_parts)}] " if context_parts else ""
        
        # Format the message
        formatted = super().format(record)
        return f"{context_str}{formatted}"


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    
    # Determine log format
    use_json = settings.log_format.lower() == "json"
    formatter_class = StructuredFormatter if use_json else PlainFormatter
    
    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": formatter_class,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "structured",
                "stream": sys.stdout
            }
        },
        "loggers": {
            "observastack": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"]
        }
    }
    
    logging.config.dictConfig(logging_config)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the observastack prefix."""
    return logging.getLogger(f"observastack.{name}")


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for request tracking."""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    correlation_id_var.set(correlation_id)
    return correlation_id


def set_tenant_context(tenant_id: str) -> None:
    """Set tenant context for logging."""
    tenant_id_var.set(tenant_id)


def set_user_context(user_id: str) -> None:
    """Set user context for logging."""
    user_id_var.set(user_id)


def clear_context() -> None:
    """Clear all logging context variables."""
    correlation_id_var.set(None)
    tenant_id_var.set(None)
    user_id_var.set(None)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    **kwargs: Any
) -> None:
    """Log performance metrics in a structured way."""
    logger.info(
        f"Performance: {operation}",
        extra={
            "performance": {
                "operation": operation,
                "duration_ms": duration_ms,
                "status": "completed"
            },
            **kwargs
        }
    )


def log_security_event(
    logger: logging.Logger,
    event_type: str,
    details: Dict[str, Any],
    severity: str = "info"
) -> None:
    """Log security-related events."""
    log_level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(
        log_level,
        f"Security event: {event_type}",
        extra={
            "security": {
                "event_type": event_type,
                "severity": severity,
                **details
            }
        }
    )


def log_business_event(
    logger: logging.Logger,
    event_type: str,
    entity_type: str,
    entity_id: str,
    action: str,
    **kwargs: Any
) -> None:
    """Log business events for audit trails."""
    logger.info(
        f"Business event: {event_type}",
        extra={
            "business": {
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                **kwargs
            }
        }
    )