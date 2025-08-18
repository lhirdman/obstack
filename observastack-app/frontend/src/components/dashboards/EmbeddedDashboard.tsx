/**
 * Embedded Grafana dashboard component with unified navigation
 */

import React, { useState, useRef, useEffect } from 'react';
import { useDashboardEmbed } from '../../hooks/useGrafana';

export interface EmbeddedDashboardProps {
  dashboardUid: string;
  panelId?: number;
  title?: string;
  theme?: 'light' | 'dark';
  timeFrom?: string;
  timeTo?: string;
  variables?: Record<string, string>;
  refresh?: string;
  height?: number;
  showNavigation?: boolean;
  showTimeControls?: boolean;
  showRefreshControls?: boolean;
  onNavigateBack?: () => void;
  onFullscreen?: () => void;
  className?: string;
}

export function EmbeddedDashboard({
  dashboardUid,
  panelId,
  title,
  theme = 'light',
  timeFrom,
  timeTo,
  variables,
  refresh,
  height = 600,
  showNavigation = true,
  showTimeControls = true,
  showRefreshControls = true,
  onNavigateBack,
  onFullscreen,
  className = ''
}: EmbeddedDashboardProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentTimeFrom, setCurrentTimeFrom] = useState(timeFrom);
  const [currentTimeTo, setCurrentTimeTo] = useState(timeTo);
  const [currentRefresh, setCurrentRefresh] = useState(refresh);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const { embedUrl, loading, error } = useDashboardEmbed({
    dashboardUid,
    panelId,
    theme,
    timeFrom: currentTimeFrom,
    timeTo: currentTimeTo,
    variables,
    refresh: currentRefresh
  });

  const handleFullscreen = () => {
    if (onFullscreen) {
      onFullscreen();
    } else {
      setIsFullscreen(!isFullscreen);
    }
  };

  const handleTimeRangeChange = (from: string, to: string) => {
    setCurrentTimeFrom(from);
    setCurrentTimeTo(to);
  };

  const handleRefreshChange = (newRefresh: string) => {
    setCurrentRefresh(newRefresh);
  };

  const refreshDashboard = () => {
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src;
    }
  };

  // Handle iframe messages for cross-origin communication
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Only accept messages from Grafana
      if (!embedUrl || !event.origin.includes('grafana')) return;

      try {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
        
        // Handle time range changes from Grafana
        if (data.type === 'timeRangeChanged') {
          setCurrentTimeFrom(data.from);
          setCurrentTimeTo(data.to);
        }
        
        // Handle refresh interval changes
        if (data.type === 'refreshChanged') {
          setCurrentRefresh(data.refresh);
        }
      } catch (err) {
        // Ignore invalid messages
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [embedUrl]);

  if (loading) {
    return (
      <div className={`embedded-dashboard loading ${className}`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`embedded-dashboard error ${className}`}>
        <div className="error-container">
          <h3>Dashboard Error</h3>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  if (!embedUrl) {
    return (
      <div className={`embedded-dashboard empty ${className}`}>
        <div className="empty-container">
          <p>No dashboard URL available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`embedded-dashboard ${isFullscreen ? 'fullscreen' : ''} ${className}`}>
      {showNavigation && (
        <DashboardNavigation
          title={title || `Dashboard ${dashboardUid}`}
          showTimeControls={showTimeControls}
          showRefreshControls={showRefreshControls}
          timeFrom={currentTimeFrom}
          timeTo={currentTimeTo}
          refresh={currentRefresh}
          onNavigateBack={onNavigateBack}
          onFullscreen={handleFullscreen}
          onTimeRangeChange={handleTimeRangeChange}
          onRefreshChange={handleRefreshChange}
          onRefresh={refreshDashboard}
          isFullscreen={isFullscreen}
        />
      )}
      
      <div className="dashboard-iframe-container">
        <iframe
          ref={iframeRef}
          src={embedUrl}
          width="100%"
          height={height}
          frameBorder="0"
          title={title || `Dashboard ${dashboardUid}`}
          className="dashboard-iframe"
          sandbox="allow-same-origin allow-scripts allow-forms"
        />
      </div>
    </div>
  );
}

interface DashboardNavigationProps {
  title: string;
  showTimeControls: boolean;
  showRefreshControls: boolean;
  timeFrom?: string;
  timeTo?: string;
  refresh?: string;
  onNavigateBack?: () => void;
  onFullscreen: () => void;
  onTimeRangeChange: (from: string, to: string) => void;
  onRefreshChange: (refresh: string) => void;
  onRefresh: () => void;
  isFullscreen: boolean;
}

function DashboardNavigation({
  title,
  showTimeControls,
  showRefreshControls,
  timeFrom,
  timeTo,
  refresh,
  onNavigateBack,
  onFullscreen,
  onTimeRangeChange,
  onRefreshChange,
  onRefresh,
  isFullscreen
}: DashboardNavigationProps) {
  const timeRangeOptions = [
    { label: 'Last 5m', value: 'now-5m', to: 'now' },
    { label: 'Last 15m', value: 'now-15m', to: 'now' },
    { label: 'Last 30m', value: 'now-30m', to: 'now' },
    { label: 'Last 1h', value: 'now-1h', to: 'now' },
    { label: 'Last 3h', value: 'now-3h', to: 'now' },
    { label: 'Last 6h', value: 'now-6h', to: 'now' },
    { label: 'Last 12h', value: 'now-12h', to: 'now' },
    { label: 'Last 24h', value: 'now-24h', to: 'now' },
    { label: 'Last 7d', value: 'now-7d', to: 'now' },
    { label: 'Last 30d', value: 'now-30d', to: 'now' }
  ];

  const refreshOptions = [
    { label: 'Off', value: '' },
    { label: '5s', value: '5s' },
    { label: '10s', value: '10s' },
    { label: '30s', value: '30s' },
    { label: '1m', value: '1m' },
    { label: '5m', value: '5m' },
    { label: '15m', value: '15m' },
    { label: '30m', value: '30m' },
    { label: '1h', value: '1h' }
  ];

  return (
    <div className="dashboard-navigation">
      <div className="nav-left">
        {onNavigateBack && (
          <button
            className="nav-button back-button"
            onClick={onNavigateBack}
            title="Go back"
          >
            ← Back
          </button>
        )}
        
        <div className="dashboard-breadcrumb">
          <span className="breadcrumb-item">Dashboards</span>
          <span className="breadcrumb-separator">/</span>
          <span className="breadcrumb-item current">{title}</span>
        </div>
      </div>

      <div className="nav-center">
        {showTimeControls && (
          <div className="time-controls">
            <select
              value={`${timeFrom}|${timeTo}`}
              onChange={(e) => {
                const [from, to] = e.target.value.split('|');
                onTimeRangeChange(from, to);
              }}
              className="time-range-select"
            >
              {timeRangeOptions.map(option => (
                <option
                  key={option.value}
                  value={`${option.value}|${option.to}`}
                >
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="nav-right">
        {showRefreshControls && (
          <div className="refresh-controls">
            <select
              value={refresh || ''}
              onChange={(e) => onRefreshChange(e.target.value)}
              className="refresh-select"
            >
              {refreshOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            
            <button
              className="nav-button refresh-button"
              onClick={onRefresh}
              title="Refresh dashboard"
            >
              ↻
            </button>
          </div>
        )}

        <button
          className="nav-button fullscreen-button"
          onClick={onFullscreen}
          title={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {isFullscreen ? '⤓' : '⤢'}
        </button>
      </div>
    </div>
  );
}