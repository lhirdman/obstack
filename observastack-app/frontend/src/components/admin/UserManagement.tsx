/**
 * User management interface for administrators
 */

import React, { useState } from 'react';
import { useUsers } from '../../hooks/useAdmin';
import { LoadingSpinner } from '../ui/LoadingSpinner';

export function UserManagement() {
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 20,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [tenantFilter, setTenantFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const { users, total, loading, error, loadUsers, manageUser } = useUsers(filters);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setFilters(prev => ({
      ...prev,
      search: query || undefined,
      page: 1,
    }));
  };

  const handleUserAction = async (userId: string, action: string) => {
    try {
      await manageUser(userId, { user_id: userId, action });
    } catch (error) {
      console.error('Failed to manage user:', error);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
          <p className="text-gray-600">Manage user accounts and permissions</p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
          Invite User
        </button>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <select
            value={tenantFilter}
            onChange={(e) => setTenantFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Tenants</option>
            {/* Would be populated with actual tenant options */}
          </select>
        </div>
        <div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Roles</option>
            <option value="admin">Admin</option>
            <option value="user">User</option>
            <option value="viewer">Viewer</option>
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

      {/* Placeholder Content */}
      {!loading && (
        <div className="bg-white border border-gray-200 rounded-lg p-8 text-center">
          <div className="text-gray-500">
            <div className="text-4xl mb-4">👥</div>
            <h3 className="text-lg font-medium mb-2">User Management</h3>
            <p>User management functionality will be implemented here.</p>
            <p className="text-sm mt-2">This includes user creation, role assignment, and account management.</p>
          </div>
        </div>
      )}
    </div>
  );
}