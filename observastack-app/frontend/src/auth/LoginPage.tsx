/**
 * Login page component for Keycloak authentication
 */

import React, { useEffect } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

interface LocationState {
  from?: {
    pathname: string
    search: string
  }
}

export function LoginPage() {
  const { isAuthenticated, isLoading, login, error } = useAuth()
  const location = useLocation()
  const state = location.state as LocationState

  // Redirect to intended destination if already authenticated
  if (isAuthenticated) {
    const from = state?.from?.pathname + (state?.from?.search || '') || '/'
    return <Navigate to={from} replace />
  }

  // Auto-trigger login when component mounts
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      login().catch(console.error)
    }
  }, [isLoading, isAuthenticated, login])

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '48px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
        textAlign: 'center',
        maxWidth: '400px',
        width: '100%',
        margin: '24px'
      }}>
        {/* Logo */}
        <div style={{
          fontSize: '32px',
          fontWeight: 'bold',
          color: '#333',
          marginBottom: '8px'
        }}>
          ObservaStack
        </div>
        
        <div style={{
          fontSize: '14px',
          color: '#666',
          marginBottom: '32px'
        }}>
          Unified Observability Platform
        </div>

        {/* Loading State */}
        {isLoading && (
          <div style={{ marginBottom: '24px' }}>
            <div style={{
              width: '40px',
              height: '40px',
              border: '4px solid #f3f3f3',
              borderTop: '4px solid #667eea',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 16px'
            }} />
            <div style={{ color: '#666', fontSize: '14px' }}>
              Redirecting to login...
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div style={{
            background: '#fee',
            border: '1px solid #fcc',
            borderRadius: '6px',
            padding: '12px',
            marginBottom: '24px',
            color: '#c33',
            fontSize: '14px'
          }}>
            <strong>Authentication Error:</strong><br />
            {error}
          </div>
        )}

        {/* Manual Login Button */}
        {!isLoading && (
          <button
            onClick={login}
            style={{
              width: '100%',
              padding: '12px 24px',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.background = '#5a6fd8'
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.background = '#667eea'
            }}
          >
            Sign In with Keycloak
          </button>
        )}

        {/* Help Text */}
        <div style={{
          fontSize: '12px',
          color: '#888',
          marginTop: '24px',
          lineHeight: '1.4'
        }}>
          You will be redirected to the Keycloak authentication server.
          Please use your organization credentials to sign in.
        </div>

        {/* Intended Destination */}
        {state?.from && (
          <div style={{
            fontSize: '12px',
            color: '#666',
            marginTop: '16px',
            padding: '8px',
            background: '#f8f9fa',
            borderRadius: '4px'
          }}>
            After login, you'll be redirected to: <code>{state.from.pathname}</code>
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}