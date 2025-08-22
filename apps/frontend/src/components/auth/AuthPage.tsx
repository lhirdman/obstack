import React, { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import { configService } from '../../lib/config';

const queryClient = new QueryClient();

const AuthPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [isKeycloakAuth, setIsKeycloakAuth] = useState(false);

  useEffect(() => {
    const authMethod = configService.getAuthMethod();
    setIsKeycloakAuth(authMethod === 'keycloak');
  }, []);

  const handleLoginSuccess = () => {
    setMessage({ type: 'success', text: 'Login successful!' });
    // The App component will automatically update now
  };

  const handleLoginError = (error: string) => {
    setMessage({ type: 'error', text: error });
  };

  const handleRegisterSuccess = () => {
    setMessage({ type: 'success', text: 'Account created successfully! Please log in.' });
    setIsLogin(true);
  };

  const handleRegisterError = (error: string) => {
    setMessage({ type: 'error', text: error });
  };

  const switchMode = () => {
    setIsLogin(!isLogin);
    setMessage(null);
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              ObservaStack
            </h1>
            <p className="text-gray-600 mb-8">
              Unified Observability Platform
            </p>
          </div>

          {message && (
            <div className={`mb-4 p-3 rounded-md ${
              message.type === 'success' 
                ? 'bg-green-50 text-green-800 border border-green-200' 
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}>
              {message.text}
            </div>
          )}

          {isLogin ? (
            <LoginForm 
              onSuccess={handleLoginSuccess}
              onError={handleLoginError}
            />
          ) : (
            <RegisterForm 
              onSuccess={handleRegisterSuccess}
              onError={handleRegisterError}
            />
          )}

          {!isKeycloakAuth && (
            <div className="mt-6 text-center">
              <button
                onClick={switchMode}
                className="text-blue-600 hover:text-blue-500 text-sm font-medium"
              >
                {isLogin
                  ? "Don't have an account? Sign up"
                  : "Already have an account? Sign in"
                }
              </button>
            </div>
          )}
        </div>
      </div>
    </QueryClientProvider>
  );
};

export default AuthPage;