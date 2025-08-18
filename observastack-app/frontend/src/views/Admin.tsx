/**
 * Admin dashboard view for system configuration and tenant management
 */

import React, { useState } from 'react';
import { Container } from '../components/layout/Container';
import { TenantManagement } from '../components/admin/TenantManagement';
import { UserManagement } from '../components/admin/UserManagement';
import { SystemSettings } from '../components/admin/SystemSettings';
import { AuditLogs } from '../components/admin/AuditLogs';
import { SystemHealth } from '../components/admin/SystemHealth';

type AdminTab = 'tenants' | 'users' | 'settings' | 'audit' | 'health';

export function Admin() {
  const [activeTab, setActiveTab] = useState<AdminTab>('tenants');

  const tabs = [
    { id: 'tenants' as AdminTab, label: 'Tenant Management', icon: '🏢' },
    { id: 'users' as AdminTab, label: 'User Management', icon: '👥' },
    { id: 'settings' as AdminTab, label: 'System Settings', icon: '⚙️' },
    { id: 'audit' as AdminTab, label: 'Audit Logs', icon: '📋' },
    { id: 'health' as AdminTab, label: 'System Health', icon: '💚' },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'tenants':
        return <TenantManagement />;
      case 'users':
        return <UserManagement />;
      case 'settings':
        return <SystemSettings />;
      case 'audit':
        return <AuditLogs />;
      case 'health':
        return <SystemHealth />;
      default:
        return <TenantManagement />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Container>
        <div className="py-6">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">System Administration</h1>
            <p className="mt-2 text-gray-600">
              Manage tenants, users, and system configuration
            </p>
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center py-2 px-1 border-b-2 font-medium text-sm
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="bg-white rounded-lg shadow">
            {renderTabContent()}
          </div>
        </div>
      </Container>
    </div>
  );
}