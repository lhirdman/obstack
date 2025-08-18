/**
 * System settings and configuration interface
 */

import React, { useState } from 'react';
import { useSystemSettings } from '../../hooks/useAdmin';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export function SystemSettings() {
  const { settings, loading, error, updateSettings } = useSystemSettings();
  const [activeTab, setActiveTab] = useState<'features' | 'global' | 'maintenance'>('features');

  const handleFeatureToggle = async (feature: string, enabled: boolean) => {
    if (!settings) return;
    
    try {
      await updateSettings({
        feature_flags: {
          ...settings.feature_flags,
          [feature]: enabled,
        },
      });
    } catch (error) {
      console.error('Failed to update feature flag:', error);
    }
  };

  const handleMaintenanceToggle = async () => {
    if (!settings) return;
    
    try {
      await updateSettings({
        maintenance_mode: !settings.maintenance_mode,
      });
    } catch (error) {
      console.error('Failed to toggle maintenance mode:', error);
    }
  };

  const tabs = [
    { id: 'features' as const, label: 'Feature Flags', icon: '🚩' },
    { id: 'global' as const, label: 'Global Settings', icon: '🌐' },
    { id: 'maintenance' as const, label: 'Maintenance', icon: '🔧' },
  ];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">System Settings</h2>
        <p className="text-gray-600">Configure global system settings and feature flags</p>
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

      {/* Tab Content */}
      {!loading && (
        <div>
          {activeTab === 'features' && (
            <div className="space-y-6">
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Feature Flags</h3>
                <div className="space-y-4">
                  {/* Placeholder feature flags */}
                  {[
                    { key: 'sso_enabled', label: 'Single Sign-On (SSO)', description: 'Enable SSO authentication' },
                    { key: 'cost_insights', label: 'Cost Insights', description: 'Enable cost analysis features' },
                    { key: 'advanced_search', label: 'Advanced Search', description: 'Enable advanced search capabilities' },
                    { key: 'api_access', label: 'API Access', description: 'Enable external API access' },
                  ].map((feature) => (
                    <div key={feature.key} className="flex items-center justify-between p-4 bg-gray-50 rounded-md">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">{feature.label}</h4>
                        <p className="text-sm text-gray-600">{feature.description}</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={settings?.feature_flags?.[feature.key] || false}
                          onChange={(e) => handleFeatureToggle(feature.key, e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'global' && (
            <div className="space-y-6">
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Global Configuration</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      System Name
                    </label>
                    <input
                      type="text"
                      defaultValue="ObservaStack"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Default Timezone
                    </label>
                    <select className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Europe/London">London</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Session Timeout (minutes)
                    </label>
                    <input
                      type="number"
                      defaultValue={60}
                      min={5}
                      max={480}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'maintenance' && (
            <div className="space-y-6">
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Maintenance Mode</h3>
                <div className="flex items-center justify-between p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                  <div>
                    <h4 className="text-sm font-medium text-yellow-900">System Maintenance</h4>
                    <p className="text-sm text-yellow-700">
                      Enable maintenance mode to prevent user access during system updates
                    </p>
                  </div>
                  <button
                    onClick={handleMaintenanceToggle}
                    className={`px-4 py-2 rounded-md text-sm font-medium ${
                      settings?.maintenance_mode
                        ? 'bg-red-600 text-white hover:bg-red-700'
                        : 'bg-yellow-600 text-white hover:bg-yellow-700'
                    }`}
                  >
                    {settings?.maintenance_mode ? 'Disable Maintenance' : 'Enable Maintenance'}
                  </button>
                </div>
              </div>

              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">System Notifications</h3>
                <div className="space-y-3">
                  {settings?.system_notifications?.map((notification, index) => (
                    <div key={index} className="p-3 bg-blue-50 border border-blue-200 rounded-md">
                      <p className="text-sm text-blue-800">{notification}</p>
                    </div>
                  )) || (
                    <p className="text-sm text-gray-500">No active system notifications</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}