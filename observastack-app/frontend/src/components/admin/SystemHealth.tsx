/**
 * System health monitoring interface
 */

import React from 'react';
import { useSystemSettings } from '../../hooks/useAdmin';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export function SystemHealth() {
  const { health, metrics, loading, error } = useSystemSettings();

  const getHealthBadge = (status: string) => {
    const baseClasses = 'px-3 py-1 text-sm font-medium rounded-full';
    
    switch (status) {
      case 'healthy':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'degraded':
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case 'unhealthy':
        return `${baseClasses} bg-red-100 text-red-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">System Health</h2>
        <p className="text-gray-600">Monitor system performance and service status</p>
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

      {/* Health Overview */}
      {!loading && (
        <div className="space-y-6">
          {/* Overall System Status */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">System Status</h3>
              <span className={getHealthBadge(health?.status || 'unknown')}>
                {health?.status || 'Unknown'}
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">99.9%</div>
                <div className="text-sm text-gray-500">Uptime</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {formatUptime(metrics?.uptime || 86400)}
                </div>
                <div className="text-sm text-gray-500">Current Uptime</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {metrics?.active_connections || 0}
                </div>
                <div className="text-sm text-gray-500">Active Connections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {metrics?.requests_per_minute || 0}
                </div>
                <div className="text-sm text-gray-500">Requests/min</div>
              </div>
            </div>
          </div>

          {/* Service Health */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Service Health</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { name: 'API Gateway', status: 'healthy', response_time: '45ms' },
                { name: 'Database', status: 'healthy', response_time: '12ms' },
                { name: 'Redis Cache', status: 'healthy', response_time: '3ms' },
                { name: 'Prometheus', status: 'healthy', response_time: '23ms' },
                { name: 'Loki', status: 'degraded', response_time: '156ms' },
                { name: 'Grafana', status: 'healthy', response_time: '67ms' },
              ].map((service) => (
                <div key={service.name} className="p-4 bg-gray-50 rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-900">{service.name}</h4>
                    <span className={getHealthBadge(service.status)}>
                      {service.status}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">
                    Response time: {service.response_time}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Resource Usage */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">CPU Usage</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Current</span>
                  <span className="text-sm font-medium">23%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '23%' }}></div>
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Average: 18%</span>
                  <span>Peak: 67%</span>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Memory Usage</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Current</span>
                  <span className="text-sm font-medium">
                    {formatBytes(metrics?.memory_used || 0)} / {formatBytes(metrics?.memory_total || 0)}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: '45%' }}></div>
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>45% used</span>
                  <span>Available: {formatBytes((metrics?.memory_total || 0) - (metrics?.memory_used || 0))}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Storage Usage */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Storage Usage</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[
                { name: 'Logs', used: 2.3, total: 10, unit: 'TB' },
                { name: 'Metrics', used: 850, total: 2000, unit: 'GB' },
                { name: 'Traces', used: 156, total: 500, unit: 'GB' },
              ].map((storage) => (
                <div key={storage.name} className="p-4 bg-gray-50 rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-900">{storage.name}</h4>
                    <span className="text-xs text-gray-500">
                      {storage.used} / {storage.total} {storage.unit}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-600 h-2 rounded-full" 
                      style={{ width: `${(storage.used / storage.total) * 100}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {Math.round((storage.used / storage.total) * 100)}% used
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Recent System Alerts</h3>
            <div className="space-y-3">
              {[
                {
                  id: 1,
                  severity: 'warning',
                  message: 'High memory usage detected on node-2',
                  timestamp: '2 minutes ago',
                },
                {
                  id: 2,
                  severity: 'info',
                  message: 'Scheduled maintenance completed successfully',
                  timestamp: '1 hour ago',
                },
                {
                  id: 3,
                  severity: 'error',
                  message: 'Temporary connection timeout to Loki service',
                  timestamp: '3 hours ago',
                },
              ].map((alert) => (
                <div key={alert.id} className="flex items-center p-3 bg-gray-50 rounded-md">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    alert.severity === 'error' ? 'bg-red-500' :
                    alert.severity === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                  }`}></div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{alert.message}</p>
                    <p className="text-xs text-gray-500">{alert.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}