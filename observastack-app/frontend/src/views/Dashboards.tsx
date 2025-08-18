/**
 * Dashboards view with unified Grafana integration
 */

import React from 'react';
import { UnifiedDashboardView } from '../components/dashboards';
import '../components/dashboards/dashboards.css';

export default function Dashboards() {
  return (
    <div className="dashboards-view">
      <UnifiedDashboardView
        showSidebar={true}
        theme="light"
        className="full-height"
      />
    </div>
  );
}