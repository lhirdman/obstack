import React, { useMemo } from 'react';
import { format } from 'date-fns';

interface ProcessedSpan {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  name: string;
  startTime: number;
  endTime: number;
  duration: number;
  attributes: Record<string, any>;
  status?: {
    code: number;
    message?: string;
  };
  serviceName?: string;
  operationName: string;
  level: number;
  children: ProcessedSpan[];
}

interface TraceWaterfallProps {
  spans: ProcessedSpan[];
  selectedSpan: ProcessedSpan | null;
  onSpanSelect: (span: ProcessedSpan) => void;
}

const TraceWaterfall: React.FC<TraceWaterfallProps> = ({ spans, selectedSpan, onSpanSelect }) => {
  const { traceStartTime, traceEndTime, traceDuration } = useMemo(() => {
    if (spans.length === 0) return { traceStartTime: 0, traceEndTime: 0, traceDuration: 0 };
    
    const startTime = Math.min(...spans.map(span => span.startTime));
    const endTime = Math.max(...spans.map(span => span.endTime));
    
    return {
      traceStartTime: startTime,
      traceEndTime: endTime,
      traceDuration: endTime - startTime
    };
  }, [spans]);

  const getSpanPosition = (span: ProcessedSpan) => {
    if (traceDuration === 0) return { left: 0, width: 100 };
    
    const relativeStart = span.startTime - traceStartTime;
    const left = (relativeStart / traceDuration) * 100;
    const width = Math.max((span.duration / traceDuration) * 100, 0.5); // Minimum width for visibility
    
    return { left, width };
  };

  const getSpanColor = (span: ProcessedSpan): string => {
    // Color based on service name
    const colors = [
      '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
      '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1'
    ];
    
    if (span.serviceName) {
      const hash = span.serviceName.split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
      }, 0);
      return colors[Math.abs(hash) % colors.length] || colors[0];
    }
    
    return colors[0] || '#3b82f6';
  };

  const getStatusColor = (span: ProcessedSpan): string => {
    if (span.status?.code === 2) return 'bg-red-500'; // Error
    if (span.status?.code === 1) return 'bg-yellow-500'; // Warning
    return 'bg-green-500'; // OK or unset
  };

  const formatDuration = (duration: number): string => {
    if (duration < 1) return `${(duration * 1000).toFixed(2)}μs`;
    if (duration < 1000) return `${duration.toFixed(2)}ms`;
    return `${(duration / 1000).toFixed(2)}s`;
  };

  const formatTime = (timestamp: number): string => {
    return format(new Date(timestamp), 'HH:mm:ss.SSS');
  };

  if (spans.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No spans to display
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Trace Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Total Duration:</span>
            <span className="ml-2 font-medium">{formatDuration(traceDuration)}</span>
          </div>
          <div>
            <span className="text-gray-500">Spans:</span>
            <span className="ml-2 font-medium">{spans.length}</span>
          </div>
          <div>
            <span className="text-gray-500">Start Time:</span>
            <span className="ml-2 font-medium">{formatTime(traceStartTime)}</span>
          </div>
          <div>
            <span className="text-gray-500">Services:</span>
            <span className="ml-2 font-medium">
              {new Set(spans.map(span => span.serviceName).filter(Boolean)).size}
            </span>
          </div>
        </div>
      </div>

      {/* Timeline Header */}
      <div className="relative">
        <div className="flex justify-between text-xs text-gray-500 mb-2">
          <span>0ms</span>
          <span>{formatDuration(traceDuration / 4)}</span>
          <span>{formatDuration(traceDuration / 2)}</span>
          <span>{formatDuration((traceDuration * 3) / 4)}</span>
          <span>{formatDuration(traceDuration)}</span>
        </div>
        <div className="h-px bg-gray-200 relative">
          <div className="absolute left-1/4 top-0 w-px h-2 bg-gray-300"></div>
          <div className="absolute left-1/2 top-0 w-px h-2 bg-gray-300"></div>
          <div className="absolute left-3/4 top-0 w-px h-2 bg-gray-300"></div>
        </div>
      </div>

      {/* Spans */}
      <div className="space-y-1">
        {spans.map((span, index) => {
          const position = getSpanPosition(span);
          const isSelected = selectedSpan?.spanId === span.spanId;
          const spanColor = getSpanColor(span);
          
          return (
            <div
              key={span.spanId}
              className={`relative cursor-pointer transition-all duration-200 ${
                isSelected ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'
              } border rounded p-2`}
              onClick={() => onSpanSelect(span)}
            >
              {/* Span Info */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2 min-w-0 flex-1">
                  {/* Indentation for hierarchy */}
                  <div style={{ marginLeft: `${span.level * 20}px` }} className="flex items-center space-x-2 min-w-0">
                    {/* Status indicator */}
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(span)}`}></div>
                    
                    {/* Service name */}
                    <span className="text-xs text-gray-500 font-medium">
                      {span.serviceName || 'unknown'}
                    </span>
                    
                    {/* Operation name */}
                    <span className="text-sm font-medium text-gray-900 truncate">
                      {span.operationName}
                    </span>
                  </div>
                </div>
                
                {/* Duration */}
                <div className="text-xs text-gray-500 font-mono">
                  {formatDuration(span.duration)}
                </div>
              </div>

              {/* Timeline bar */}
              <div className="relative h-6 bg-gray-100 rounded">
                <div
                  className="absolute top-1 h-4 rounded transition-all duration-200"
                  style={{
                    left: `${position.left}%`,
                    width: `${position.width}%`,
                    backgroundColor: spanColor,
                    opacity: isSelected ? 1 : 0.8
                  }}
                >
                  {/* Span duration label (if wide enough) */}
                  {position.width > 10 && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xs text-white font-medium">
                        {formatDuration(span.duration)}
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Start time marker */}
                <div
                  className="absolute top-0 w-px h-6 bg-gray-400"
                  style={{ left: `${position.left}%` }}
                ></div>
              </div>

              {/* Additional span info */}
              <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                <div className="flex items-center space-x-4">
                  <span>Start: {formatTime(span.startTime)}</span>
                  {span.attributes['http.method'] && (
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {span.attributes['http.method']} {span.attributes['http.url'] || span.attributes['http.target']}
                    </span>
                  )}
                  {span.attributes['db.statement'] && (
                    <span className="px-2 py-1 bg-blue-100 rounded">
                      DB Query
                    </span>
                  )}
                </div>
                <span className="font-mono">
                  {span.spanId.substring(0, 8)}...
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Legend</h4>
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span>Success</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
            <span>Warning</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 rounded-full bg-red-500"></div>
            <span>Error</span>
          </div>
          <div className="flex items-center space-x-1">
            <span>Colors represent different services</span>
          </div>
          <div className="flex items-center space-x-1">
            <span>Indentation shows span hierarchy</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TraceWaterfall;