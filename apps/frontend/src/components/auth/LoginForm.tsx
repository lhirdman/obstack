import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { authService, LoginRequest } from '../../services/auth';
import { configService } from '../../lib/config';

interface LoginFormProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onError }) => {
  const [formData, setFormData] = useState<LoginRequest>({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isKeycloakAuth, setIsKeycloakAuth] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const queryClient = useQueryClient();

  useEffect(() => {
    const initAuth = async () => {
      const authMethod = configService.getAuthMethod();
      setIsKeycloakAuth(authMethod === 'keycloak');
      
      if (authMethod === 'keycloak') {
        try {
          // Initialize Keycloak and check if already authenticated
          const authenticated = await authService.init();
          if (authenticated) {
            onSuccess?.();
            return;
          }
        } catch (error) {
          console.error('Failed to initialize Keycloak:', error);
          onError?.('Failed to initialize authentication system');
        }
      }
      
      setIsInitializing(false);
    };

    initAuth();
  }, [onSuccess, onError]);

  const loginMutation = useMutation({
    mutationFn: async (data?: LoginRequest | null) => {
      if (isKeycloakAuth) {
        // For Keycloak, this will redirect to Keycloak login
        await authService.login();
        return null; // No return value as this redirects
      } else {
        // Local authentication
        if (!data) {
          throw new Error('Credentials required for local authentication');
        }
        return authService.login(data);
      }
    },
    onSuccess: (data) => {
      if (!isKeycloakAuth) {
        // Only invalidate queries for local auth, Keycloak handles redirect
        queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
        onSuccess?.();
      }
    },
    onError: (error: Error) => {
      onError?.(error.message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isKeycloakAuth) {
      // For Keycloak, no form data needed
      loginMutation.mutate(null);
    } else {
      // For local auth, use form data
      loginMutation.mutate(formData);
    }
  };

  const handleKeycloakLogin = () => {
    loginMutation.mutate(null);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  if (isInitializing) {
    return (
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
        Sign In
      </h2>
      
      {isKeycloakAuth ? (
        // Keycloak authentication UI
        <div className="space-y-4">
          <div className="text-center text-gray-600 mb-4">
            <p>Sign in with your corporate credentials</p>
          </div>
          
          {loginMutation.error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
              {loginMutation.error.message}
            </div>
          )}

          <button
            onClick={handleKeycloakLogin}
            disabled={loginMutation.isPending}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
          >
            {loginMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Redirecting...
              </>
            ) : (
              'Sign In with SSO'
            )}
          </button>
        </div>
      ) : (
        // Local authentication form
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your password"
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? (
                  <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                ) : (
                  <EyeIcon className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
          </div>

          {loginMutation.error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
              {loginMutation.error.message}
            </div>
          )}

          <button
            type="submit"
            disabled={loginMutation.isPending}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loginMutation.isPending ? 'Signing In...' : 'Sign In'}
          </button>
        </form>
      )}
    </div>
  );
};

export default LoginForm;