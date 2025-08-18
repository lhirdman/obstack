/**
 * Detailed tenant view with stats, health, and management options
 */

import React, { useState } from 'react';
import { useTenant } from '../../hooks/useAdmin';
import { TenantStatus } from '../../types/admin';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface TenantDetailProps {
  tenantId: string;
  onBack: () => void;
  onUpdate: (tenantId: string, updateData: any) => void;
  onDelete: (tenantId: string) => void;
}

export function TenantDetail({ tenantId, onBack, onUpdate, onDelete }: TenantDetailProps) {
  const { tenant, stats, health, loading, error } = useTenant(tenantId);
  const [activeTab, setActiveTab] = useState<'overview' | 'settings' | 'health'>('overview');

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !tenant) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <div className="text-red-500 mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Tenant</h3>
          <p className="text-gray-600 mb-4">{error || 'Tenant not found'}</p>
          <button
            onClick={onBack}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Back to List
          </button>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: TenantStatus) => {
    const baseClasses = 'px-3 py-1 text-sm font-medium rounded-full';
    
    switch (status) {
      case TenantStatus.ACTIVE:
        return `${baseClasses} bg-green-100 text-green-800`;
      case TenantStatus.SUSPENDED:
        return `${baseClasses} bg-red-100 text-red-800`;
      case TenantStatus.PENDING:
        return `${baseClasses} bg-yellow-100 text-yellow-800`;
      case TenantStatus.ARCHIVED:
        return `${baseClasses} bg-gray-100 text-gray-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatStorage = (mb: number) => {
    if (mb < 1024) return `${mb.toFixed(1)} MB`;
    const gb = mb / 1024;
    if (gb < 1024) return `${gb.toFixed(1)} GB`;
    const tb = gb / 1024;
    return `${tb.toFixed(1)} TB`;
  };

  const formatCost = (cost?: number) => {
    if (cost === undefined || cost === null) return 'N/A';
    return `$${cost.toFixed(2)}`;
  };

  const handleStatusToggle = () => {
    const newStatus = tenant.status === TenantStatus.ACTIVE 
      ? TenantStatus.SUSPENDED 
      : TenantStatus.ACTIVE;
    
    onUpdate(tenant.id, { status: newStatus });
  };

  const tabs = [
    { id: 'overview' as const, label: 'Overview', icon: '📊' },
    { id: 'settings' as const, label: 'Settings', icon: '⚙️' },
    { id: 'health' as const, label: 'Health', icon: '💚' },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <button
            onClick={onBack}
            className="mr-4 text-gray-600 hover:text-gray-900"
          >
            ← Back
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{tenant.name}</h2>
            <p className="text-gray-600">{tenant.domain}</p>
          </div>
        </div>
        <div className="flex items-center space-x-3">
          <span className={getStatusBadge(tenant.status)}>
            {tenant.status}
          </span>
          <button
            onClick={handleStatusToggle}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              tenant.status === TenantStatus.ACTIVE
                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
          >
            {tenant.status === TenantStatus.ACTIVE ? 'Suspend' : 'Activate'}
          </button>
          <button
            onClick={() => onDelete(tenant.id)}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm font-medium"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Basic Info */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Name</dt>
                <dd className="text-sm text-gray-900">{tenant.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Domain</dt>
                <dd className="text-sm text-gray-900">{tenant.domain}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Description</dt>
                <dd className="text-sm text-gray-900">{tenant.description || 'No description'}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Created</dt>
                <dd className="text-sm text-gray-900">{formatDate(tenant.created_at)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                <dd className="text-sm text-gray-900">{formatDate(tenant.updated_at)}</dd>
              </div>
            </div>
          </div>

          {/* Statistics */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                      👥
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Users</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.user_count}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                      📊
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Dashboards</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.dashboard_count}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-yellow-100 rounded-md flex items-center justify-center">
                      🚨
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Active Alerts</p>
                    <p className="text-2xl font-semibold text-gray-900">{stats.alert_count}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                      💾
                    </div>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Storage</p>
                    <p className="text-2xl font-semibold text-gray-900">{formatStorage(stats.storage_usage_mb)}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Cost Information */}
          {stats && (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Cost Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Monthly Cost</dt>
                  <dd className="text-lg font-semibold text-gray-900">{formatCost(stats.monthly_cost)}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Cost Trend</dt>
                  <dd className={`text-lg font-semibold ${
                    stats.cost_trend === 'up' ? 'text-red-600' : 
                    stats.cost_trend === 'down' ? 'text-green-600' : 'text-gray-900'
                  }`}>
                    {stats.cost_trend === 'up' ? '↗️ Increasing' : 
                     stats.cost_trend === 'down' ? '↘️ Decreasing' : '→ Stable'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Last Activity</dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {stats.last_activity ? formatDate(stats.last_activity) : 'No activity'}
                  </dd>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="space-y-6">
          {/* Tenant Settings */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Tenant Limits</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Max Users</dt>
                <dd className="text-sm text-gray-900">{tenant.settings.max_users}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Max Dashboards</dt>
                <dd className="text-sm text-gray-900">{tenant.settings.max_dashboards}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Max Alerts</dt>
                <dd className="text-sm text-gray-900">{tenant.settings.max_alerts}</dd>
              </div>
            </div>
          </div>

          {/* Feature Flags */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Enabled Features</h3>
            <div className="flex flex-wrap gap-2">
              {tenant.settings.features_enabled.map((feature) => (
                <span
                  key={feature}
                  className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full"
                >
                  {feature}
                </span>
              ))}
            </div>
          </div>

          {/* Data Retention */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Data Retention Policy</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Logs</dt>
                <dd className="text-sm text-gray-900">{tenant.retention_policy.logs_retention_days} days</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Metrics</dt>
                <dd className="text-sm text-gray-900">{tenant.retention_policy.metrics_retention_days} days</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Traces</dt>
                <dd className="text-sm text-gray-900">{tenant.retention_policy.traces_retention_days} days</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Alerts</dt>
                <dd className="text-sm text-gray-900">{tenant.retention_policy.alerts_retention_days} days</dd>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'health' && health && (
        <div className="space-y-6">
          {/* Overall Health */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">System Health</h3>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                health.status === 'healthy' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {health.status}
              </span>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Last checked: {formatDate(health.last_check)}
            </p>
          </div>

          {/* Service Health */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Service Status</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(health.services).map(([service, status]) => (
                <div key={service} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <span className="text-sm font-medium text-gray-900 capitalize">{service}</span>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    status === 'healthy' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Issues */}
          {health.issues.length > 0 && (
            <div className="bg-white border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-red-900 mb-4">Issues</h3>
              <ul className="space-y-2">
                {health.issues.map((issue, index) => (
                  <li key={index} className="text-sm text-red-700 flex items-center">
                    <span className="mr-2">⚠️</span>
                    {issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}