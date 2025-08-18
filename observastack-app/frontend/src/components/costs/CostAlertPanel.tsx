/**
 * Cost alert management panel component
 */

import React, { useState } from 'react';
import type { CostAlert, CostAlertType } from '../../types/costs';

interface CostAlertPanelProps {
  alerts: CostAlert[];
  loading?: boolean;
  onResolveAlert?: (alertId: string) => Promise<void>;
  onCreateAlert?: (alert: Omit<CostAlert, 'id' | 'createdAt' | 'tenantId'>) => Promise<void>;
  className?: string;
}

export function CostAlertPanel({
  alerts,
  loading = false,
  onResolveAlert,
  onCreateAlert,
  className = ''
}: CostAlertPanelProps) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterType, setFilterType] = useState<CostAlertType | 'all'>('all');

  const filteredAlerts = alerts.filter(alert => {
    const severityMatch = filterSeverity === 'all' || alert.severity === filterSeverity;
    const typeMatch = filterType === 'all' || alert.type === filterType;
    return severityMatch && typeMatch;
  });

  const activeAlerts = filteredAlerts.filter(alert => !alert.resolvedAt);
  const resolvedAlerts = filteredAlerts.filter(alert => alert.resolvedAt);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="border rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Cost Alerts</h3>
          <p className="text-sm text-gray-600">
            {activeAlerts.length} active alerts • {resolvedAlerts.length} resolved
          </p>
        </div>
        {onCreateAlert && (
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
          >
            Create Alert
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Severity:</label>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Type:</label>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as CostAlertType | 'all')}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Types</option>
            <option value="budget_exceeded">Budget Exceeded</option>
            <option value="anomaly_detected">Anomaly Detected</option>
            <option value="efficiency_low">Low Efficiency</option>
            <option value="waste_detected">Waste Detected</option>
            <option value="threshold_breach">Threshold Breach</option>
          </select>
        </div>
      </div>

      {/* Active alerts */}
      {activeAlerts.length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-medium text-gray-900 mb-3">Active Alerts</h4>
          <div className="space-y-3">
            {activeAlerts.map(alert => (
              <AlertCard
                key={alert.id}
                alert={alert}
                onResolve={onResolveAlert}
              />
            ))}
          </div>
        </div>
      )}

      {/* Resolved alerts */}
      {resolvedAlerts.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-3">Resolved Alerts</h4>
          <div className="space-y-3">
            {resolvedAlerts.map(alert => (
              <AlertCard
                key={alert.id}
                alert={alert}
                isResolved
              />
            ))}
          </div>
        </div>
      )}

      {filteredAlerts.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No cost alerts found
        </div>
      )}

      {/* Create alert modal */}
      {showCreateForm && onCreateAlert && (
        <CreateAlertModal
          onClose={() => setShowCreateForm(false)}
          onCreate={onCreateAlert}
        />
      )}
    </div>
  );
}

interface AlertCardProps {
  alert: CostAlert;
  onResolve?: (alertId: string) => Promise<void>;
  isResolved?: boolean;
}

function AlertCard({ alert, onResolve, isResolved = false }: AlertCardProps) {
  const [resolving, setResolving] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTypeLabel = (type: CostAlertType) => {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const handleResolve = async () => {
    if (!onResolve) return;
    
    setResolving(true);
    try {
      await onResolve(alert.id);
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className={`border rounded-lg p-4 ${isResolved ? 'bg-gray-50 opacity-75' : 'bg-white'}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityColor(alert.severity)}`}>
              {alert.severity.toUpperCase()}
            </span>
            <span className="text-sm text-gray-600">
              {getTypeLabel(alert.type)}
            </span>
            {isResolved && (
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800 border border-green-200">
                RESOLVED
              </span>
            )}
          </div>
          
          <h4 className="text-md font-medium text-gray-900 mb-1">
            {alert.title}
          </h4>
          
          <p className="text-sm text-gray-600 mb-2">
            {alert.description}
          </p>
          
          <div className="flex items-center space-x-4 text-sm text-gray-500 mb-3">
            <span>{alert.cluster} • {alert.namespace}</span>
            {alert.workload && <span>• {alert.workload}</span>}
            <span>• ${alert.currentValue.toFixed(2)} / ${alert.threshold.toFixed(2)}</span>
          </div>

          {alert.recommendations.length > 0 && (
            <div className="mb-3">
              <span className="text-sm font-medium text-gray-700">Recommendations:</span>
              <ul className="mt-1 text-sm text-gray-600 list-disc list-inside">
                {alert.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="text-xs text-gray-500">
            Created: {new Date(alert.createdAt).toLocaleString()}
            {alert.resolvedAt && (
              <span> • Resolved: {new Date(alert.resolvedAt).toLocaleString()}</span>
            )}
          </div>
        </div>
        
        {!isResolved && onResolve && (
          <button
            onClick={handleResolve}
            disabled={resolving}
            className="ml-4 px-3 py-1 text-sm font-medium text-green-700 bg-green-100 rounded-md hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {resolving ? 'Resolving...' : 'Resolve'}
          </button>
        )}
      </div>
    </div>
  );
}

interface CreateAlertModalProps {
  onClose: () => void;
  onCreate: (alert: Omit<CostAlert, 'id' | 'createdAt' | 'tenantId'>) => Promise<void>;
}

function CreateAlertModal({ onClose, onCreate }: CreateAlertModalProps) {
  const [formData, setFormData] = useState({
    type: 'threshold_breach' as CostAlertType,
    severity: 'medium' as const,
    title: '',
    description: '',
    threshold: 100,
    namespace: '',
    workload: '',
    cluster: '',
    recommendations: ['']
  });
  const [creating, setCreating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setCreating(true);
    try {
      await onCreate({
        ...formData,
        currentValue: 0, // Will be set by the backend
        recommendations: formData.recommendations.filter(r => r.trim()),
        actionUrl: undefined,
        resolvedAt: undefined,
        metadata: {}
      });
      onClose();
    } catch (error) {
      console.error('Failed to create alert:', error);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Create Cost Alert</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Alert Type
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as CostAlertType }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="threshold_breach">Threshold Breach</option>
              <option value="budget_exceeded">Budget Exceeded</option>
              <option value="anomaly_detected">Anomaly Detected</option>
              <option value="efficiency_low">Low Efficiency</option>
              <option value="waste_detected">Waste Detected</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Severity
            </label>
            <select
              value={formData.severity}
              onChange={(e) => setFormData(prev => ({ ...prev, severity: e.target.value as any }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Cluster
              </label>
              <input
                type="text"
                value={formData.cluster}
                onChange={(e) => setFormData(prev => ({ ...prev, cluster: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Threshold ($)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.threshold}
                onChange={(e) => setFormData(prev => ({ ...prev, threshold: parseFloat(e.target.value) }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Namespace
              </label>
              <input
                type="text"
                value={formData.namespace}
                onChange={(e) => setFormData(prev => ({ ...prev, namespace: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Workload (optional)
              </label>
              <input
                type="text"
                value={formData.workload}
                onChange={(e) => setFormData(prev => ({ ...prev, workload: e.target.value }))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creating}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {creating ? 'Creating...' : 'Create Alert'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}