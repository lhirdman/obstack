import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import AuthPage from './components/auth/AuthPage';
import KeycloakCallback from './components/auth/KeycloakCallback';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Dashboard from './components/Dashboard';
import Navbar from './components/Navbar';
import { authService } from './services/auth';
import { configService } from './lib/config';

const queryClient = new QueryClient();

const AppContent: React.FC = () => {
  const [authInitialized, setAuthInitialized] = useState(false);
  const [authRefetchTrigger, setAuthRefetchTrigger] = useState(0);

  // Initialize auth service on app start
  useEffect(() => {
    const initAuth = async () => {
      try {
        await authService.init();
      } catch (error) {
        console.error('Failed to initialize auth service:', error);
      } finally {
        setAuthInitialized(true);
      }
    };

    initAuth();
  }, []);

  // Use React Query to check authentication status
  const { data: user, isLoading, isError } = useQuery({
    queryKey: ['auth', 'me', authRefetchTrigger],
    queryFn: () => authService.getCurrentUser(),
    retry: false, // Don't retry on auth failures
    staleTime: 5 * 60 * 1000, // Consider data fresh for 5 minutes
    enabled: authInitialized, // Only run query after auth is initialized
  });

  const isAuthenticated = !isError && !!user;
  const isKeycloakAuth = configService.getAuthMethod() === 'keycloak';

  const handleLoginSuccess = () => {
    // Trigger a refetch of the auth status
    setAuthRefetchTrigger(prev => prev + 1);
  };

  const handleLogout = () => {
    // Trigger a refetch to update auth status
    setAuthRefetchTrigger(prev => prev + 1);
  };

  if (!authInitialized || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        {/* Keycloak callback route */}
        <Route 
          path="/auth/callback" 
          element={
            <KeycloakCallback 
              onSuccess={handleLoginSuccess}
              onError={(error) => console.error('Keycloak callback error:', error)}
            />
          } 
        />
        
        {/* Main application routes */}
        <Route 
          path="/*" 
          element={
            isAuthenticated ? (
              <div className="min-h-screen bg-gray-50">
                <Navbar onLogout={handleLogout} />
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
            ) : (
              <AuthPage />
            )
          } 
        />
      </Routes>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
};

export default App;