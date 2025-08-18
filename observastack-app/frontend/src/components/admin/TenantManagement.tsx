/**
 * Tenant management interface for administrators
 */

import React, { useState } from 'react';
import { useTenants } from '../../hooks/useAdmin';
import { TenantStatus, TenantFilters } from '../../types/admin';
import { TenantList } from './TenantList';
import { TenantForm } from './TenantForm';
import { TenantDetail } from './TenantDetail';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export function TenantManagement() {
  const [filters, setFilters] = useState<TenantFilters>({
    page: 1,
    page_size: 20,
  });
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<TenantStatus | ''>('');

  const { tenants, total, loading, error, loadTenants, createTenant, updateTenant, deleteTenant } = useTenants(filters);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setFilters(prev => ({
      ...prev,
      ...(query ? { search: query } : {}),
      page: 1,
    }));
  };

  const handleStatusFilter = (status: TenantStatus | '') => {
    setStatusFilter(status);
    setFilters(prev => ({
      ...prev,
      ...(status ? { status: status as TenantStatus } : {}),
      page: 1,
    }));
  };

  const handlePageChange = (page: number) => {
    setFilters(prev => ({ ...prev, page }));
  };

  const handleCreateTenant = async (tenantData: any) => {
    try {
      await createTenant(tenantData);
      setShowCreateForm(false);
    } catch (error) {
      // Error is handled by the hook
      console.error('Failed to create tenant:', error);
    }
  };

  const handleUpdateTenant = async (tenantId: string, updateData: any) => {
    try {
      await updateTenant(tenantId, updateData);
    } catch (error) {
      console.error('Failed to update tenant:', error);
    }
  };

  const handleDeleteTenant = async (tenantId: string) => {
    if (window.confirm('Are you sure you want to delete this tenant? This action cannot be undone.')) {
      try {
        await deleteTenant(tenantId);
        if (selectedTenantId === tenantId) {
          setSelectedTenantId(null);
        }
      } catch (error) {
        console.error('Failed to delete tenant:', error);
      }
    }
  };

  if (selectedTenantId) {
    return (
      <TenantDetail
        tenantId={selectedTenantId}
        onBack={() => setSelectedTenantId(null)}
        onUpdate={handleUpdateTenant}
        onDelete={handleDeleteTenant}
      />
    );
  }

  if (showCreateForm) {
    return (
      <TenantForm
        onSubmit={handleCreateTenant}
        onCancel={() => setShowCreateForm(false)}
        loading={loading}
      />
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Tenant Management</h2>
          <p className="text-gray-600">Manage tenant accounts and configurations</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Create Tenant
        </button>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search tenants..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <select
            value={statusFilter}
            onChange={(e) => handleStatusFilter(e.target.value as TenantStatus | '')}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value={TenantStatus.ACTIVE}>Active</option>
            <option value={TenantStatus.SUSPENDED}>Suspended</option>
            <option value={TenantStatus.PENDING}>Pending</option>
            <option value={TenantStatus.ARCHIVED}>Archived</option>
          </select>
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

      {/* Tenant List */}
      {!loading && (
        <TenantList
          tenants={tenants}
          total={total}
          currentPage={filters.page || 1}
          pageSize={filters.page_size || 20}
          onPageChange={handlePageChange}
          onTenantSelect={setSelectedTenantId}
          onTenantUpdate={handleUpdateTenant}
          onTenantDelete={handleDeleteTenant}
        />
      )}
    </div>
  );
}