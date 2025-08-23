import React, { useState } from 'react';
import { CodeBracketIcon, BookOpenIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

interface QueryBuilderProps {
  query: string;
  onQueryChange: (query: string) => void;
  onExecute: () => void;
}

const COMMON_QUERIES = [
  {
    name: 'System Health',
    queries: [
      { label: 'Up Status', query: 'up' },
      { label: 'CPU Usage', query: 'rate(cpu_usage_total[5m])' },
      { label: 'Memory Usage', query: 'memory_usage_bytes / memory_total_bytes * 100' },
      { label: 'Disk Usage', query: 'disk_usage_bytes / disk_total_bytes * 100' },
    ]
  },
  {
    name: 'HTTP Metrics',
    queries: [
      { label: 'Request Rate', query: 'rate(http_requests_total[5m])' },
      { label: 'Error Rate', query: 'rate(http_requests_total{status=~"5.."}[5m])' },
      { label: 'Response Time', query: 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))' },
      { label: 'Request Count', query: 'sum(http_requests_total) by (method, status)' },
    ]
  },
  {
    name: 'Application Metrics',
    queries: [
      { label: 'Active Connections', query: 'active_connections' },
      { label: 'Queue Length', query: 'queue_length' },
      { label: 'Processing Time', query: 'avg(processing_time_seconds)' },
      { label: 'Error Count', query: 'sum(errors_total) by (type)' },
    ]
  }
];

const PROMQL_FUNCTIONS = [
  'rate()', 'increase()', 'sum()', 'avg()', 'max()', 'min()', 'count()',
  'histogram_quantile()', 'by()', 'without()', 'group_left()', 'group_right()',
  'abs()', 'ceil()', 'floor()', 'round()', 'sqrt()', 'exp()', 'ln()', 'log2()', 'log10()'
];

const QueryBuilder: React.FC<QueryBuilderProps> = ({
  query,
  onQueryChange,
  onExecute
}) => {
  const [showExamples, setShowExamples] = useState(false);
  const [showFunctions, setShowFunctions] = useState(false);

  const handleQuerySelect = (selectedQuery: string) => {
    onQueryChange(selectedQuery);
    setShowExamples(false);
  };

  const handleFunctionInsert = (func: string) => {
    // Insert function at cursor position or at the end
    const textarea = document.querySelector('textarea[name="query"]') as HTMLTextAreaElement;
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newQuery = query.substring(0, start) + func + query.substring(end);
      onQueryChange(newQuery);
      
      // Set cursor position after the inserted function
      setTimeout(() => {
        textarea.focus();
        textarea.setSelectionRange(start + func.length, start + func.length);
      }, 0);
    } else {
      onQueryChange(query + func);
    }
    setShowFunctions(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      onExecute();
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-sm font-medium text-gray-700 flex items-center">
            <CodeBracketIcon className="h-4 w-4 mr-1" />
            PromQL Query
          </label>
          <div className="flex space-x-2">
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowExamples(!showExamples)}
                className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 border border-gray-300 rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <BookOpenIcon className="h-3 w-3 mr-1" />
                Examples
                <ChevronDownIcon className="h-3 w-3 ml-1" />
              </button>
              
              {showExamples && (
                <div className="absolute right-0 mt-1 w-80 bg-white border border-gray-200 rounded-md shadow-lg z-10 max-h-96 overflow-y-auto">
                  {COMMON_QUERIES.map((category) => (
                    <div key={category.name} className="p-2">
                      <h4 className="text-xs font-semibold text-gray-700 mb-2 px-2">
                        {category.name}
                      </h4>
                      {category.queries.map((item) => (
                        <button
                          key={item.label}
                          onClick={() => handleQuerySelect(item.query)}
                          className="w-full text-left px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded block"
                        >
                          <div className="font-medium">{item.label}</div>
                          <div className="text-gray-500 font-mono text-xs truncate">
                            {item.query}
                          </div>
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowFunctions(!showFunctions)}
                className="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 border border-gray-300 rounded hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Functions
                <ChevronDownIcon className="h-3 w-3 ml-1" />
              </button>
              
              {showFunctions && (
                <div className="absolute right-0 mt-1 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-10 max-h-64 overflow-y-auto">
                  <div className="p-2">
                    {PROMQL_FUNCTIONS.map((func) => (
                      <button
                        key={func}
                        onClick={() => handleFunctionInsert(func)}
                        className="w-full text-left px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded font-mono"
                      >
                        {func}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <textarea
          name="query"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Enter PromQL query (e.g., up, rate(http_requests_total[5m]))"
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm resize-y"
        />
        
        <div className="mt-1 text-xs text-gray-500">
          Press Ctrl+Enter (Cmd+Enter on Mac) to execute the query
        </div>
      </div>

      {/* Query Validation */}
      {query.trim() && (
        <div className="text-xs">
          {query.trim().length > 0 && (
            <div className="flex items-center text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              Query ready to execute
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QueryBuilder;