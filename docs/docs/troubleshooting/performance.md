# Performance Optimization

This guide covers performance optimization techniques for ObservaStack, including monitoring, analysis, and tuning strategies for both development and production environments.

## Performance Monitoring

### Key Performance Indicators (KPIs)

#### Application Performance
- **Response Time**: API endpoint response times (p50, p95, p99)
- **Throughput**: Requests per second (RPS)
- **Error Rate**: Percentage of failed requests
- **Availability**: Service uptime percentage

#### System Performance
- **CPU Utilization**: Average and peak CPU usage
- **Memory Usage**: RAM consumption and garbage collection
- **Disk I/O**: Read/write operations and latency
- **Network**: Bandwidth utilization and packet loss

#### Data Source Performance
- **Query Latency**: Time to execute queries against data sources
- **Data Ingestion Rate**: Events/logs processed per second
- **Storage Utilization**: Disk space usage and growth rate
- **Index Performance**: Search and aggregation performance

### Performance Metrics Collection

#### Backend Metrics

```python
# app/middleware/performance.py
from prometheus_client import Counter, Histogram, Gauge, Summary
import time
import psutil
import gc

# Application metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

# System metrics
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')
GC_COLLECTIONS = Counter('gc_collections_total', 'Total garbage collections', ['generation'])

# Database metrics
DB_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

DB_CONNECTION_POOL = Gauge(
    'database_connections_active',
    'Active database connections'
)

class PerformanceMiddleware:
    def __init__(self):
        self.process = psutil.Process()
    
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment active requests
        ACTIVE_REQUESTS.inc()
        
        # Collect system metrics
        self.collect_system_metrics()
        
        try:
            response = await call_next(request)
            
            # Record request metrics
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            return response
            
        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.dec()
    
    def collect_system_metrics(self):
        """Collect system performance metrics."""
        # CPU usage
        cpu_percent = self.process.cpu_percent()
        CPU_USAGE.set(cpu_percent)
        
        # Memory usage
        memory_info = self.process.memory_info()
        MEMORY_USAGE.set(memory_info.rss)
        
        # Garbage collection stats
        for i, stat in enumerate(gc.get_stats()):
            GC_COLLECTIONS.labels(generation=str(i))._value._value = stat['collections']
```

#### Frontend Performance Monitoring

```typescript
// src/utils/performanceMonitor.ts
interface PerformanceMetrics {
  pageLoadTime: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
  timeToInteractive: number;
}

class PerformanceMonitor {
  private metrics: Partial<PerformanceMetrics> = {};
  
  constructor() {
    this.setupObservers();
  }
  
  private setupObservers() {
    // Core Web Vitals observer
    if ('PerformanceObserver' in window) {
      // Largest Contentful Paint
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.metrics.largestContentfulPaint = lastEntry.startTime;
        this.reportMetric('lcp', lastEntry.startTime);
      }).observe({ entryTypes: ['largest-contentful-paint'] });
      
      // First Input Delay
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          this.metrics.firstInputDelay = entry.processingStart - entry.startTime;
          this.reportMetric('fid', entry.processingStart - entry.startTime);
        });
      }).observe({ entryTypes: ['first-input'] });
      
      // Cumulative Layout Shift
      let clsValue = 0;
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        });
        this.metrics.cumulativeLayoutShift = clsValue;
        this.reportMetric('cls', clsValue);
      }).observe({ entryTypes: ['layout-shift'] });
    }
    
    // Navigation timing
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
        
        this.metrics.pageLoadTime = navigation.loadEventEnd - navigation.fetchStart;
        this.metrics.firstContentfulPaint = this.getFirstContentfulPaint();
        this.metrics.timeToInteractive = this.calculateTTI();
        
        this.reportAllMetrics();
      }, 0);
    });
  }
  
  private getFirstContentfulPaint(): number {
    const paintEntries = performance.getEntriesByType('paint');
    const fcpEntry = paintEntries.find(entry => entry.name === 'first-contentful-paint');
    return fcpEntry ? fcpEntry.startTime : 0;
  }
  
  private calculateTTI(): number {
    // Simplified TTI calculation
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
    return navigation.domInteractive - navigation.fetchStart;
  }
  
  private reportMetric(name: string, value: number) {
    // Send to analytics
    if (typeof gtag !== 'undefined') {
      gtag('event', 'web_vitals', {
        name,
        value: Math.round(value),
        event_category: 'performance'
      });
    }
    
    // Send to backend
    this.sendToBackend(name, value);
  }
  
  private reportAllMetrics() {
    Object.entries(this.metrics).forEach(([name, value]) => {
      if (value !== undefined) {
        this.reportMetric(name, value);
      }
    });
  }
  
  private async sendToBackend(name: string, value: number) {
    try {
      await fetch('/api/v1/metrics/frontend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric: name,
          value,
          timestamp: Date.now(),
          url: window.location.pathname,
          userAgent: navigator.userAgent
        })
      });
    } catch (error) {
      console.error('Failed to send performance metric:', error);
    }
  }
  
  // Manual performance measurement
  measureFunction<T>(name: string, fn: () => T): T {
    const startTime = performance.now();
    
    try {
      const result = fn();
      
      if (result instanceof Promise) {
        return result.finally(() => {
          const duration = performance.now() - startTime;
          this.reportMetric(`function_${name}`, duration);
        }) as T;
      } else {
        const duration = performance.now() - startTime;
        this.reportMetric(`function_${name}`, duration);
        return result;
      }
    } catch (error) {
      const duration = performance.now() - startTime;
      this.reportMetric(`function_${name}_error`, duration);
      throw error;
    }
  }
}

export const performanceMonitor = new PerformanceMonitor();
```

## Performance Analysis

### Identifying Bottlenecks

#### Database Performance Analysis

```python
# app/utils/db_profiler.py
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

class DatabaseProfiler:
    def __init__(self):
        self.query_stats = defaultdict(list)
        self.slow_queries = []
        self.setup_listeners()
    
    def setup_listeners(self):
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._statement = statement
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - context._query_start_time
            
            # Categorize query
            query_type = statement.strip().split()[0].upper()
            table_name = self.extract_table_name(statement)
            
            # Record statistics
            self.query_stats[f"{query_type}_{table_name}"].append(total_time)
            
            # Track slow queries
            if total_time > 1.0:  # Queries taking more than 1 second
                self.slow_queries.append({
                    'statement': statement[:500],  # Truncate long statements
                    'duration': total_time,
                    'timestamp': time.time(),
                    'parameters': str(parameters)[:200] if parameters else None
                })
                
                logger.warning(
                    f"Slow query detected: {total_time:.3f}s",
                    extra={
                        'duration': total_time,
                        'query_type': query_type,
                        'table': table_name,
                        'statement': statement[:200]
                    }
                )
            
            # Record metric
            DB_QUERY_DURATION.labels(
                operation=query_type,
                table=table_name
            ).observe(total_time)
    
    def extract_table_name(self, statement: str) -> str:
        """Extract table name from SQL statement."""
        try:
            statement_upper = statement.upper()
            
            if 'FROM' in statement_upper:
                parts = statement_upper.split('FROM')[1].split()
                return parts[0].strip('`"[]') if parts else 'unknown'
            elif 'UPDATE' in statement_upper:
                parts = statement_upper.split('UPDATE')[1].split()
                return parts[0].strip('`"[]') if parts else 'unknown'
            elif 'INSERT INTO' in statement_upper:
                parts = statement_upper.split('INSERT INTO')[1].split()
                return parts[0].strip('`"[]') if parts else 'unknown'
            elif 'DELETE FROM' in statement_upper:
                parts = statement_upper.split('DELETE FROM')[1].split()
                return parts[0].strip('`"[]') if parts else 'unknown'
                
            return 'unknown'
        except Exception:
            return 'unknown'
    
    def get_performance_report(self) -> dict:
        """Generate performance report."""
        report = {
            'slow_queries': self.slow_queries[-10:],  # Last 10 slow queries
            'query_statistics': {}
        }
        
        # Calculate statistics for each query type
        for query_key, durations in self.query_stats.items():
            if durations:
                report['query_statistics'][query_key] = {
                    'count': len(durations),
                    'avg_duration': sum(durations) / len(durations),
                    'max_duration': max(durations),
                    'min_duration': min(durations),
                    'total_duration': sum(durations)
                }
        
        return report

# Global profiler instance
db_profiler = DatabaseProfiler()
```

#### API Performance Analysis

```python
# app/utils/api_profiler.py
from collections import defaultdict
import time
import statistics

class APIProfiler:
    def __init__(self):
        self.endpoint_stats = defaultdict(list)
        self.error_counts = defaultdict(int)
    
    def record_request(self, method: str, path: str, duration: float, status_code: int):
        """Record API request performance."""
        endpoint_key = f"{method} {path}"
        self.endpoint_stats[endpoint_key].append(duration)
        
        if status_code >= 400:
            self.error_counts[endpoint_key] += 1
    
    def get_performance_summary(self) -> dict:
        """Get performance summary for all endpoints."""
        summary = {}
        
        for endpoint, durations in self.endpoint_stats.items():
            if durations:
                summary[endpoint] = {
                    'request_count': len(durations),
                    'avg_response_time': statistics.mean(durations),
                    'p50_response_time': statistics.median(durations),
                    'p95_response_time': statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
                    'p99_response_time': statistics.quantiles(durations, n=100)[98] if len(durations) > 100 else max(durations),
                    'max_response_time': max(durations),
                    'min_response_time': min(durations),
                    'error_count': self.error_counts.get(endpoint, 0),
                    'error_rate': self.error_counts.get(endpoint, 0) / len(durations)
                }
        
        return summary
    
    def get_slowest_endpoints(self, limit: int = 10) -> list:
        """Get the slowest endpoints by average response time."""
        summary = self.get_performance_summary()
        
        sorted_endpoints = sorted(
            summary.items(),
            key=lambda x: x[1]['avg_response_time'],
            reverse=True
        )
        
        return sorted_endpoints[:limit]

# Global API profiler
api_profiler = APIProfiler()

# Middleware integration
class ProfilingMiddleware:
    async def __call__(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        api_profiler.record_request(
            request.method,
            request.url.path,
            duration,
            response.status_code
        )
        
        return response
```

### Memory Usage Analysis

```python
# app/utils/memory_profiler.py
import tracemalloc
import psutil
import gc
from typing import Dict, List, Any

class MemoryProfiler:
    def __init__(self):
        self.snapshots = {}
        self.process = psutil.Process()
    
    def start_profiling(self, key: str = "default"):
        """Start memory profiling."""
        tracemalloc.start()
        self.snapshots[key] = {
            'start_snapshot': tracemalloc.take_snapshot(),
            'start_time': time.time(),
            'start_memory': self.process.memory_info().rss
        }
    
    def analyze_memory_usage(self, key: str = "default") -> Dict[str, Any]:
        """Analyze current memory usage."""
        if key not in self.snapshots:
            return {}
        
        current_snapshot = tracemalloc.take_snapshot()
        start_data = self.snapshots[key]
        
        # Compare snapshots
        top_stats = current_snapshot.compare_to(start_data['start_snapshot'], 'lineno')
        
        # Current memory info
        current_memory = self.process.memory_info()
        memory_diff = current_memory.rss - start_data['start_memory']
        
        # Garbage collection stats
        gc_stats = gc.get_stats()
        
        return {
            'memory_usage': {
                'current_rss': current_memory.rss,
                'current_vms': current_memory.vms,
                'memory_diff': memory_diff,
                'memory_percent': self.process.memory_percent()
            },
            'top_memory_consumers': [
                {
                    'filename': stat.traceback.format()[0] if stat.traceback else 'unknown',
                    'size': stat.size,
                    'size_diff': stat.size_diff,
                    'count': stat.count,
                    'count_diff': stat.count_diff
                }
                for stat in top_stats[:10]
            ],
            'garbage_collection': {
                'total_objects': len(gc.get_objects()),
                'generation_stats': gc_stats
            },
            'duration': time.time() - start_data['start_time']
        }
    
    def detect_memory_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks."""
        leaks = []
        
        # Force garbage collection
        collected = gc.collect()
        
        # Check for objects that should have been collected
        for obj in gc.garbage:
            leaks.append({
                'type': type(obj).__name__,
                'repr': repr(obj)[:100],
                'referrers_count': len(gc.get_referrers(obj))
            })
        
        return leaks
    
    def stop_profiling(self, key: str = "default"):
        """Stop memory profiling and return analysis."""
        analysis = self.analyze_memory_usage(key)
        
        if key in self.snapshots:
            del self.snapshots[key]
        
        tracemalloc.stop()
        return analysis

# Usage in endpoints
memory_profiler = MemoryProfiler()

@router.post("/search")
async def search_with_profiling(query: SearchQuery):
    if settings.ENABLE_PROFILING:
        memory_profiler.start_profiling("search")
    
    try:
        results = await search_service.search(query)
        
        if settings.ENABLE_PROFILING:
            memory_analysis = memory_profiler.analyze_memory_usage("search")
            logger.info("Memory usage analysis", extra=memory_analysis)
        
        return results
    finally:
        if settings.ENABLE_PROFILING:
            memory_profiler.stop_profiling("search")
```

## Performance Optimization Strategies

### Backend Optimization

#### Database Optimization

```python
# app/db/optimization.py
from sqlalchemy import Index, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

class DatabaseOptimizer:
    def __init__(self, engine):
        self.engine = engine
    
    def optimize_connection_pool(self):
        """Optimize database connection pool settings."""
        # Connection pool configuration
        self.engine.pool = QueuePool(
            creator=self.engine.pool._creator,
            pool_size=20,  # Number of connections to maintain
            max_overflow=30,  # Additional connections allowed
            pool_timeout=30,  # Timeout for getting connection
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True  # Validate connections before use
        )
    
    def create_performance_indexes(self):
        """Create indexes for better query performance."""
        with self.engine.connect() as conn:
            # Index for user queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_tenant_email 
                ON users(tenant_id, email)
            """))
            
            # Index for search queries
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_search_logs_timestamp_tenant 
                ON search_logs(timestamp DESC, tenant_id)
            """))
            
            # Index for alerts
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_alerts_status_tenant_created 
                ON alerts(status, tenant_id, created_at DESC)
            """))
    
    def analyze_query_performance(self):
        """Analyze and optimize slow queries."""
        with self.engine.connect() as conn:
            # Get slow queries from PostgreSQL
            slow_queries = conn.execute(text("""
                SELECT query, mean_time, calls, total_time
                FROM pg_stat_statements
                WHERE mean_time > 1000  -- Queries taking more than 1 second
                ORDER BY mean_time DESC
                LIMIT 10
            """)).fetchall()
            
            return [
                {
                    'query': row.query[:200],
                    'mean_time': row.mean_time,
                    'calls': row.calls,
                    'total_time': row.total_time
                }
                for row in slow_queries
            ]

# Query optimization techniques
class OptimizedQueries:
    @staticmethod
    def get_user_alerts_optimized(session, user_id: str, limit: int = 50):
        """Optimized query for user alerts."""
        return session.execute(text("""
            SELECT a.id, a.name, a.severity, a.status, a.created_at
            FROM alerts a
            INNER JOIN users u ON a.tenant_id = u.tenant_id
            WHERE u.id = :user_id
            AND a.status IN ('active', 'acknowledged')
            ORDER BY a.created_at DESC
            LIMIT :limit
        """), {'user_id': user_id, 'limit': limit}).fetchall()
    
    @staticmethod
    def get_search_results_optimized(session, query: str, tenant_id: str, limit: int = 100):
        """Optimized search query with proper indexing."""
        return session.execute(text("""
            SELECT id, timestamp, message, level, service
            FROM logs
            WHERE tenant_id = :tenant_id
            AND to_tsvector('english', message) @@ plainto_tsquery('english', :query)
            ORDER BY timestamp DESC
            LIMIT :limit
        """), {
            'tenant_id': tenant_id,
            'query': query,
            'limit': limit
        }).fetchall()
```

#### Caching Strategies

```python
# app/cache/redis_cache.py
import redis
import json
import pickle
from typing import Any, Optional, Union
import hashlib

class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.default_ttl = 300  # 5 minutes
    
    def _make_key(self, key: str, tenant_id: str = None) -> str:
        """Create cache key with optional tenant isolation."""
        if tenant_id:
            return f"tenant:{tenant_id}:{key}"
        return key
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode()
        return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            return json.loads(value.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return pickle.loads(value)
    
    async def get(self, key: str, tenant_id: str = None) -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._make_key(key, tenant_id)
        value = await self.redis.get(cache_key)
        
        if value is None:
            return None
        
        return self._deserialize(value)
    
    async def set(self, key: str, value: Any, ttl: int = None, tenant_id: str = None):
        """Set value in cache."""
        cache_key = self._make_key(key, tenant_id)
        serialized_value = self._serialize(value)
        
        await self.redis.setex(
            cache_key,
            ttl or self.default_ttl,
            serialized_value
        )
    
    async def delete(self, key: str, tenant_id: str = None):
        """Delete value from cache."""
        cache_key = self._make_key(key, tenant_id)
        await self.redis.delete(cache_key)
    
    async def get_or_set(self, key: str, factory, ttl: int = None, tenant_id: str = None):
        """Get value from cache or set it using factory function."""
        value = await self.get(key, tenant_id)
        
        if value is None:
            value = await factory() if asyncio.iscoroutinefunction(factory) else factory()
            await self.set(key, value, ttl, tenant_id)
        
        return value

# Cache decorators
def cache_result(ttl: int = 300, key_prefix: str = None):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await redis_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await redis_cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar logic for sync functions
            pass
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Usage examples
@cache_result(ttl=600, key_prefix="user_profile")
async def get_user_profile(user_id: str) -> dict:
    # Expensive database query
    return await database.fetch_user_profile(user_id)

@cache_result(ttl=300, key_prefix="search_results")
async def search_logs(query: str, tenant_id: str) -> list:
    # Expensive search operation
    return await loki_client.search(query, tenant_id)
```

#### Async Optimization

```python
# app/utils/async_optimization.py
import asyncio
from typing import List, Any, Callable
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class AsyncOptimizer:
    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.semaphore = asyncio.Semaphore(100)  # Limit concurrent operations
    
    async def gather_with_concurrency(self, *coroutines, limit: int = 10):
        """Execute coroutines with concurrency limit."""
        semaphore = asyncio.Semaphore(limit)
        
        async def sem_coro(coro):
            async with semaphore:
                return await coro
        
        return await asyncio.gather(*[sem_coro(coro) for coro in coroutines])
    
    async def batch_process(self, items: List[Any], processor: Callable, batch_size: int = 100):
        """Process items in batches to avoid overwhelming resources."""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = [processor(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)
            
            # Small delay between batches to prevent resource exhaustion
            await asyncio.sleep(0.01)
        
        return results
    
    async def run_in_executor(self, func: Callable, *args):
        """Run CPU-intensive function in thread executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

# Usage in search service
class OptimizedSearchService:
    def __init__(self):
        self.optimizer = AsyncOptimizer()
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
        )
    
    async def search_all_sources(self, query: SearchQuery, tenant_id: str):
        """Search across all data sources concurrently."""
        
        # Create search tasks for different sources
        tasks = []
        
        if query.type in ['logs', 'all']:
            tasks.append(self.search_loki(query, tenant_id))
        
        if query.type in ['metrics', 'all']:
            tasks.append(self.search_prometheus(query, tenant_id))
        
        if query.type in ['traces', 'all']:
            tasks.append(self.search_tempo(query, tenant_id))
        
        # Execute searches concurrently with limit
        results = await self.optimizer.gather_with_concurrency(*tasks, limit=3)
        
        # Combine and process results
        combined_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Search error: {result}")
                continue
            combined_results.extend(result)
        
        return combined_results
    
    async def search_loki(self, query: SearchQuery, tenant_id: str):
        """Optimized Loki search with connection pooling."""
        async with self.semaphore:
            # Use connection pooling for better performance
            async with self.session.post(
                f"{settings.LOKI_URL}/loki/api/v1/query_range",
                json={
                    'query': f'{{tenant_id="{tenant_id}"}} |~ "{query.free_text}"',
                    'start': query.time_range.start,
                    'end': query.time_range.end,
                    'limit': query.limit or 1000
                }
            ) as response:
                data = await response.json()
                return self.parse_loki_response(data)
```

### Frontend Optimization

#### Bundle Optimization

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({
      filename: 'dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@headlessui/react', '@heroicons/react'],
          'chart-vendor': ['recharts', 'd3'],
          'utils-vendor': ['date-fns', 'lodash-es'],
          
          // Feature-based chunks
          'search': ['./src/views/Search', './src/components/search'],
          'alerts': ['./src/views/Alerts', './src/components/alerts'],
          'dashboards': ['./src/views/Dashboards', './src/components/dashboards'],
        },
      },
    },
    target: 'es2020',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom'],
  },
});
```

#### Component Optimization

```typescript
// src/components/optimized/VirtualizedList.tsx
import React, { memo, useMemo, useCallback } from 'react';
import { FixedSizeList as List } from 'react-window';

interface VirtualizedListProps {
  items: any[];
  itemHeight: number;
  height: number;
  renderItem: (item: any, index: number) => React.ReactNode;
}

export const VirtualizedList = memo<VirtualizedListProps>(({
  items,
  itemHeight,
  height,
  renderItem
}) => {
  const ItemRenderer = useCallback(({ index, style }) => (
    <div style={style}>
      {renderItem(items[index], index)}
    </div>
  ), [items, renderItem]);

  return (
    <List
      height={height}
      itemCount={items.length}
      itemSize={itemHeight}
      itemData={items}
    >
      {ItemRenderer}
    </List>
  );
});

// Optimized search results component
export const SearchResults = memo<SearchResultsProps>(({
  results,
  loading,
  onResultClick
}) => {
  // Memoize expensive calculations
  const processedResults = useMemo(() => {
    return results.map(result => ({
      ...result,
      formattedTimestamp: formatTimestamp(result.timestamp),
      highlightedMessage: highlightSearchTerms(result.message, searchTerm)
    }));
  }, [results, searchTerm]);

  // Memoize event handlers
  const handleResultClick = useCallback((result: SearchResult) => {
    onResultClick(result);
  }, [onResultClick]);

  const renderItem = useCallback((item: SearchResult, index: number) => (
    <SearchResultCard
      key={item.id}
      result={item}
      onClick={handleResultClick}
    />
  ), [handleResultClick]);

  if (loading) {
    return <SearchResultsSkeleton />;
  }

  return (
    <VirtualizedList
      items={processedResults}
      itemHeight={120}
      height={600}
      renderItem={renderItem}
    />
  );
});
```

#### State Management Optimization

```typescript
// src/hooks/useOptimizedSearch.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useCallback } from 'react';
import { debounce } from 'lodash-es';

export function useOptimizedSearch() {
  const queryClient = useQueryClient();
  
  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce(async (query: SearchQuery) => {
      return searchService.search(query);
    }, 300),
    []
  );
  
  // Query with caching and background updates
  const searchQuery = useQuery({
    queryKey: ['search', searchParams],
    queryFn: () => debouncedSearch(searchParams),
    staleTime: 30000, // 30 seconds
    cacheTime: 300000, // 5 minutes
    refetchOnWindowFocus: false,
    enabled: !!searchParams.freeText,
  });
  
  // Prefetch related queries
  const prefetchRelated = useCallback(async (result: SearchResult) => {
    // Prefetch log details
    queryClient.prefetchQuery({
      queryKey: ['log-details', result.id],
      queryFn: () => searchService.getLogDetails(result.id),
      staleTime: 60000,
    });
    
    // Prefetch related traces
    if (result.traceId) {
      queryClient.prefetchQuery({
        queryKey: ['trace', result.traceId],
        queryFn: () => searchService.getTrace(result.traceId),
        staleTime: 60000,
      });
    }
  }, [queryClient]);
  
  return {
    ...searchQuery,
    prefetchRelated,
    invalidateSearch: () => queryClient.invalidateQueries(['search']),
  };
}
```

## Performance Testing

### Load Testing

```python
# tests/performance/load_test.py
from locust import HttpUser, task, between
import random
import json

class ObservaStackUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def search_logs(self):
        """Test log search performance."""
        search_terms = ["error", "warning", "info", "debug", "exception"]
        query = {
            "freeText": random.choice(search_terms),
            "type": "logs",
            "timeRange": {
                "start": "2025-08-16T00:00:00Z",
                "end": "2025-08-16T23:59:59Z"
            },
            "limit": 100
        }
        
        with self.client.post(
            "/api/v1/search",
            headers=self.headers,
            json=query,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if len(data.get("items", [])) > 0:
                    response.success()
                else:
                    response.failure("No results returned")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def get_alerts(self):
        """Test alerts endpoint performance."""
        with self.client.get(
            "/api/v1/alerts",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def get_dashboards(self):
        """Test dashboards endpoint performance."""
        with self.client.get(
            "/api/v1/dashboards",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

# Run load test
# locust -f load_test.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

### Performance Benchmarking

```python
# tests/performance/benchmark.py
import asyncio
import time
import statistics
from typing import List, Callable, Any

class PerformanceBenchmark:
    def __init__(self):
        self.results = {}
    
    async def benchmark_function(
        self,
        name: str,
        func: Callable,
        iterations: int = 100,
        *args,
        **kwargs
    ) -> dict:
        """Benchmark a function's performance."""
        durations = []
        errors = 0
        
        for _ in range(iterations):
            start_time = time.time()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
                
                duration = time.time() - start_time
                durations.append(duration)
                
            except Exception as e:
                errors += 1
                logger.error(f"Benchmark error in {name}: {e}")
        
        if durations:
            results = {
                'name': name,
                'iterations': len(durations),
                'errors': errors,
                'avg_duration': statistics.mean(durations),
                'median_duration': statistics.median(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'std_deviation': statistics.stdev(durations) if len(durations) > 1 else 0,
                'p95_duration': statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations),
                'p99_duration': statistics.quantiles(durations, n=100)[98] if len(durations) > 100 else max(durations),
                'throughput': len(durations) / sum(durations) if sum(durations) > 0 else 0
            }
        else:
            results = {
                'name': name,
                'iterations': 0,
                'errors': errors,
                'error': 'All iterations failed'
            }
        
        self.results[name] = results
        return results
    
    def compare_benchmarks(self, baseline: str, comparison: str) -> dict:
        """Compare two benchmark results."""
        if baseline not in self.results or comparison not in self.results:
            return {}
        
        baseline_result = self.results[baseline]
        comparison_result = self.results[comparison]
        
        return {
            'baseline': baseline_result,
            'comparison': comparison_result,
            'performance_change': {
                'avg_duration_change': (
                    comparison_result['avg_duration'] - baseline_result['avg_duration']
                ) / baseline_result['avg_duration'] * 100,
                'throughput_change': (
                    comparison_result['throughput'] - baseline_result['throughput']
                ) / baseline_result['throughput'] * 100 if baseline_result['throughput'] > 0 else 0
            }
        }

# Usage example
async def run_benchmarks():
    benchmark = PerformanceBenchmark()
    
    # Benchmark search operations
    await benchmark.benchmark_function(
        "search_logs_cached",
        search_service.search_logs_cached,
        iterations=50,
        query="error",
        tenant_id="test-tenant"
    )
    
    await benchmark.benchmark_function(
        "search_logs_uncached",
        search_service.search_logs_uncached,
        iterations=50,
        query="error",
        tenant_id="test-tenant"
    )
    
    # Compare results
    comparison = benchmark.compare_benchmarks("search_logs_uncached", "search_logs_cached")
    print(json.dumps(comparison, indent=2))
```

## Performance Monitoring Dashboard

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "ObservaStack Performance Dashboard",
    "panels": [
      {
        "title": "API Response Times",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      },
      {
        "title": "Database Query Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m]))",
            "legendFormat": "{{operation}} {{table}}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "memory_usage_bytes / 1024 / 1024",
            "legendFormat": "Memory Usage (MB)"
          }
        ]
      },
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU Usage %"
          }
        ]
      }
    ]
  }
}
```

## Performance Optimization Checklist

### Backend Performance
- [ ] **Database queries optimized** with proper indexes
- [ ] **Connection pooling** configured appropriately
- [ ] **Caching implemented** for expensive operations
- [ ] **Async operations** used for I/O-bound tasks
- [ ] **Memory usage monitored** and optimized
- [ ] **Query performance analyzed** and slow queries identified

### Frontend Performance
- [ ] **Bundle size optimized** with code splitting
- [ ] **Components memoized** to prevent unnecessary re-renders
- [ ] **Virtual scrolling** implemented for large lists
- [ ] **Images optimized** and lazy loaded
- [ ] **API calls debounced** and cached
- [ ] **Core Web Vitals** monitored and optimized

### Infrastructure Performance
- [ ] **Load balancing** configured for high availability
- [ ] **CDN** set up for static assets
- [ ] **Compression** enabled for responses
- [ ] **HTTP/2** enabled for better performance
- [ ] **Resource limits** set appropriately
- [ ] **Monitoring** in place for all components

## Next Steps

- [Review debugging techniques](debugging.md) for performance issues
- [Set up monitoring](../user-guide/alerts.md) for performance metrics
- [Configure production setup](../deployment/production-setup.md) for optimal performance