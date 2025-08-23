import React, { useState } from 'react';
import { MagnifyingGlassIcon, ClockIcon } from '@heroicons/react/24/outline';

interface TraceSearchProps {
  onSearch: (traceId: string) => void;
  isLoading: boolean;
}

const TraceSearch: React.FC<TraceSearchProps> = ({ onSearch, isLoading }) => {
  const [traceId, setTraceId] = useState('');
  const [searchHistory, setSearchHistory] = useState<string[]>([]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (traceId.trim()) {
      onSearch(traceId.trim());
      
      // Add to search history (keep last 5)
      setSearchHistory(prev => {
        const newHistory = [traceId.trim(), ...prev.filter(id => id !== traceId.trim())];
        return newHistory.slice(0, 5);
      });
    }
  };

  const handleHistorySelect = (selectedTraceId: string) => {
    setTraceId(selectedTraceId);
    onSearch(selectedTraceId);
  };

  const isValidTraceId = (id: string): boolean => {
    // Basic validation for hex string (16 or 32 characters)
    return /^[0-9a-fA-F]{16,32}$/.test(id);
  };

  return (
    <div className="space-y-4">
      {/* Search Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="traceId" className="block text-sm font-medium text-gray-700 mb-2">
            Trace ID
          </label>
          <div className="relative">
            <input
              type="text"
              id="traceId"
              value={traceId}
              onChange={(e) => setTraceId(e.target.value)}
              placeholder="Enter trace ID (e.g., 1234567890abcdef)"
              className="w-full px-4 py-2 pr-12 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!traceId.trim() || isLoading}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
              ) : (
                <MagnifyingGlassIcon className="h-5 w-5" />
              )}
            </button>
          </div>
          
          {/* Validation feedback */}
          {traceId && !isValidTraceId(traceId) && (
            <p className="mt-1 text-xs text-amber-600">
              Trace ID should be a hexadecimal string (16-32 characters)
            </p>
          )}
          
          {traceId && isValidTraceId(traceId) && (
            <p className="mt-1 text-xs text-green-600">
              Valid trace ID format
            </p>
          )}
        </div>

        <div className="flex justify-between items-center">
          <button
            type="submit"
            disabled={!traceId.trim() || isLoading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Searching...
              </>
            ) : (
              <>
                <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
                Search Trace
              </>
            )}
          </button>
          
          <div className="text-xs text-gray-500">
            Press Enter to search
          </div>
        </div>
      </form>

      {/* Search History */}
      {searchHistory.length > 0 && (
        <div>
          <div className="flex items-center mb-2">
            <ClockIcon className="h-4 w-4 text-gray-400 mr-1" />
            <h3 className="text-sm font-medium text-gray-700">Recent Searches</h3>
          </div>
          <div className="space-y-1">
            {searchHistory.map((historyTraceId, index) => (
              <button
                key={index}
                onClick={() => handleHistorySelect(historyTraceId)}
                className="w-full text-left px-3 py-2 text-xs font-mono text-gray-600 bg-gray-50 hover:bg-gray-100 rounded border transition-colors"
                disabled={isLoading}
              >
                {historyTraceId}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Search Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Search Tips</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• Trace IDs are hexadecimal strings (0-9, a-f)</li>
          <li>• Typical length is 16 or 32 characters</li>
          <li>• You can only search traces from your tenant</li>
          <li>• Recent searches are saved for quick access</li>
        </ul>
      </div>
    </div>
  );
};

export default TraceSearch;