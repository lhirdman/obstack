/**
 * Audit logs viewer for system administration
 */

import React, { useState } from 'react';
import { useAuditLogs } from '../../hooks/useAdmin';
import { AuditLogFilters } from '../../types/admin';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export function AuditLogs() {
  const [filters, setFilters] = useState<AuditLogFilters>({
    page: 1,
    page_size: 50,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  const { logs, loading, error } = useAuditLogs(filters);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setFilters(prev => ({
      ...prev,
      ...(query ? { user_id: query } : {}),
      page: 1,
    }));
  };

  const handleActionFilter = (action: string) => {
    setActionFilter(action);
    setFilters(prev => ({
      ...prev,
      ...(action ? { action } : {}),
      page: 1,
    }));
  };

  const handleResourceFilter = (resource: string) => {
    setResourceFilter(resource);
    setFilters(prev => ({
      ...prev,
      ...(resource ? { resource_type: resource } : {}),
      page: 1,
    }));
  };

  const handleDateRangeChange = (field: 'start' | 'end', value: string) => {
    const newRange = { ...dateRange, [field]: value };
    setDateRange(newRange);
    setFilters(prev => ({
      ...prev,
      ...(newRange.start ? { start_date: newRange.start } : {}),
      ...(newRange.end ? { end_date: newRange.end } : {}),
      page: 1,
    }));
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getActionBadge = (action: string) => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full';
    
    if (action.includes('create')) {
      return `${baseClasses} bg-green-100 text-green-800`;
    } else if (action.includes('delete')) {
      return `${baseClasses} bg-red-100 text-red-800`;
    } else if (action.includes('update')) {
      return `${baseClasses} bg-blue-100 text-blue-800`;
    } else {
      return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Audit Logs</h2>
        <p className="text-gray-600">View system activity and user actions</p>
      </div>

      {/* Filters */}
      <div className="mb-6 space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by user ID..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <select
              value={actionFilter}
              onChange={(e) => handleActionFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Actions</option>
              <option value="tenant_created">Tenant Created</option>
              <option value="tenant_updated">Tenant Updated</option>
              <option value="tenant_deleted">Tenant Deleted</option>
              <option value="user_login">User Login</option>
              <option value="user_logout">User Logout</option>
            </select>
          </div>
          <div>
            <select
              value={resourceFilter}
              onChange={(e) => handleResourceFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Resources</option>
              <option value="tenant">Tenant</option>
              <option value="user">User</option>
              <option value="alert">Alert</option>
              <option value="dashboard">Dashboard</option>
            </select>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
            <input
              type="datetime-local"
              value={dateRange.start}
              onChange={(e) => handleDateRangeChange('start', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
            <input
              type="datetime-local"
              value={dateRange.end}
              onChange={(e) => handleDateRangeChange('end', e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      )}

      {/* Audit Logs Table */}
      {!loading && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Resource
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Details
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {logs.logs.length > 0 ? (
                  logs.logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(log.timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {log.user_id}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={getActionBadge(log.action)}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{log.resource_type}</div>
                          {log.resource_id && (
                            <div className="text-gray-500 text-xs">{log.resource_id}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div className="max-w-xs truncate">
                          {Object.keys(log.details).length > 0 ? (
                            <pre className="text-xs bg-gray-100 p-2 rounded">
                              {JSON.stringify(log.details, null, 2)}
                            </pre>
                          ) : (
                            'No details'
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-6 py-12 text-center">
                      <div className="text-gray-500">
                        <div className="text-4xl mb-4">📋</div>
                        <h3 className="text-lg font-medium mb-2">No audit logs found</h3>
                        <p>No logs match the current filters.</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {logs.total > logs.page_size && (
            <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
              <div className="flex items-center justify-between">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    disabled={logs.page <= 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  <button
                    disabled={logs.page >= Math.ceil(logs.total / logs.page_size)}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing{' '}
                      <span className="font-medium">
                        {(logs.page - 1) * logs.page_size + 1}
                      </span>{' '}
                      to{' '}
                      <span className="font-medium">
                        {Math.min(logs.page * logs.page_size, logs.total)}
                      </span>{' '}
                      of <span className="font-medium">{logs.total}</span> results
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}