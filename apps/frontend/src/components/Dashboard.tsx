import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { authService } from '../services/auth';

const Dashboard: React.FC = () => {
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => authService.getCurrentUser(),
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Welcome to ObservaStack, {user?.username}!
              </h2>
              <p className="text-gray-600 mb-2">
                You are successfully authenticated and accessing a protected route.
              </p>
              <p className="text-sm text-gray-500">
                Tenant: {user?.tenant_id} | Roles: {user?.roles?.join(', ') || 'None'}
              </p>
              <p className="text-sm text-gray-400 mt-4">
                The observability dashboard will be implemented in future stories.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;