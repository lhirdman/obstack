import React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '../services/auth';

interface NavbarProps {
  onLogout?: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ onLogout }) => {
  const queryClient = useQueryClient();

  const logoutMutation = useMutation({
    mutationFn: () => authService.logout(),
    onSuccess: () => {
      // Clear all cached queries
      queryClient.clear();
      onLogout?.();
    },
    onError: (error) => {
      console.error('Logout failed:', error);
      // Even if logout API fails, clear cache and trigger logout
      queryClient.clear();
      onLogout?.();
    },
  });

  const handleLogout = () => {
    logoutMutation.mutate();
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-semibold text-gray-900">
              ObservaStack
            </h1>
          </div>
          <div className="flex items-center">
            <button
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
              className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {logoutMutation.isPending ? 'Logging out...' : 'Logout'}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;