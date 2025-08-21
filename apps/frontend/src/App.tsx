import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import AuthPage from './components/auth/AuthPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Dashboard from './components/Dashboard';
import Navbar from './components/Navbar';
import { authService } from './services/auth';

const App: React.FC = () => {
  const [authRefetchTrigger, setAuthRefetchTrigger] = useState(0);

  // Use React Query to check authentication status
  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['auth', 'me', authRefetchTrigger],
    queryFn: () => authService.getCurrentUser(),
    retry: false, // Don't retry on auth failures
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });

  const isAuthenticated = !isError && !!user;

  const handleLoginSuccess = () => {
    // Trigger a refetch of the auth status
    setAuthRefetchTrigger(prev => prev + 1);
  };

  const handleLogout = () => {
    // Trigger a refetch to update auth status
    setAuthRefetchTrigger(prev => prev + 1);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  import React from 'react';
import { useQuery } from '@tanstack/react-query';
import AuthPage from './components/auth/AuthPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Dashboard from './components/Dashboard';
import Navbar from './components/Navbar';
import { authService } from './services/auth';

const App: React.FC = () => {
  // Use React Query to check authentication status
  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: () => authService.getCurrentUser(),
    retry: false, // Don't retry on auth failures
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
  });

  const isAuthenticated = !isError && !!user;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <ProtectedRoute
        fallback={
          <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Verifying access...</p>
            </div>
          </div>
        }
      >
        <Dashboard />
      </ProtectedRoute>
    </div>
  );
};

export default App;