/**
 * Tenant list component with pagination and actions
 */

import React from 'react';
import { Tenant, TenantStatus } from '../../types/admin';

interface TenantListProps {
  tenants: Tenant[];
  total: number;
  currentPage: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onTenantSelect: (tenantId: string) => void;
  onTenantUpdate: (tenantId: string, updateData: any) => void;
  onTenantDelete: (tenantId: string) => void;
}

export function TenantList({
  tenants,
  total,
  currentPage,
  pageSize,
  onPageChange,
  onTenantSelect,
  onTenantUpdate,
  onTenantDelete,
}: TenantListProps) {
  const totalPages = Math.ceil(total / pageSize);

  const getStatusBadge = (status: TenantStatus) => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full';
    
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
    return new Date(dateString).toLocaleDateString();
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

  const handleStatusToggle = (tenant: Tenant) => {
    const newStatus = tenant.status === TenantStatus.ACTIVE 
      ? TenantStatus.SUSPENDED 
      : TenantStatus.ACTIVE;
    
    onTenantUpdate(tenant.id, { status: newStatus });
  };

  return (
    <div>
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Tenant
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Users
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Storage
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Monthly Cost
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tenants.map((tenant) => (
              <tr key={tenant.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {tenant.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {tenant.domain}
                    </div>
                    {tenant.description && (
                      <div className="text-xs text-gray-400 mt-1">
                        {tenant.description}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={getStatusBadge(tenant.status)}>
                    {tenant.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {tenant.user_count}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatStorage(tenant.storage_usage_mb)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatCost(tenant.monthly_cost)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(tenant.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex justify-end space-x-2">
                    <button
                      onClick={() => onTenantSelect(tenant.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleStatusToggle(tenant)}
                      className={`${
                        tenant.status === TenantStatus.ACTIVE
                          ? 'text-red-600 hover:text-red-900'
                          : 'text-green-600 hover:text-green-900'
                      }`}
                    >
                      {tenant.status === TenantStatus.ACTIVE ? 'Suspend' : 'Activate'}
                    </button>
                    <button
                      onClick={() => onTenantDelete(tenant.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty State */}
      {tenants.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500">
            <div className="text-4xl mb-4">🏢</div>
            <h3 className="text-lg font-medium mb-2">No tenants found</h3>
            <p>Create your first tenant to get started.</p>
          </div>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 mt-4">
          <div className="flex flex-1 justify-between sm:hidden">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
              className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Showing{' '}
                <span className="font-medium">
                  {(currentPage - 1) * pageSize + 1}
                </span>{' '}
                to{' '}
                <span className="font-medium">
                  {Math.min(currentPage * pageSize, total)}
                </span>{' '}
                of <span className="font-medium">{total}</span> results
              </p>
            </div>
            <div>
              <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm">
                <button
                  onClick={() => onPageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Previous</span>
                  ←
                </button>
                
                {/* Page Numbers */}
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const pageNum = Math.max(1, Math.min(totalPages - 4, currentPage - 2)) + i;
                  if (pageNum > totalPages) return null;
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => onPageChange(pageNum)}
                      className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                        pageNum === currentPage
                          ? 'z-10 bg-blue-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                          : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
                
                <button
                  onClick={() => onPageChange(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                  className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Next</span>
                  →
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}