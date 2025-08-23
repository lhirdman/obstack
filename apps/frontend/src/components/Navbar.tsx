import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { HomeIcon, ChartBarIcon, DocumentMagnifyingGlassIcon } from '@heroicons/react/24/outline';
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

  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Metrics', href: '/metrics', icon: ChartBarIcon },
    { name: 'Traces', href: '/traces', icon: DocumentMagnifyingGlassIcon },
  ];

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors">
              ObservaStack
            </Link>
            
            {/* Navigation Links */}
            <div className="hidden md:flex space-x-4">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="h-4 w-4 mr-2" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
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