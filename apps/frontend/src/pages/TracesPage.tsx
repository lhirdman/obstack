import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MagnifyingGlassIcon, DocumentMagnifyingGlassIcon, ClockIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../lib/api-client';
import TraceSearch from '../components/TraceSearch';
import TraceWaterfall from '../components/TraceWaterfall';
import TraceDetails from '../components/TraceDetails';

interface Trace {
  batches: Array<{
    resource: {
      attributes: Array<{
        key: string;
        value: { stringValue?: string; intValue?: string; doubleValue?: number; boolValue?: boolean };
      }>;
    };
    scopeSpans: Array<{
      spans: Array<{
        traceId: string;
        spanId: string;
        parentSpanId?: string;
        name: string;
        startTimeUnixNano: string;
        endTimeUnixNano: string;
        attributes: Array<{
          key: string;
          value: { stringValue?: string; intValue?: string; doubleValue?: number; boolValue?: boolean };
        }>;
        status?: {
          code: number;
          message?: string;
        };
      }>;
    }>;
  }>;
}

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

const TracesPage: React.FC = () => {
  const [selectedTraceId, setSelectedTraceId] = useState<string>('');
  const [selectedSpan, setSelectedSpan] = useState<ProcessedSpan | null>(null);
  const [searchExecuted, setSearchExecuted] = useState(false);

  // Query for trace data
  const { data: traceData, isLoading, error, refetch } = useQuery({
    queryKey: ['trace', selectedTraceId],
    queryFn: async (): Promise<Trace> => {
      return apiClient.get(`/traces/${selectedTraceId}`);
    },
    enabled: searchExecuted && !!selectedTraceId.trim(),
    retry: false,
    staleTime: 60000, // 1 minute
  });

  const handleTraceSearch = (traceId: string) => {
    setSelectedTraceId(traceId);
    setSelectedSpan(null);
    setSearchExecuted(true);
    refetch();
  };

  const handleSpanSelect = (span: ProcessedSpan) => {
    setSelectedSpan(span);
  };

  const processTraceData = (trace: Trace): ProcessedSpan[] => {
    if (!trace?.batches) return [];

    const spans: ProcessedSpan[] = [];
    const spanMap = new Map<string, ProcessedSpan>();

    // First pass: create all spans
    trace.batches.forEach(batch => {
      const serviceName = batch.resource.attributes.find(attr => attr.key === 'service.name')?.value.stringValue || 'unknown';
      
      batch.scopeSpans.forEach(scopeSpan => {
        scopeSpan.spans.forEach(span => {
          const startTime = parseInt(span.startTimeUnixNano) / 1000000; // Convert to milliseconds
          const endTime = parseInt(span.endTimeUnixNano) / 1000000;
          
          const attributes: Record<string, any> = {};
          span.attributes.forEach(attr => {
            const value = attr.value.stringValue || attr.value.intValue || attr.value.doubleValue || attr.value.boolValue;
            attributes[attr.key] = value;
          });

          const processedSpan: ProcessedSpan = {
            traceId: span.traceId,
            spanId: span.spanId,
            parentSpanId: span.parentSpanId || undefined,
            name: span.name,
            startTime,
            endTime,
            duration: endTime - startTime,
            attributes,
            status: span.status,
            serviceName,
            operationName: span.name,
            level: 0,
            children: []
          };

          spans.push(processedSpan);
          spanMap.set(span.spanId, processedSpan);
        });
      });
    });

    // Second pass: build hierarchy and calculate levels
    const rootSpans: ProcessedSpan[] = [];
    
    spans.forEach(span => {
      if (span.parentSpanId && spanMap.has(span.parentSpanId)) {
        const parent = spanMap.get(span.parentSpanId)!;
        parent.children.push(span);
        span.level = parent.level + 1;
      } else {
        rootSpans.push(span);
      }
    });

    // Sort spans by start time
    const sortSpans = (spanList: ProcessedSpan[]) => {
      spanList.sort((a, b) => a.startTime - b.startTime);
      spanList.forEach(span => sortSpans(span.children));
    };
    
    sortSpans(rootSpans);
    return rootSpans;
  };

  const processedSpans = traceData ? processTraceData(traceData) : [];
  const flatSpans = processedSpans.length > 0 ? flattenSpans(processedSpans) : [];

  function flattenSpans(spans: ProcessedSpan[]): ProcessedSpan[] {
    const result: ProcessedSpan[] = [];
    spans.forEach(span => {
      result.push(span);
      result.push(...flattenSpans(span.children));
    });
    return result;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center">
            <DocumentMagnifyingGlassIcon className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Traces</h1>
          </div>
          <p className="mt-2 text-gray-600">
            Search and visualize distributed traces to understand request flows and performance
          </p>
        </div>

        {/* Search Section */}
        <div className="bg-white shadow rounded-lg mb-6">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Trace Search</h2>
          </div>
          <div className="p-6">
            <TraceSearch
              onSearch={handleTraceSearch}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Results Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Waterfall View */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-medium text-gray-900">Trace Waterfall</h2>
                  {traceData && flatSpans.length > 0 && (
                    <div className="flex items-center text-sm text-gray-500">
                      <ClockIcon className="h-4 w-4 mr-1" />
                      {flatSpans.length} spans
                    </div>
                  )}
                </div>
              </div>
              <div className="p-6">
                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                    <div className="flex">
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-red-800">
                          Trace Not Found
                        </h3>
                        <div className="mt-2 text-sm text-red-700">
                          {error instanceof Error ? error.message : 'The requested trace could not be found or you do not have permission to view it.'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {!searchExecuted && (
                  <div className="text-center py-12">
                    <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No trace selected</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Enter a trace ID above to view the distributed trace waterfall.
                    </p>
                  </div>
                )}

                {searchExecuted && isLoading && (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-sm text-gray-500">Loading trace...</p>
                  </div>
                )}

                {searchExecuted && !isLoading && !error && traceData && flatSpans.length > 0 && (
                  <TraceWaterfall
                    spans={flatSpans}
                    selectedSpan={selectedSpan}
                    onSpanSelect={handleSpanSelect}
                  />
                )}

                {searchExecuted && !isLoading && !error && traceData && flatSpans.length === 0 && (
                  <div className="text-center py-12">
                    <DocumentMagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No spans found</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      The trace exists but contains no span data.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Span Details */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Span Details</h2>
              </div>
              <div className="p-6">
                {selectedSpan ? (
                  <TraceDetails span={selectedSpan} />
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-500">
                      <svg className="mx-auto h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p className="mt-2 text-sm text-gray-500">
                        Click on a span in the waterfall to view its details
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TracesPage;