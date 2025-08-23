---
sidebar_position: 3
---

# Traces

The Traces view in ObservaStack allows you to search for and visualize distributed traces in a waterfall diagram format. This powerful tool helps you debug performance issues, understand service dependencies, and analyze request flows across your microservices architecture.

## Getting Started

### Accessing the Traces View

1. **From the Dashboard**: Click the "Open Traces" button on the main dashboard
2. **From the Navigation**: Use the "Traces" link in the top navigation bar
3. **Direct URL**: Navigate to `/traces` in your browser

### Basic Interface

The Traces view consists of three main sections:

- **Trace Search Panel**: Where you enter trace IDs to search for specific traces
- **Waterfall Visualization**: Visual representation of spans in chronological order
- **Span Details Panel**: Detailed information about the selected span

## Searching for Traces

### Trace ID Search

Currently, the primary method for finding traces is by trace ID:

1. **Enter Trace ID**: Input the hexadecimal trace ID in the search field
2. **Validation**: The system validates the format (16-32 hexadecimal characters)
3. **Execute Search**: Click "Search Trace" or press Enter
4. **View Results**: The waterfall diagram displays if the trace is found

### Trace ID Format

- **Valid Characters**: 0-9, a-f, A-F (hexadecimal)
- **Length**: Typically 16 or 32 characters
- **Example**: `1234567890abcdef` or `1234567890abcdef1234567890abcdef`

### Search History

The interface automatically saves your recent searches:

- **Recent Searches**: Up to 5 recent trace IDs are saved
- **Quick Access**: Click on any history item to search again
- **Automatic Cleanup**: History is maintained per browser session

## Understanding the Waterfall View

### Trace Overview

The waterfall view provides a comprehensive visualization of your distributed trace:

- **Timeline**: Horizontal axis showing time progression
- **Spans**: Individual operations represented as colored bars
- **Hierarchy**: Parent-child relationships shown through indentation
- **Services**: Different colors represent different services

### Trace Summary

At the top of the waterfall, you'll find key metrics:

- **Total Duration**: Complete time from first span start to last span end
- **Span Count**: Total number of spans in the trace
- **Start Time**: When the trace began
- **Service Count**: Number of unique services involved

### Timeline Scale

The timeline provides temporal context:

- **Time Markers**: 0%, 25%, 50%, 75%, and 100% of total duration
- **Proportional Scaling**: Span widths represent relative duration
- **Visual Alignment**: Spans are positioned based on their start times

### Span Representation

Each span in the waterfall contains:

- **Status Indicator**: Colored dot showing success (green), warning (yellow), or error (red)
- **Service Name**: Which service generated the span
- **Operation Name**: What operation was performed
- **Duration**: How long the operation took
- **Timeline Bar**: Visual representation of timing and duration

### Hierarchy and Relationships

- **Indentation**: Child spans are indented under their parents
- **Color Coding**: Each service has a consistent color throughout the trace
- **Nesting Levels**: Multiple levels of nesting show complex call chains

## Span Details

### Selecting Spans

Click on any span in the waterfall to view detailed information:

- **Span Overview**: High-level information about the selected span
- **Timing Details**: Precise start time, end time, and duration
- **Identifiers**: Trace ID, span ID, and parent span ID
- **Attributes**: Key-value pairs providing context about the operation

### Span Status

Each span has a status indicating the outcome:

- **OK (Green)**: Operation completed successfully
- **Cancelled (Yellow)**: Operation was cancelled
- **Error (Red)**: Operation failed with an error
- **Unset (Gray)**: No status information available

### Timing Information

Detailed timing data includes:

- **Start Time**: When the span began (with millisecond precision)
- **End Time**: When the span completed
- **Duration**: Total time taken (displayed in appropriate units)

### Attributes by Category

Span attributes are organized into logical groups:

#### HTTP Attributes
- **Method**: HTTP method (GET, POST, etc.)
- **URL/Target**: Request URL or path
- **Status Code**: HTTP response status
- **User Agent**: Client information

#### Database Attributes
- **Statement**: SQL query or database operation
- **Connection**: Database connection details
- **Table**: Target table or collection

#### RPC Attributes
- **Service**: Remote service name
- **Method**: RPC method called
- **System**: RPC system type

#### Other Attributes
- **Custom Tags**: Application-specific metadata
- **Infrastructure**: Deployment and runtime information

### Hierarchy Information

For each span, you can see:

- **Level**: Depth in the call hierarchy
- **Children Count**: Number of direct child spans
- **Parent Relationship**: Whether the span has a parent

## Performance Analysis

### Identifying Bottlenecks

Use the waterfall view to identify performance issues:

1. **Long Spans**: Look for spans with disproportionately long durations
2. **Sequential Operations**: Identify operations that could be parallelized
3. **Service Boundaries**: Analyze time spent in different services
4. **Database Queries**: Check for slow or frequent database operations

### Understanding Service Dependencies

The trace visualization reveals:

- **Service Call Patterns**: How services interact with each other
- **Critical Path**: The longest chain of dependent operations
- **Parallel Processing**: Operations that run concurrently
- **External Dependencies**: Calls to external services or APIs

### Error Analysis

When investigating errors:

1. **Error Propagation**: See how errors flow through the system
2. **Failure Points**: Identify where in the call chain errors occur
3. **Context Information**: Use span attributes to understand error conditions
4. **Recovery Patterns**: Observe retry and fallback mechanisms

## Best Practices

### Effective Trace Analysis

1. **Start with Overview**: Review the trace summary before diving into details
2. **Follow the Critical Path**: Focus on the longest-running sequence of spans
3. **Check Error Spans**: Always investigate spans with error status
4. **Compare Similar Traces**: Look at multiple traces for the same operation

### Using Span Details

1. **Examine Attributes**: Span attributes often contain crucial debugging information
2. **Check Timing**: Look for unexpected delays or timing patterns
3. **Understand Context**: Use service and operation names to understand the business logic
4. **Correlate with Logs**: Use span IDs to find related log entries

### Performance Optimization

1. **Identify Hotspots**: Focus on spans that consume the most time
2. **Analyze Parallelization**: Look for opportunities to run operations concurrently
3. **Database Optimization**: Pay special attention to database query spans
4. **Service Boundaries**: Consider the cost of service-to-service communication

## Troubleshooting

### Common Issues

#### Trace Not Found
- **Check Trace ID**: Ensure the trace ID is correctly formatted
- **Verify Permissions**: You can only access traces from your tenant
- **Time Range**: Traces may have expired based on retention policies
- **Service Configuration**: Ensure your services are properly instrumented

#### Empty or Incomplete Traces
- **Instrumentation**: Verify that all services are properly instrumented
- **Sampling**: Check if trace sampling is affecting data collection
- **Network Issues**: Ensure trace data is being transmitted successfully
- **Storage**: Verify that the tracing backend is storing data correctly

#### Missing Span Details
- **Attribute Collection**: Check if span attributes are being collected
- **Data Limits**: Some attributes may be truncated due to size limits
- **Configuration**: Verify instrumentation configuration in your services

### Getting Help

1. **Trace ID Validation**: Use the built-in validation to ensure proper format
2. **Search Tips**: Refer to the search tips panel for guidance
3. **Error Messages**: Read error messages carefully for specific guidance
4. **Documentation**: Consult your tracing system's documentation for instrumentation help

## Security and Privacy

### Data Access

- **Tenant Isolation**: You can only access traces from your assigned tenant
- **Automatic Filtering**: All searches are automatically filtered by tenant ID
- **Secure Transmission**: All trace data is transmitted securely

### Privacy Considerations

- **Sensitive Data**: Be cautious about including sensitive information in span attributes
- **Data Retention**: Traces are subject to configured retention policies
- **Access Logging**: Trace access activities are logged for security purposes

## Advanced Features

### Raw Span Data

For debugging and integration purposes:

- **JSON Export**: View the complete span data in JSON format
- **API Integration**: Use the raw data for custom analysis tools
- **Debugging**: Examine the exact data structure for troubleshooting

### Integration with Other Views

Traces work together with other ObservaStack features:

- **Metrics Correlation**: Use trace timing to understand metric spikes
- **Log Correlation**: Use span IDs to find related log entries
- **Alert Investigation**: Use traces to investigate alert conditions

## Tips and Tricks

1. **Bookmark Interesting Traces**: Save trace IDs for important examples
2. **Use Search History**: Leverage the recent searches for quick access
3. **Focus on Critical Path**: Start analysis with the longest-running spans
4. **Check Service Colors**: Use consistent service colors to track service involvement
5. **Examine Error Context**: Error spans often contain the most valuable debugging information
6. **Compare Before and After**: Use traces to validate performance improvements
7. **Document Patterns**: Keep notes on common trace patterns for your applications

## Keyboard Shortcuts

- **Enter**: Execute trace search from the search field
- **Tab**: Navigate between interface elements
- **Escape**: Close any open dropdowns or modals

## Future Enhancements

The Traces view will continue to evolve with additional features:

- **Advanced Search**: Search by service name, operation, tags, and time ranges
- **Trace Comparison**: Side-by-side comparison of multiple traces
- **Performance Baselines**: Compare traces against historical baselines
- **Custom Views**: Save and share custom trace analysis views