import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { AuthProvider, LoginPage, ProtectedRoute, AdminRoute, defaultKeycloakConfig } from './auth'
import { ToastProvider, OfflineIndicator, ErrorBoundary } from './components/ui'
import App from './shell/App'
import Search from './views/Search'
import Alerts from './views/Alerts'
import Insights from './views/Insights'
import Dashboards from './views/Dashboards'
import { Admin } from './views/Admin'

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
    },
  },
})

// Create router with authentication
const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <App />
      </ProtectedRoute>
    ),
    children: [
      { path: '/', element: <Search /> },
      { path: '/search', element: <Search /> },
      { path: '/alerts', element: <Alerts /> },
      { path: '/insights', element: <Insights /> },
      { path: '/dashboards', element: <Dashboards /> },
      {
        path: '/admin',
        element: (
          <AdminRoute>
            <Admin />
          </AdminRoute>
        )
      }
    ]
  }
])

// Error handler for authentication errors
function handleAuthError(error: string) {
  console.error('Authentication error:', error)
  // Could show a toast notification or other user feedback here
}

const root = createRoot(document.getElementById('root')!)
root.render(
  <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <AuthProvider config={defaultKeycloakConfig} onAuthError={handleAuthError}>
        <ToastProvider>
          <RouterProvider router={router} />
          <OfflineIndicator showWhenOnline />
          <ReactQueryDevtools initialIsOpen={false} />
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  </ErrorBoundary>
)
