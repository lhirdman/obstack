/**
 * Tenant creation and editing form
 */

import React, { useState } from 'react';
import { TenantCreate, TenantSettings, DataRetentionPolicy } from '../../types/admin';
import { LoadingSpinner } from '../ui/LoadingSpinner';

interface TenantFormProps {
  tenant?: any; // For editing existing tenant
  onSubmit: (data: TenantCreate) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

export function TenantForm({ tenant, onSubmit, onCancel, loading = false }: TenantFormProps) {
  const [formData, setFormData] = useState<TenantCreate>({
    name: tenant?.name || '',
    domain: tenant?.domain || '',
    description: tenant?.description || '',
    admin_email: tenant?.admin_email || '',
    admin_username: tenant?.admin_username || '',
    settings: {
      max_users: tenant?.settings?.max_users || 10,
      max_dashboards: tenant?.settings?.max_dashboards || 50,
      max_alerts: tenant?.settings?.max_alerts || 100,
      features_enabled: tenant?.settings?.features_enabled || ['search', 'alerts', 'insights'],
      custom_branding: tenant?.settings?.custom_branding || {},
      notification_settings: tenant?.settings?.notification_settings || {},
      cost_budget_monthly: tenant?.settings?.cost_budget_monthly || undefined,
      cost_alert_threshold: tenant?.settings?.cost_alert_threshold || 0.8,
    },
    retention_policy: {
      logs_retention_days: tenant?.retention_policy?.logs_retention_days || 30,
      metrics_retention_days: tenant?.retention_policy?.metrics_retention_days || 90,
      traces_retention_days: tenant?.retention_policy?.traces_retention_days || 14,
      alerts_retention_days: tenant?.retention_policy?.alerts_retention_days || 365,
      cost_data_retention_days: tenant?.retention_policy?.cost_data_retention_days || 730,
    },
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState<'basic' | 'settings' | 'retention'>('basic');

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Tenant name is required';
    }

    if (!formData.domain.trim()) {
      newErrors.domain = 'Domain is required';
    } else if (!/^[a-z0-9-_]+$/.test(formData.domain)) {
      newErrors.domain = 'Domain must contain only lowercase letters, numbers, hyphens, and underscores';
    }

    if (!formData.admin_email.trim()) {
      newErrors.admin_email = 'Admin email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.admin_email)) {
      newErrors.admin_email = 'Invalid email format';
    }

    if (!formData.admin_username.trim()) {
      newErrors.admin_username = 'Admin username is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const handleSettingsChange = (field: keyof TenantSettings, value: any) => {
    setFormData(prev => ({
      ...prev,
      settings: {
        ...prev.settings!,
        [field]: value,
      },
    }));
  };

  const handleRetentionChange = (field: keyof DataRetentionPolicy, value: number) => {
    setFormData(prev => ({
      ...prev,
      retention_policy: {
        ...prev.retention_policy!,
        [field]: value,
      },
    }));
  };

  const handleFeatureToggle = (feature: string) => {
    const currentFeatures = formData.settings?.features_enabled || [];
    const newFeatures = currentFeatures.includes(feature)
      ? currentFeatures.filter(f => f !== feature)
      : [...currentFeatures, feature];
    
    handleSettingsChange('features_enabled', newFeatures);
  };

  const availableFeatures = [
    { id: 'search', label: 'Unified Search' },
    { id: 'alerts', label: 'Alert Management' },
    { id: 'insights', label: 'Cost Insights' },
    { id: 'dashboards', label: 'Custom Dashboards' },
    { id: 'api_access', label: 'API Access' },
  ];

  const tabs = [
    { id: 'basic' as const, label: 'Basic Info' },
    { id: 'settings' as const, label: 'Settings' },
    { id: 'retention' as const, label: 'Data Retention' },
  ];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">
          {tenant ? 'Edit Tenant' : 'Create New Tenant'}
        </h2>
        <p className="text-gray-600">
          {tenant ? 'Update tenant configuration' : 'Set up a new tenant account'}
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Basic Info Tab */}
        {activeTab === 'basic' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tenant Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.name ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Enter tenant name"
                />
                {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Domain *
                </label>
                <input
                  type="text"
                  value={formData.domain}
                  onChange={(e) => handleInputChange('domain', e.target.value.toLowerCase())}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.domain ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="tenant-domain"
                />
                {errors.domain && <p className="mt-1 text-sm text-red-600">{errors.domain}</p>}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Optional description"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Admin Email *
                </label>
                <input
                  type="email"
                  value={formData.admin_email}
                  onChange={(e) => handleInputChange('admin_email', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.admin_email ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="admin@example.com"
                />
                {errors.admin_email && <p className="mt-1 text-sm text-red-600">{errors.admin_email}</p>}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Admin Username *
                </label>
                <input
                  type="text"
                  value={formData.admin_username}
                  onChange={(e) => handleInputChange('admin_username', e.target.value)}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    errors.admin_username ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="admin"
                />
                {errors.admin_username && <p className="mt-1 text-sm text-red-600">{errors.admin_username}</p>}
              </div>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Users
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={formData.settings?.max_users}
                  onChange={(e) => handleSettingsChange('max_users', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Dashboards
                </label>
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={formData.settings?.max_dashboards}
                  onChange={(e) => handleSettingsChange('max_dashboards', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Alerts
                </label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={formData.settings?.max_alerts}
                  onChange={(e) => handleSettingsChange('max_alerts', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Monthly Budget (USD)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.settings?.cost_budget_monthly || ''}
                  onChange={(e) => handleSettingsChange('cost_budget_monthly', e.target.value ? parseFloat(e.target.value) : undefined)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Optional"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cost Alert Threshold
                </label>
                <select
                  value={formData.settings?.cost_alert_threshold}
                  onChange={(e) => handleSettingsChange('cost_alert_threshold', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={0.5}>50%</option>
                  <option value={0.7}>70%</option>
                  <option value={0.8}>80%</option>
                  <option value={0.9}>90%</option>
                  <option value={0.95}>95%</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Enabled Features
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {availableFeatures.map((feature) => (
                  <label key={feature.id} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.settings?.features_enabled?.includes(feature.id) || false}
                      onChange={() => handleFeatureToggle(feature.id)}
                      className="mr-2 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm text-gray-700">{feature.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Data Retention Tab */}
        {activeTab === 'retention' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Logs Retention (days)
                </label>
                <input
                  type="number"
                  min="1"
                  max="3650"
                  value={formData.retention_policy?.logs_retention_days}
                  onChange={(e) => handleRetentionChange('logs_retention_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Metrics Retention (days)
                </label>
                <input
                  type="number"
                  min="1"
                  max="3650"
                  value={formData.retention_policy?.metrics_retention_days}
                  onChange={(e) => handleRetentionChange('metrics_retention_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Traces Retention (days)
                </label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={formData.retention_policy?.traces_retention_days}
                  onChange={(e) => handleRetentionChange('traces_retention_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Alerts Retention (days)
                </label>
                <input
                  type="number"
                  min="1"
                  max="3650"
                  value={formData.retention_policy?.alerts_retention_days}
                  onChange={(e) => handleRetentionChange('alerts_retention_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cost Data Retention (days)
                </label>
                <input
                  type="number"
                  min="1"
                  max="3650"
                  value={formData.retention_policy?.cost_data_retention_days}
                  onChange={(e) => handleRetentionChange('cost_data_retention_days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200 mt-8">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {loading && <LoadingSpinner size="sm" className="mr-2" />}
            {tenant ? 'Update Tenant' : 'Create Tenant'}
          </button>
        </div>
      </form>
    </div>
  );
}