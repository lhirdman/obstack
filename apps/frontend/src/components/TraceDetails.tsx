import React from 'react';
import { format } from 'date-fns';
import { 
  ClockIcon, 
  ServerIcon, 
  TagIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

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

interface TraceDetailsProps {
  span: ProcessedSpan;
}

const TraceDetails: React.FC<TraceDetailsProps> = ({ span }) => {
  const formatDuration = (duration: number): string => {
    if (duration < 1) return `${(duration * 1000).toFixed(2)}μs`;
    if (duration < 1000) return `${duration.toFixed(2)}ms`;
    return `${(duration / 1000).toFixed(2)}s`;
  };

  const formatTime = (timestamp: number): string => {
    return format(new Date(timestamp), 'yyyy-MM-dd HH:mm:ss.SSS');
  };

  const getStatusInfo = (status?: { code: number; message?: string }) => {
    if (!status) {
      return {
        icon: CheckCircleIcon,
        color: 'text-gray-500',
        bgColor: 'bg-gray-100',
        label: 'Unset',
        description: 'No status information available'
      };
    }

    switch (status.code) {
      case 0:
        return {
          icon: CheckCircleIcon,
          color: 'text-green-600',
          bgColor: 'bg-green-100',
          label: 'OK',
          description: 'Operation completed successfully'
        };
      case 1:
        return {
          icon: ExclamationTriangleIcon,
          color: 'text-yellow-600',
          bgColor: 'bg-yellow-100',
          label: 'Cancelled',
          description: 'Operation was cancelled'
        };
      case 2:
        return {
          icon: XCircleIcon,
          color: 'text-red-600',
          bgColor: 'bg-red-100',
          label: 'Error',
          description: status.message || 'Operation failed with an error'
        };
      default:
        return {
          icon: ExclamationTriangleIcon,
          color: 'text-gray-600',
          bgColor: 'bg-gray-100',
          label: `Code ${status.code}`,
          description: status.message || 'Unknown status code'
        };
    }
  };

  const statusInfo = getStatusInfo(span.status);
  const StatusIcon = statusInfo.icon;

  // Group attributes by category
  const httpAttributes = Object.entries(span.attributes).filter(([key]) => key.startsWith('http.'));
  const dbAttributes = Object.entries(span.attributes).filter(([key]) => key.startsWith('db.'));
  const rpcAttributes = Object.entries(span.attributes).filter(([key]) => key.startsWith('rpc.'));
  const otherAttributes = Object.entries(span.attributes).filter(([key]) => 
    !key.startsWith('http.') && !key.startsWith('db.') && !key.startsWith('rpc.')
  );

  const renderAttributeGroup = (title: string, attributes: [string, any][], icon: React.ComponentType<any>) => {
    if (attributes.length === 0) return null;

    const IconComponent = icon;

    return (
      <div className="mb-4">
        <div className="flex items-center mb-2">
          <IconComponent className="h-4 w-4 text-gray-500 mr-2" />
          <h4 className="text-sm font-medium text-gray-700">{title}</h4>
        </div>
        <div className="space-y-1">
          {attributes.map(([key, value]) => (
            <div key={key} className="flex justify-between items-start text-xs">
              <span className="text-gray-600 font-medium mr-2 min-w-0 flex-1">
                {key.replace(/^(http|db|rpc)\./, '')}:
              </span>
              <span className="text-gray-900 font-mono break-all">
                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Span Overview */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Span Overview</h3>
        
        {/* Status */}
        <div className="mb-4">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${statusInfo.bgColor} ${statusInfo.color}`}>
            <StatusIcon className="h-4 w-4 mr-2" />
            {statusInfo.label}
          </div>
          {statusInfo.description && (
            <p className="text-xs text-gray-600 mt-1">{statusInfo.description}</p>
          )}
        </div>

        {/* Basic Info */}
        <div className="space-y-3 text-sm">
          <div className="flex items-center">
            <ServerIcon className="h-4 w-4 text-gray-400 mr-2" />
            <span className="text-gray-600">Service:</span>
            <span className="ml-2 font-medium">{span.serviceName || 'Unknown'}</span>
          </div>
          
          <div className="flex items-center">
            <TagIcon className="h-4 w-4 text-gray-400 mr-2" />
            <span className="text-gray-600">Operation:</span>
            <span className="ml-2 font-medium">{span.operationName}</span>
          </div>
          
          <div className="flex items-center">
            <ClockIcon className="h-4 w-4 text-gray-400 mr-2" />
            <span className="text-gray-600">Duration:</span>
            <span className="ml-2 font-medium">{formatDuration(span.duration)}</span>
          </div>
        </div>
      </div>

      {/* Timing Information */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">Timing</h4>
        <div className="bg-gray-50 rounded-lg p-3 space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-600">Start Time:</span>
            <span className="font-mono">{formatTime(span.startTime)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">End Time:</span>
            <span className="font-mono">{formatTime(span.endTime)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Duration:</span>
            <span className="font-mono font-medium">{formatDuration(span.duration)}</span>
          </div>
        </div>
      </div>

      {/* Span IDs */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">Identifiers</h4>
        <div className="space-y-2 text-xs">
          <div>
            <span className="text-gray-600 block mb-1">Trace ID:</span>
            <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono break-all">
              {span.traceId}
            </code>
          </div>
          <div>
            <span className="text-gray-600 block mb-1">Span ID:</span>
            <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono break-all">
              {span.spanId}
            </code>
          </div>
          {span.parentSpanId && (
            <div>
              <span className="text-gray-600 block mb-1">Parent Span ID:</span>
              <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono break-all">
                {span.parentSpanId}
              </code>
            </div>
          )}
        </div>
      </div>

      {/* Attributes */}
      {(httpAttributes.length > 0 || dbAttributes.length > 0 || rpcAttributes.length > 0 || otherAttributes.length > 0) && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-3">Attributes</h4>
          
          {renderAttributeGroup('HTTP', httpAttributes, TagIcon)}
          {renderAttributeGroup('Database', dbAttributes, ServerIcon)}
          {renderAttributeGroup('RPC', rpcAttributes, ServerIcon)}
          {renderAttributeGroup('Other', otherAttributes, TagIcon)}
        </div>
      )}

      {/* Hierarchy Info */}
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">Hierarchy</h4>
        <div className="bg-gray-50 rounded-lg p-3 space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-600">Level:</span>
            <span className="font-medium">{span.level}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Children:</span>
            <span className="font-medium">{span.children.length}</span>
          </div>
          {span.parentSpanId && (
            <div className="flex justify-between">
              <span className="text-gray-600">Has Parent:</span>
              <span className="font-medium text-green-600">Yes</span>
            </div>
          )}
        </div>
      </div>

      {/* Raw Data (Collapsible) */}
      <details className="group">
        <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-gray-900">
          Raw Span Data
        </summary>
        <div className="mt-3 bg-gray-900 rounded-lg p-3 overflow-auto">
          <pre className="text-xs text-gray-100">
            {JSON.stringify(
              {
                traceId: span.traceId,
                spanId: span.spanId,
                parentSpanId: span.parentSpanId,
                name: span.name,
                startTime: span.startTime,
                endTime: span.endTime,
                duration: span.duration,
                attributes: span.attributes,
                status: span.status,
                serviceName: span.serviceName,
                level: span.level
              },
              null,
              2
            )}
          </pre>
        </div>
      </details>
    </div>
  );
};

export default TraceDetails;