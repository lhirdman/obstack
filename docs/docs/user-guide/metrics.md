---
sidebar_position: 2
---

# Metrics

The Metrics view in ObservaStack allows you to query and visualize time-series metrics from your observability stack using PromQL (Prometheus Query Language). This powerful interface provides real-time insights into your system's performance and health.

## Getting Started

### Accessing the Metrics View

1. **From the Dashboard**: Click the "Open Metrics" button on the main dashboard
2. **From the Navigation**: Use the "Metrics" link in the top navigation bar
3. **Direct URL**: Navigate to `/metrics` in your browser

### Basic Interface

The Metrics view consists of several key components:

- **Query Configuration Panel**: Where you build and execute your queries
- **Time Range Selector**: Controls the time window for your data
- **Results Visualization**: Charts and graphs displaying your metrics
- **Query Examples**: Pre-built queries for common use cases

## Query Types

ObservaStack supports two types of metric queries:

### Instant Queries

Instant queries return the current value of metrics at a specific point in time.

- **Use Case**: Current system status, real-time monitoring
- **Visualization**: Bar charts showing current values
- **Example**: `up` (shows which services are currently running)

### Range Queries

Range queries return time-series data over a specified time period.

- **Use Case**: Trend analysis, historical data, performance monitoring
- **Visualization**: Line charts showing data over time
- **Example**: `rate(http_requests_total[5m])` (request rate over time)

## Building Queries

### Using the Query Builder

1. **Select Query Type**: Choose between "Instant Query" or "Range Query"
2. **Enter PromQL**: Type your query in the text area
3. **Use Examples**: Click "Examples" to browse pre-built queries
4. **Insert Functions**: Click "Functions" to add PromQL functions
5. **Execute**: Click "Execute Query" or press Ctrl+Enter

### Query Examples by Category

#### System Health
- `up` - Service availability status
- `rate(cpu_usage_total[5m])` - CPU usage rate
- `memory_usage_bytes / memory_total_bytes * 100` - Memory utilization percentage
- `disk_usage_bytes / disk_total_bytes * 100` - Disk usage percentage

#### HTTP Metrics
- `rate(http_requests_total[5m])` - Request rate per second
- `rate(http_requests_total{status=~"5.."}[5m])` - Error rate
- `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` - 95th percentile response time
- `sum(http_requests_total) by (method, status)` - Request count by method and status

#### Application Metrics
- `active_connections` - Current active connections
- `queue_length` - Current queue size
- `avg(processing_time_seconds)` - Average processing time
- `sum(errors_total) by (type)` - Error count by type

### PromQL Functions

Common PromQL functions available in the function helper:

- **Aggregation**: `sum()`, `avg()`, `max()`, `min()`, `count()`
- **Rate Calculation**: `rate()`, `increase()`
- **Mathematical**: `abs()`, `ceil()`, `floor()`, `round()`, `sqrt()`
- **Statistical**: `histogram_quantile()`
- **Grouping**: `by()`, `without()`, `group_left()`, `group_right()`

## Time Range Configuration

### Quick Range Selectors

Use the quick range buttons for common time periods:
- **5m, 15m, 30m**: Short-term monitoring
- **1h, 3h, 6h**: Medium-term analysis
- **12h, 24h**: Long-term trends

### Custom Time Ranges

1. **Start Time**: Set the beginning of your time window
2. **End Time**: Set the end of your time window
3. **Step/Resolution**: Control data granularity (for range queries)

### Resolution (Step) Guidelines

Choose appropriate step sizes based on your time range:
- **5s-15s**: For ranges up to 15 minutes
- **30s-1m**: For ranges up to 1 hour
- **5m-15m**: For ranges up to 12 hours
- **30m-1h**: For ranges over 12 hours

## Visualization Features

### Chart Types

- **Line Charts**: Time-series data with trend lines
- **Bar Charts**: Instant values comparison
- **Area Charts**: Filled line charts for better visual impact

### Interactive Features

- **Zoom**: Use mouse wheel or zoom controls to focus on specific time periods
- **Pan**: Drag to move through different time ranges
- **Legend**: Click series names to show/hide specific metrics
- **Tooltips**: Hover over data points for detailed information

### Chart Customization

Charts automatically:
- Use distinct colors for different metric series
- Format timestamps in readable format
- Scale axes appropriately
- Show metric labels with full context

## Best Practices

### Query Performance

1. **Use Specific Labels**: Filter metrics with relevant labels to reduce data volume
2. **Appropriate Time Ranges**: Don't query unnecessarily large time windows
3. **Efficient Functions**: Use `rate()` instead of `increase()` for per-second rates
4. **Limit Series**: Use aggregation functions to reduce the number of time series

### Monitoring Patterns

1. **Golden Signals**: Monitor latency, traffic, errors, and saturation
2. **RED Method**: Rate, Errors, Duration for request-driven services
3. **USE Method**: Utilization, Saturation, Errors for resource monitoring
4. **Baseline Establishment**: Create queries for normal operating conditions

### Query Organization

1. **Start Simple**: Begin with basic queries and add complexity gradually
2. **Use Comments**: Document complex queries for future reference
3. **Save Useful Queries**: Keep a collection of your most-used queries
4. **Test Incrementally**: Build complex queries step by step

## Troubleshooting

### Common Issues

#### No Data Returned
- **Check Time Range**: Ensure your time range includes periods with data
- **Verify Metric Names**: Confirm metric names are spelled correctly
- **Check Labels**: Ensure label filters match existing data
- **Tenant Isolation**: Remember that you only see data from your tenant

#### Query Errors
- **Syntax Errors**: Use the Examples and Functions helpers for correct syntax
- **Invalid Functions**: Refer to PromQL documentation for function usage
- **Type Mismatches**: Ensure functions are applied to appropriate data types

#### Performance Issues
- **Reduce Time Range**: Query smaller time windows
- **Add Label Filters**: Use specific labels to reduce data volume
- **Increase Step Size**: Use larger step sizes for long time ranges
- **Limit Series**: Use aggregation to reduce the number of time series

### Getting Help

1. **Query Examples**: Use the built-in examples as starting points
2. **Function Reference**: Explore the functions dropdown for syntax help
3. **PromQL Documentation**: Refer to official Prometheus documentation
4. **Error Messages**: Read error messages carefully for specific guidance

## Security and Tenant Isolation

### Data Access

- **Tenant Isolation**: You can only access metrics from your assigned tenant
- **Automatic Filtering**: All queries are automatically filtered by tenant ID
- **Secure Access**: All requests require valid authentication

### Privacy

- **No Cross-Tenant Access**: Metrics from other tenants are never visible
- **Audit Logging**: All query activities are logged for security purposes
- **Data Retention**: Metrics follow configured retention policies

## Advanced Usage

### Complex Queries

Build sophisticated monitoring queries by combining multiple functions:

```promql
# Calculate error rate percentage
(
  rate(http_requests_total{status=~"5.."}[5m]) /
  rate(http_requests_total[5m])
) * 100
```

### Alerting Preparation

Use the Metrics view to develop and test queries for alerting:

1. **Threshold Testing**: Find appropriate alert thresholds
2. **Query Validation**: Ensure queries return expected results
3. **Performance Testing**: Verify queries execute efficiently

### Integration with Other Views

Metrics work together with other ObservaStack features:

- **Traces**: Use metrics to identify performance issues, then drill down with traces
- **Logs**: Correlate metric spikes with log events
- **Alerts**: Convert tested queries into monitoring alerts

## Keyboard Shortcuts

- **Ctrl+Enter** (Cmd+Enter on Mac): Execute the current query
- **Tab**: Navigate between form fields
- **Escape**: Close dropdown menus

## Tips and Tricks

1. **Use the Examples**: Start with examples and modify them for your needs
2. **Experiment with Functions**: Try different PromQL functions to understand their behavior
3. **Monitor Regularly**: Set up regular monitoring routines for your key metrics
4. **Document Queries**: Keep notes on useful queries for future reference
5. **Combine with Time Ranges**: Use different time ranges to understand both immediate and long-term trends