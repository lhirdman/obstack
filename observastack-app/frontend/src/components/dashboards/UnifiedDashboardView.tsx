/**
 * Unified dashboard view combining browser and embedded dashboard
 */

import React, { useState, useEffect } from 'react';
import { DashboardBrowser } from './DashboardBrowser';
import { EmbeddedDashboard } from './EmbeddedDashboard';
import { DashboardInfo } from '../../services/grafana-service';

export interface UnifiedDashboardViewProps {
  initialDashboardUid?: string;
  showSidebar?: boolean;
  theme?: 'light' | 'dark';
  className?: string;
}

export function UnifiedDashboardView({
  initialDashboardUid,
  showSidebar = true,
  theme = 'light',
  className = ''
}: UnifiedDashboardViewProps) {
  const [selectedDashboard, setSelectedDashboard] = useState<DashboardInfo | null>(null);
  const [sidebarVisible, setSidebarVisible] = useState(showSidebar);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Set initial dashboard if provided
  useEffect(() => {
    if (initialDashboardUid && !selectedDashboard) {
      // Create a minimal dashboard info for initial load
      setSelectedDashboard({
        uid: initialDashboardUid,
        title: `Dashboard ${initialDashboardUid}`,
        tags: [],
        url: `/d/${initialDashboardUid}`
      });
    }
  }, [initialDashboardUid, selectedDashboard]);

  const handleDashboardSelect = (dashboard: DashboardInfo) => {
    setSelectedDashboard(dashboard);
    
    // Auto-hide sidebar on mobile when dashboard is selected
    if (window.innerWidth < 768) {
      setSidebarVisible(false);
    }
  };

  const handleNavigateBack = () => {
    setSelectedDashboard(null);
    setSidebarVisible(true);
  };

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    setSidebarVisible(!isFullscreen); // Hide sidebar in fullscreen
  };

  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  return (
    <div className={`unified-dashboard-view ${theme} ${isFullscreen ? 'fullscreen' : ''} ${className}`}>
      {/* Mobile header */}
      <div className="mobile-header">
        <button
          className="sidebar-toggle"
          onClick={toggleSidebar}
          title={sidebarVisible ? 'Hide sidebar' : 'Show sidebar'}
        >
          ☰
        </button>
        
        <h1 className="view-title">
          {selectedDashboard ? selectedDashboard.title : 'Dashboards'}
        </h1>

        {selectedDashboard && (
          <button
            className="fullscreen-toggle"
            onClick={handleFullscreen}
            title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
          >
            {isFullscreen ? '⤓' : '⤢'}
          </button>
        )}
      </div>

      <div className="dashboard-layout">
        {/* Sidebar */}
        <div className={`dashboard-sidebar ${sidebarVisible ? 'visible' : 'hidden'}`}>
          <div className="sidebar-header">
            <h2>Dashboard Browser</h2>
            <button
              className="sidebar-close"
              onClick={() => setSidebarVisible(false)}
              title="Close sidebar"
            >
              ×
            </button>
          </div>

          <DashboardBrowser
            onDashboardSelect={handleDashboardSelect}
            selectedDashboardUid={selectedDashboard?.uid}
            showCostDashboards={true}
            showObservabilityDashboards={true}
            className="sidebar-browser"
          />
        </div>

        {/* Main content */}
        <div className="dashboard-main">
          {selectedDashboard ? (
            <EmbeddedDashboard
              dashboardUid={selectedDashboard.uid}
              title={selectedDashboard.title}
              theme={theme}
              height={isFullscreen ? window.innerHeight - 60 : 600}
              showNavigation={!isFullscreen}
              onNavigateBack={handleNavigateBack}
              onFullscreen={handleFullscreen}
              className="main-dashboard"
            />
          ) : (
            <DashboardWelcome
              onShowBrowser={() => setSidebarVisible(true)}
              theme={theme}
            />
          )}
        </div>
      </div>

      {/* Sidebar overlay for mobile */}
      {sidebarVisible && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarVisible(false)}
        />
      )}
    </div>
  );
}

interface DashboardWelcomeProps {
  onShowBrowser: () => void;
  theme: 'light' | 'dark';
}

function DashboardWelcome({ onShowBrowser, theme }: DashboardWelcomeProps) {
  return (
    <div className={`dashboard-welcome ${theme}`}>
      <div className="welcome-content">
        <div className="welcome-icon">📊</div>
        
        <h2>Welcome to ObservaStack Dashboards</h2>
        
        <p>
          Access all your observability and cost monitoring dashboards in one unified interface.
          Browse through organized categories or search for specific dashboards.
        </p>

        <div className="welcome-features">
          <div className="feature">
            <div className="feature-icon">🔍</div>
            <h3>Unified Search</h3>
            <p>Search across all dashboards, tags, and folders</p>
          </div>

          <div className="feature">
            <div className="feature-icon">💰</div>
            <h3>Cost Monitoring</h3>
            <p>Dedicated cost dashboards with OpenCost integration</p>
          </div>

          <div className="feature">
            <div className="feature-icon">📈</div>
            <h3>Observability</h3>
            <p>Logs, metrics, and traces in organized dashboards</p>
          </div>

          <div className="feature">
            <div className="feature-icon">🎯</div>
            <h3>Tenant Isolation</h3>
            <p>Secure multi-tenant dashboard access</p>
          </div>
        </div>

        <div className="welcome-actions">
          <button
            className="primary-button"
            onClick={onShowBrowser}
          >
            Browse Dashboards
          </button>
        </div>
      </div>
    </div>
  );
}