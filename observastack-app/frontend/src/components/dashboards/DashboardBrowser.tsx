/**
 * Dashboard browser component for discovering and organizing dashboards
 */

import React, { useState, useEffect } from 'react';
import { useGrafana } from '../../hooks/useGrafana';
import { DashboardInfo } from '../../services/grafana-service';

export interface DashboardBrowserProps {
  onDashboardSelect: (dashboard: DashboardInfo) => void;
  selectedDashboardUid?: string;
  showCostDashboards?: boolean;
  showObservabilityDashboards?: boolean;
  className?: string;
}

export function DashboardBrowser({
  onDashboardSelect,
  selectedDashboardUid,
  showCostDashboards = true,
  showObservabilityDashboards = true,
  className = ''
}: DashboardBrowserProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'cost' | 'observability'>('all');
  const [filteredDashboards, setFilteredDashboards] = useState<DashboardInfo[]>([]);

  const {
    dashboards,
    costDashboards,
    observabilityDashboards,
    loading,
    error,
    refresh
  } = useGrafana();

  // Filter dashboards based on search and category
  useEffect(() => {
    let dashboardsToFilter: DashboardInfo[] = [];

    switch (selectedCategory) {
      case 'cost':
        dashboardsToFilter = costDashboards;
        break;
      case 'observability':
        dashboardsToFilter = observabilityDashboards;
        break;
      default:
        dashboardsToFilter = dashboards;
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      dashboardsToFilter = dashboardsToFilter.filter(dashboard =>
        dashboard.title.toLowerCase().includes(query) ||
        dashboard.tags.some(tag => tag.toLowerCase().includes(query)) ||
        (dashboard.folder_title && dashboard.folder_title.toLowerCase().includes(query))
      );
    }

    setFilteredDashboards(dashboardsToFilter);
  }, [dashboards, costDashboards, observabilityDashboards, searchQuery, selectedCategory]);

  const handleCategoryChange = (category: 'all' | 'cost' | 'observability') => {
    setSelectedCategory(category);
    setSearchQuery(''); // Clear search when changing category
  };

  const groupDashboardsByFolder = (dashboards: DashboardInfo[]) => {
    const grouped: Record<string, DashboardInfo[]> = {};
    
    dashboards.forEach(dashboard => {
      const folder = dashboard.folder_title || 'General';
      if (!grouped[folder]) {
        grouped[folder] = [];
      }
      grouped[folder].push(dashboard);
    });

    return grouped;
  };

  const groupedDashboards = groupDashboardsByFolder(filteredDashboards);

  if (loading) {
    return (
      <div className={`dashboard-browser loading ${className}`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading dashboards...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`dashboard-browser error ${className}`}>
        <div className="error-container">
          <h3>Error Loading Dashboards</h3>
          <p>{error}</p>
          <button onClick={refresh}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className={`dashboard-browser ${className}`}>
      <div className="browser-header">
        <h2>Dashboards</h2>
        
        <div className="browser-controls">
          <div className="category-tabs">
            <button
              className={`category-tab ${selectedCategory === 'all' ? 'active' : ''}`}
              onClick={() => handleCategoryChange('all')}
            >
              All ({dashboards.length})
            </button>
            
            {showObservabilityDashboards && (
              <button
                className={`category-tab ${selectedCategory === 'observability' ? 'active' : ''}`}
                onClick={() => handleCategoryChange('observability')}
              >
                Observability ({observabilityDashboards.length})
              </button>
            )}
            
            {showCostDashboards && (
              <button
                className={`category-tab ${selectedCategory === 'cost' ? 'active' : ''}`}
                onClick={() => handleCategoryChange('cost')}
              >
                Cost Monitoring ({costDashboards.length})
              </button>
            )}
          </div>

          <div className="search-controls">
            <input
              type="text"
              placeholder="Search dashboards..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            
            <button
              onClick={refresh}
              className="refresh-button"
              title="Refresh dashboards"
            >
              ↻
            </button>
          </div>
        </div>
      </div>

      <div className="browser-content">
        {Object.keys(groupedDashboards).length === 0 ? (
          <div className="empty-state">
            <p>No dashboards found</p>
            {searchQuery && (
              <button onClick={() => setSearchQuery('')}>Clear search</button>
            )}
          </div>
        ) : (
          <div className="dashboard-folders">
            {Object.entries(groupedDashboards).map(([folderName, folderDashboards]) => (
              <DashboardFolder
                key={folderName}
                name={folderName}
                dashboards={folderDashboards}
                selectedDashboardUid={selectedDashboardUid}
                onDashboardSelect={onDashboardSelect}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface DashboardFolderProps {
  name: string;
  dashboards: DashboardInfo[];
  selectedDashboardUid?: string;
  onDashboardSelect: (dashboard: DashboardInfo) => void;
}

function DashboardFolder({
  name,
  dashboards,
  selectedDashboardUid,
  onDashboardSelect
}: DashboardFolderProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="dashboard-folder">
      <div
        className="folder-header"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <span className={`folder-icon ${isExpanded ? 'expanded' : 'collapsed'}`}>
          {isExpanded ? '▼' : '▶'}
        </span>
        <span className="folder-name">{name}</span>
        <span className="folder-count">({dashboards.length})</span>
      </div>

      {isExpanded && (
        <div className="folder-dashboards">
          {dashboards.map(dashboard => (
            <DashboardCard
              key={dashboard.uid}
              dashboard={dashboard}
              isSelected={dashboard.uid === selectedDashboardUid}
              onSelect={() => onDashboardSelect(dashboard)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface DashboardCardProps {
  dashboard: DashboardInfo;
  isSelected: boolean;
  onSelect: () => void;
}

function DashboardCard({ dashboard, isSelected, onSelect }: DashboardCardProps) {
  const isCostDashboard = dashboard.tags.some(tag => 
    ['cost', 'opencost', 'kubernetes-cost'].includes(tag.toLowerCase())
  );

  const isObservabilityDashboard = dashboard.tags.some(tag =>
    ['observability', 'monitoring', 'logs', 'metrics', 'traces'].includes(tag.toLowerCase())
  );

  return (
    <div
      className={`dashboard-card ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
    >
      <div className="card-header">
        <h4 className="dashboard-title">{dashboard.title}</h4>
        
        <div className="dashboard-indicators">
          {isCostDashboard && (
            <span className="indicator cost-indicator" title="Cost Monitoring">
              💰
            </span>
          )}
          {isObservabilityDashboard && (
            <span className="indicator observability-indicator" title="Observability">
              📊
            </span>
          )}
        </div>
      </div>

      {dashboard.tags.length > 0 && (
        <div className="dashboard-tags">
          {dashboard.tags.slice(0, 3).map(tag => (
            <span key={tag} className="tag">
              {tag}
            </span>
          ))}
          {dashboard.tags.length > 3 && (
            <span className="tag more">+{dashboard.tags.length - 3}</span>
          )}
        </div>
      )}

      <div className="card-footer">
        <span className="dashboard-uid">{dashboard.uid}</span>
      </div>
    </div>
  );
}