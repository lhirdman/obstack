# Debugging

This guide provides comprehensive debugging techniques and tools for troubleshooting ObservaStack issues in development and production environments.

## Debugging Philosophy

Effective debugging follows a systematic approach:

1. **Reproduce the issue** consistently
2. **Isolate the problem** to specific components
3. **Gather relevant information** (logs, metrics, traces)
4. **Form hypotheses** about root causes
5. **Test solutions** incrementally
6. **Document findings** for future reference

## Logging and Log Analysis

### Application Logging

#### Backend Logging Configuration

```python
# app/core/logging.py
import logging
import sys
from typing import Dict, Any
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'tenant_id'):
            log_data['tenant_id'] = record.tenant_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        # Add exception info
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def setup_logging(level: str = "INFO", structured: bool = True):
    """Configure application logging."""
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

#### Frontend Logging

```typescript
// src/utils/logger.ts
interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  context?: Record<string, any>;
  error?: Error;
}

class Logger {
  private context: Record<string, any> = {};
  
  setContext(context: Record<string, any>) {
    this.context = { ...this.context, ...context };
  }
  
  private log(level: LogEntry['level'], message: string, context?: Record<string, any>, error?: Error) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: { ...this.context, ...context },
      error
    };
    
    // Console output
    console[level](message, entry);
    
    // Send to backend in production
    if (process.env.NODE_ENV === 'production') {
      this.sendToBackend(entry);
    }
  }
  
  private async sendToBackend(entry: LogEntry) {
    try {
      await fetch('/api/v1/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry)
      });
    } catch (error) {
      console.error('Failed to send log to backend:', error);
    }
  }
  
  debug(message: string, context?: Record<string, any>) {
    this.log('debug', message, context);
  }
  
  info(message: string, context?: Record<string, any>) {
    this.log('info', message, context);
  }
  
  warn(message: string, context?: Record<string, any>) {
    this.log('warn', message, context);
  }
  
  error(message: string, context?: Record<string, any>, error?: Error) {
    this.log('error', message, context, error);
  }
}

export const logger = new Logger();

// Set up global error handling
window.addEventListener('error', (event) => {
  logger.error('Unhandled error', {
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno
  }, event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  logger.error('Unhandled promise rejection', {
    reason: event.reason
  });
});
```

### Log Analysis Techniques

#### Structured Log Queries

```bash
# Search for errors in the last hour
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={level="error"}' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)000000000" \
  --data-urlencode "end=$(date +%s)000000000"

# Search for specific user activity
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={user_id="user-123"}' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)000000000" \
  --data-urlencode "end=$(date +%s)000000000"

# Search for database connection errors
curl -G "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={} |~ "database.*connection.*error"' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)000000000" \
  --data-urlencode "end=$(date +%s)000000000"
```

#### Log Correlation

```python
# app/utils/correlation.py
import uuid
from contextvars import ContextVar
from fastapi import Request

# Context variable for request correlation
correlation_id: ContextVar[str] = ContextVar('correlation_id')

class CorrelationMiddleware:
    async def __call__(self, request: Request, call_next):
        # Generate or extract correlation ID
        corr_id = request.headers.get('X-Correlation-ID', str(uuid.uuid4()))
        correlation_id.set(corr_id)
        
        # Add to request state
        request.state.correlation_id = corr_id
        
        response = await call_next(request)
        
        # Add to response headers
        response.headers['X-Correlation-ID'] = corr_id
        
        return response

# Usage in logging
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    class CorrelationAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            try:
                corr_id = correlation_id.get()
                return f"[{corr_id}] {msg}", kwargs
            except LookupError:
                return msg, kwargs
    
    return CorrelationAdapter(logger, {})
```

## Performance Debugging

### Application Performance Monitoring

#### Custom Metrics Collection

```python
# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'tenant_id']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint', 'tenant_id']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections',
    ['service']
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type', 'table']
)

class MetricsMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment active connections
        ACTIVE_CONNECTIONS.labels(service='backend').inc()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            tenant_id = getattr(request.state, 'tenant_id', 'unknown')
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                tenant_id=tenant_id
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path,
                tenant_id=tenant_id
            ).observe(duration)
            
            return response
            
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.labels(service='backend').dec()
```

#### Database Query Analysis

```python
# app/db/profiling.py
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    
    # Log slow queries
    if total > 1.0:  # Queries taking more than 1 second
        logger.warning(
            "Slow query detected",
            extra={
                "duration": total,
                "statement": statement[:200],  # Truncate long statements
                "parameters": str(parameters)[:100] if parameters else None
            }
        )
    
    # Record metric
    DATABASE_QUERY_DURATION.labels(
        query_type=statement.split()[0].upper(),
        table=extract_table_name(statement)
    ).observe(total)

def extract_table_name(statement: str) -> str:
    """Extract table name from SQL statement."""
    try:
        # Simple extraction for common cases
        statement = statement.upper()
        if 'FROM' in statement:
            parts = statement.split('FROM')[1].split()
            return parts[0] if parts else 'unknown'
        elif 'UPDATE' in statement:
            parts = statement.split('UPDATE')[1].split()
            return parts[0] if parts else 'unknown'
        elif 'INSERT INTO' in statement:
            parts = statement.split('INSERT INTO')[1].split()
            return parts[0] if parts else 'unknown'
        return 'unknown'
    except Exception:
        return 'unknown'
```

### Frontend Performance Debugging

#### Performance Monitoring

```typescript
// src/utils/performance.ts
interface PerformanceEntry {
  name: string;
  startTime: number;
  duration: number;
  type: 'navigation' | 'resource' | 'measure' | 'paint';
}

class PerformanceMonitor {
  private observer: PerformanceObserver | null = null;
  
  start() {
    if (!('PerformanceObserver' in window)) {
      console.warn('PerformanceObserver not supported');
      return;
    }
    
    this.observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.handlePerformanceEntry(entry);
      }
    });
    
    // Observe different types of performance entries
    this.observer.observe({ entryTypes: ['navigation', 'resource', 'measure', 'paint'] });
  }
  
  private handlePerformanceEntry(entry: PerformanceEntry) {
    // Log slow operations
    if (entry.duration > 1000) {
      logger.warn('Slow operation detected', {
        name: entry.name,
        duration: entry.duration,
        type: entry.type
      });
    }
    
    // Send metrics to backend
    this.sendMetric({
      name: entry.name,
      duration: entry.duration,
      type: entry.type,
      timestamp: Date.now()
    });
  }
  
  measureFunction<T>(name: string, fn: () => T): T {
    const startMark = `${name}-start`;
    const endMark = `${name}-end`;
    
    performance.mark(startMark);
    
    try {
      const result = fn();
      
      if (result instanceof Promise) {
        return result.finally(() => {
          performance.mark(endMark);
          performance.measure(name, startMark, endMark);
        }) as T;
      } else {
        performance.mark(endMark);
        performance.measure(name, startMark, endMark);
        return result;
      }
    } catch (error) {
      performance.mark(endMark);
      performance.measure(name, startMark, endMark);
      throw error;
    }
  }
  
  private async sendMetric(metric: any) {
    try {
      await fetch('/api/v1/metrics/frontend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(metric)
      });
    } catch (error) {
      console.error('Failed to send performance metric:', error);
    }
  }
}

export const performanceMonitor = new PerformanceMonitor();

// Usage example
export const measureApiCall = <T>(name: string, apiCall: () => Promise<T>): Promise<T> => {
  return performanceMonitor.measureFunction(name, apiCall);
};
```

## Distributed Tracing

### OpenTelemetry Integration

#### Backend Tracing

```python
# app/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

def setup_tracing(app, service_name: str = "observastack-backend"):
    """Set up distributed tracing."""
    
    # Set up tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Configure OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint="http://tempo:4317",
        insecure=True
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument database
    SQLAlchemyInstrumentor().instrument()
    
    # Instrument Redis
    RedisInstrumentor().instrument()
    
    return tracer

# Custom tracing decorator
def trace_function(operation_name: str = None):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function parameters as attributes
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.set_attribute("function.result", "error")
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Usage example
@trace_function("search.logs")
async def search_logs(query: SearchQuery, tenant_id: str) -> List[LogEntry]:
    tracer = trace.get_tracer(__name__)
    
    with tracer.start_as_current_span("validate_query") as span:
        span.set_attribute("query.text", query.free_text)
        span.set_attribute("query.type", query.type)
        span.set_attribute("tenant.id", tenant_id)
        
        if not query.free_text.strip():
            span.set_attribute("validation.result", "failed")
            raise ValueError("Query cannot be empty")
        
        span.set_attribute("validation.result", "passed")
    
    with tracer.start_as_current_span("loki_query") as span:
        span.set_attribute("datasource", "loki")
        results = await loki_client.query(query, tenant_id)
        span.set_attribute("results.count", len(results))
    
    return results
```

#### Frontend Tracing

```typescript
// src/utils/tracing.ts
import { trace, context, SpanStatusCode } from '@opentelemetry/api';
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-otlp-http';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';

// Set up tracing
const provider = new WebTracerProvider();

const exporter = new OTLPTraceExporter({
  url: '/api/v1/traces',
});

provider.addSpanProcessor(new BatchSpanProcessor(exporter));

// Register instrumentations
registerInstrumentations({
  instrumentations: [
    new FetchInstrumentation({
      propagateTraceHeaderCorsUrls: [
        /^https?:\/\/localhost/,
        /^https?:\/\/.*\.observastack\.com/,
      ],
    }),
  ],
});

trace.setGlobalTracerProvider(provider);

const tracer = trace.getTracer('observastack-frontend');

// Tracing utilities
export const traceFunction = <T>(
  name: string,
  fn: () => T | Promise<T>,
  attributes?: Record<string, string | number | boolean>
): T | Promise<T> => {
  const span = tracer.startSpan(name);
  
  if (attributes) {
    Object.entries(attributes).forEach(([key, value]) => {
      span.setAttributes({ [key]: value });
    });
  }
  
  const result = context.with(trace.setSpan(context.active(), span), fn);
  
  if (result instanceof Promise) {
    return result
      .then((value) => {
        span.setStatus({ code: SpanStatusCode.OK });
        span.end();
        return value;
      })
      .catch((error) => {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });
        span.end();
        throw error;
      });
  } else {
    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
    return result;
  }
};

// Usage in React components
export const useTracing = (componentName: string) => {
  const traceRender = useCallback(() => {
    return traceFunction(`${componentName}.render`, () => {
      // Component render logic
    });
  }, [componentName]);
  
  const traceEffect = useCallback((effectName: string, effect: () => void) => {
    return traceFunction(`${componentName}.${effectName}`, effect);
  }, [componentName]);
  
  return { traceRender, traceEffect };
};
```

## Error Tracking and Analysis

### Error Handling Patterns

#### Backend Error Handling

```python
# app/exceptions.py
from typing import Optional, Dict, Any
import traceback
import logging

logger = logging.getLogger(__name__)

class ObservaStackException(Exception):
    """Base exception for ObservaStack."""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
        cause: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        
        # Log the exception
        logger.error(
            f"Exception occurred: {self.error_code}",
            extra={
                "error_code": self.error_code,
                "message": message,
                "details": self.details,
                "cause": str(cause) if cause else None,
                "traceback": traceback.format_exc()
            }
        )

class ValidationError(ObservaStackException):
    """Validation error."""
    pass

class AuthenticationError(ObservaStackException):
    """Authentication error."""
    pass

class AuthorizationError(ObservaStackException):
    """Authorization error."""
    pass

class ExternalServiceError(ObservaStackException):
    """External service error."""
    pass

class DataSourceError(ExternalServiceError):
    """Data source connection error."""
    pass

# Global exception handler
@app.exception_handler(ObservaStackException)
async def observastack_exception_handler(request: Request, exc: ObservaStackException):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, "correlation_id", None)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        extra={
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
            "request_path": request.url.path,
            "request_method": request.method
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, "correlation_id", None)
            }
        }
    )
```

#### Frontend Error Boundaries

```typescript
// src/components/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { logger } from '../utils/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({ errorInfo });
    
    // Log error
    logger.error('React Error Boundary caught an error', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    }, error);
    
    // Call custom error handler
    this.props.onError?.(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            <summary>Error Details</summary>
            {this.state.error && this.state.error.toString()}
            <br />
            {this.state.errorInfo?.componentStack}
          </details>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Usage
export function App() {
  return (
    <ErrorBoundary
      onError={(error, errorInfo) => {
        // Send error to monitoring service
        sendErrorToMonitoring(error, errorInfo);
      }}
    >
      <Router>
        <Routes>
          {/* Your routes */}
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}
```

## Debugging Tools and Techniques

### Development Tools

#### Debug Endpoints

```python
# app/api/debug.py (only in development)
from fastapi import APIRouter, Depends
from app.core.config import settings

if settings.DEBUG:
    router = APIRouter(prefix="/debug", tags=["debug"])
    
    @router.get("/info")
    async def debug_info():
        """Get debug information about the application."""
        return {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "version": settings.VERSION,
            "database_url": settings.DATABASE_URL.replace(
                settings.DATABASE_URL.split('@')[0].split('://')[-1], 
                "***"
            ),
            "redis_url": settings.REDIS_URL.replace(
                settings.REDIS_URL.split('@')[0].split('://')[-1], 
                "***"
            ) if settings.REDIS_URL else None
        }
    
    @router.get("/health/detailed")
    async def detailed_health():
        """Detailed health check with component status."""
        health_checks = {}
        
        # Database health
        try:
            await database.execute("SELECT 1")
            health_checks["database"] = {"status": "healthy", "latency": "< 1ms"}
        except Exception as e:
            health_checks["database"] = {"status": "unhealthy", "error": str(e)}
        
        # Redis health
        try:
            await redis.ping()
            health_checks["redis"] = {"status": "healthy"}
        except Exception as e:
            health_checks["redis"] = {"status": "unhealthy", "error": str(e)}
        
        # External services health
        for service_name, client in [
            ("prometheus", prometheus_client),
            ("loki", loki_client),
            ("tempo", tempo_client)
        ]:
            try:
                healthy = await client.health_check()
                health_checks[service_name] = {
                    "status": "healthy" if healthy else "unhealthy"
                }
            except Exception as e:
                health_checks[service_name] = {"status": "unhealthy", "error": str(e)}
        
        return {
            "overall_status": "healthy" if all(
                check["status"] == "healthy" for check in health_checks.values()
            ) else "unhealthy",
            "checks": health_checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @router.post("/simulate-error")
    async def simulate_error(error_type: str = "generic"):
        """Simulate different types of errors for testing."""
        if error_type == "validation":
            raise ValidationError("Simulated validation error")
        elif error_type == "auth":
            raise AuthenticationError("Simulated auth error")
        elif error_type == "external":
            raise ExternalServiceError("Simulated external service error")
        else:
            raise Exception("Simulated generic error")
```

#### Interactive Debugging

```python
# app/utils/debug.py
import pdb
import sys
from typing import Any

def debug_here():
    """Drop into debugger at this point."""
    if sys.gettrace() is None:  # Not already debugging
        pdb.set_trace()

def debug_on_exception(func):
    """Decorator to drop into debugger on exception."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            if settings.DEBUG:
                import traceback
                traceback.print_exc()
                pdb.post_mortem()
            raise
    return wrapper

# Usage
@debug_on_exception
async def problematic_function():
    # Your code here
    debug_here()  # Manual breakpoint
    pass
```

### Production Debugging

#### Remote Debugging Setup

```python
# app/utils/remote_debug.py
import logging
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

class RemoteDebugger:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.debug_sessions = {}
    
    def start_session(self, session_id: str, context: Dict[str, Any]):
        """Start a remote debugging session."""
        if not self.enabled:
            return
        
        self.debug_sessions[session_id] = {
            "start_time": datetime.utcnow(),
            "context": context,
            "events": []
        }
        
        logger.info(f"Started debug session: {session_id}")
    
    def log_event(self, session_id: str, event: str, data: Any = None):
        """Log an event in the debug session."""
        if not self.enabled or session_id not in self.debug_sessions:
            return
        
        self.debug_sessions[session_id]["events"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "data": data
        })
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """End debug session and return collected data."""
        if not self.enabled or session_id not in self.debug_sessions:
            return {}
        
        session_data = self.debug_sessions.pop(session_id)
        session_data["end_time"] = datetime.utcnow()
        
        logger.info(f"Ended debug session: {session_id}")
        return session_data

# Global debugger instance
remote_debugger = RemoteDebugger(enabled=settings.DEBUG)

# Usage in request handlers
@router.post("/search")
async def search(request: Request, query: SearchQuery):
    session_id = request.headers.get("X-Debug-Session")
    
    if session_id:
        remote_debugger.start_session(session_id, {
            "endpoint": "/search",
            "query": query.dict(),
            "user_id": request.state.user_id
        })
        
        remote_debugger.log_event(session_id, "query_validation_start")
        # ... validation logic ...
        remote_debugger.log_event(session_id, "query_validation_end", {"valid": True})
        
        remote_debugger.log_event(session_id, "search_start")
        results = await search_service.search(query)
        remote_debugger.log_event(session_id, "search_end", {"count": len(results)})
        
        debug_data = remote_debugger.end_session(session_id)
        # Optionally include debug data in response headers
        
    return results
```

### Memory and Resource Debugging

#### Memory Profiling

```python
# app/utils/profiling.py
import psutil
import tracemalloc
from typing import Dict, Any
import gc

class MemoryProfiler:
    def __init__(self):
        self.snapshots = {}
    
    def start_tracing(self, key: str = "default"):
        """Start memory tracing."""
        tracemalloc.start()
        self.snapshots[key] = {
            "start": tracemalloc.take_snapshot(),
            "start_time": time.time()
        }
    
    def take_snapshot(self, key: str = "default") -> Dict[str, Any]:
        """Take a memory snapshot and compare with start."""
        if key not in self.snapshots:
            return {}
        
        current = tracemalloc.take_snapshot()
        start_snapshot = self.snapshots[key]["start"]
        
        # Compare snapshots
        top_stats = current.compare_to(start_snapshot, 'lineno')
        
        # Get current memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "memory_usage": {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "percent": process.memory_percent()
            },
            "top_differences": [
                {
                    "filename": stat.traceback.format()[0],
                    "size_diff": stat.size_diff,
                    "count_diff": stat.count_diff
                }
                for stat in top_stats[:10]
            ],
            "gc_stats": {
                "collections": gc.get_stats(),
                "objects": len(gc.get_objects())
            }
        }
    
    def stop_tracing(self, key: str = "default"):
        """Stop memory tracing."""
        if key in self.snapshots:
            del self.snapshots[key]
        tracemalloc.stop()

# Usage
memory_profiler = MemoryProfiler()

@router.post("/search")
async def search(query: SearchQuery):
    if settings.DEBUG:
        memory_profiler.start_tracing("search")
    
    try:
        results = await search_service.search(query)
        
        if settings.DEBUG:
            memory_stats = memory_profiler.take_snapshot("search")
            logger.debug("Memory usage after search", extra=memory_stats)
        
        return results
    finally:
        if settings.DEBUG:
            memory_profiler.stop_tracing("search")
```

## Debugging Checklist

### When Issues Occur

1. **Gather Information**
   - [ ] Reproduce the issue consistently
   - [ ] Check recent deployments or changes
   - [ ] Review error logs and metrics
   - [ ] Identify affected users/tenants

2. **Initial Investigation**
   - [ ] Check service health endpoints
   - [ ] Review system resource usage
   - [ ] Examine database performance
   - [ ] Check external service connectivity

3. **Deep Dive Analysis**
   - [ ] Analyze distributed traces
   - [ ] Review application logs with correlation IDs
   - [ ] Check for memory leaks or resource exhaustion
   - [ ] Examine database query performance

4. **Resolution and Prevention**
   - [ ] Implement fix and test thoroughly
   - [ ] Update monitoring and alerting
   - [ ] Document the issue and resolution
   - [ ] Conduct post-mortem if necessary

### Common Debugging Scenarios

#### Performance Issues
- Check CPU and memory usage
- Analyze slow database queries
- Review cache hit rates
- Examine network latency

#### Authentication Problems
- Verify JWT token validity
- Check Keycloak connectivity
- Review user permissions
- Validate tenant isolation

#### Data Source Issues
- Test connectivity to Prometheus/Loki/Tempo
- Check query syntax and parameters
- Verify data source health
- Review rate limiting and quotas

#### Frontend Issues
- Check browser console for errors
- Review network requests in dev tools
- Analyze bundle size and loading times
- Test across different browsers

## Next Steps

- [Review common issues](common-issues.md) for known problems and solutions
- [Set up monitoring](../user-guide/alerts.md) for proactive issue detection
- [Configure performance monitoring](performance.md) for ongoing optimization