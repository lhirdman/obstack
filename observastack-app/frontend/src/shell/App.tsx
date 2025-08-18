import React from 'react'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { 
  MagnifyingGlassIcon, 
  ExclamationTriangleIcon, 
  ChartBarIcon, 
  PresentationChartBarIcon,
  Cog6ToothIcon,
  UserIcon
} from '@heroicons/react/24/outline'
import { useAuth, ConditionalRender, getUserDisplayName } from '../auth'
import { 
  ResponsiveLayout, 
  Sidebar, 
  SidebarHeader, 
  SidebarNav, 
  SidebarNavItem,
  Container,
  TouchFriendlyButton
} from '../components/layout'

export default function App() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const isActive = (path: string) => {
    return location.pathname === path || (path === '/search' && location.pathname === '/')
  }

  const sidebarContent = (
    <Sidebar>
      <SidebarHeader title="ObservaStack" />
      
      <SidebarNav>
        <SidebarNavItem
          href="/search"
          icon={<MagnifyingGlassIcon className="w-5 h-5" />}
          active={isActive('/search')}
        >
          Search
        </SidebarNavItem>
        
        <SidebarNavItem
          href="/alerts"
          icon={<ExclamationTriangleIcon className="w-5 h-5" />}
          active={isActive('/alerts')}
        >
          Alerts
        </SidebarNavItem>
        
        <SidebarNavItem
          href="/insights"
          icon={<ChartBarIcon className="w-5 h-5" />}
          active={isActive('/insights')}
        >
          Insights
        </SidebarNavItem>
        
        <SidebarNavItem
          href="/dashboards"
          icon={<PresentationChartBarIcon className="w-5 h-5" />}
          active={isActive('/dashboards')}
        >
          Dashboards
        </SidebarNavItem>
        
        <ConditionalRender roles={['admin', 'tenant-admin']}>
          <SidebarNavItem
            href="/admin"
            icon={<Cog6ToothIcon className="w-5 h-5" />}
            active={isActive('/admin')}
          >
            Admin
          </SidebarNavItem>
        </ConditionalRender>
      </SidebarNav>

      {/* User Info */}
      {user && (
        <div className="mt-auto pt-4 border-t border-gray-200">
          <div className="flex items-center mb-3">
            <UserIcon className="w-5 h-5 text-gray-400 mr-2" />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-gray-900 truncate">
                {getUserDisplayName(user)}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {user.tenantId}
              </p>
            </div>
          </div>
          
          <div className="mb-3">
            <p className="text-xs text-gray-500">
              Roles: {user.roles.map(r => r.name).join(', ')}
            </p>
          </div>
          
          <TouchFriendlyButton
            variant="secondary"
            size="sm"
            onClick={logout}
            className="w-full"
          >
            Logout
          </TouchFriendlyButton>
          
          {/* Debug Info */}
          <div className="mt-2 text-xs text-gray-400">
            Route: {location.pathname}
          </div>
        </div>
      )}
    </Sidebar>
  )

  return (
    <ResponsiveLayout sidebar={sidebarContent}>
      <Container size="full" padding="md" className="py-4 sm:py-6 lg:py-8">
        <Outlet />
      </Container>
    </ResponsiveLayout>
  )
}
