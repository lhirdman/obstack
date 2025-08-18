/**
 * Cost trend chart component for displaying cost trends over time
 */

import React from 'react';
import type { CostTrend } from '../../types/costs';

interface CostTrendChartProps {
  trends: CostTrend[];
  title: string;
  loading?: boolean;
  className?: string;
  showForecast?: boolean;
}

export function CostTrendChart({
  trends,
  title,
  loading = false,
  className = '',
  showForecast = true
}: CostTrendChartProps) {
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
      </div>
    );
  }

  if (trends.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          No trend data available
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <div className="flex items-center space-x-4">
          {showForecast && (
            <div className="flex items-center">
              <div className="w-3 h-0.5 bg-blue-300 border-dashed border-t-2 border-blue-300 mr-2"></div>
              <span className="text-sm text-gray-600">Forecast</span>
            </div>
          )}
          <div className="flex items-center">
            <div className="w-3 h-0.5 bg-blue-600 mr-2"></div>
            <span className="text-sm text-gray-600">Actual</span>
          </div>
        </div>
      </div>
      
      <div className="h-64">
        <TrendLineChart trends={trends} showForecast={showForecast} />
      </div>
      
      {/* Trend summary */}
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        {trends.slice(0, 3).map((trend, index) => (
          <TrendSummary key={index} trend={trend} />
        ))}
      </div>
    </div>
  );
}

function TrendLineChart({ trends, showForecast }: { trends: CostTrend[]; showForecast: boolean }) {
  // Combine all data points from all trends
  const allDataPoints = trends.flatMap(trend => 
    trend.dataPoints.map(point => ({
      ...point,
      resourceType: trend.resourceType,
      isForecast: false
    }))
  );

  const allForecastPoints = showForecast ? trends.flatMap(trend =>
    trend.forecastPoints.map(point => ({
      ...point,
      resourceType: trend.resourceType,
      isForecast: true
    }))
  ) : [];

  const combinedPoints = [...allDataPoints, ...allForecastPoints].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  if (combinedPoints.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No trend data available
      </div>
    );
  }

  const maxValue = Math.max(...combinedPoints.map(point => point.value));
  const minValue = Math.min(...combinedPoints.map(point => point.value));
  const valueRange = maxValue - minValue || 1;

  const colors = {
    cpu: '#3B82F6',
    memory: '#10B981',
    storage: '#F59E0B',
    network: '#EF4444',
    gpu: '#8B5CF6'
  };

  // Group points by resource type
  const pointsByResource = combinedPoints.reduce((acc, point) => {
    if (!acc[point.resourceType]) {
      acc[point.resourceType] = [];
    }
    acc[point.resourceType].push(point);
    return acc;
  }, {} as Record<string, typeof combinedPoints>);

  return (
    <div className="relative h-full">
      <svg width="100%" height="100%" className="overflow-visible">
        {/* Grid lines */}
        {Array.from({ length: 5 }).map((_, i) => {
          const y = (i / 4) * 100;
          return (
            <g key={i}>
              <line
                x1="0%"
                y1={`${y}%`}
                x2="100%"
                y2={`${y}%`}
                stroke="#E5E7EB"
                strokeWidth="1"
              />
              <text
                x="0"
                y={`${y}%`}
                dy="-4"
                className="text-xs fill-gray-500"
              >
                ${((maxValue - (y / 100) * valueRange)).toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Trend lines */}
        {Object.entries(pointsByResource).map(([resourceType, points]) => {
          const actualPoints = points.filter(p => !p.isForecast);
          const forecastPoints = points.filter(p => p.isForecast);
          
          const createPath = (dataPoints: typeof points) => {
            if (dataPoints.length < 2) return '';
            
            return dataPoints.map((point, index) => {
              const x = (index / (dataPoints.length - 1)) * 100;
              const y = ((maxValue - point.value) / valueRange) * 100;
              return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
            }).join(' ');
          };

          return (
            <g key={resourceType}>
              {/* Actual trend line */}
              {actualPoints.length > 1 && (
                <path
                  d={createPath(actualPoints)}
                  fill="none"
                  stroke={colors[resourceType as keyof typeof colors] || '#6B7280'}
                  strokeWidth="2"
                  className="transition-all duration-300"
                />
              )}
              
              {/* Forecast trend line */}
              {showForecast && forecastPoints.length > 1 && (
                <path
                  d={createPath(forecastPoints)}
                  fill="none"
                  stroke={colors[resourceType as keyof typeof colors] || '#6B7280'}
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  opacity="0.6"
                  className="transition-all duration-300"
                />
              )}
              
              {/* Data points */}
              {actualPoints.map((point, index) => {
                const x = (index / Math.max(actualPoints.length - 1, 1)) * 100;
                const y = ((maxValue - point.value) / valueRange) * 100;
                
                return (
                  <circle
                    key={`${resourceType}-${index}`}
                    cx={`${x}%`}
                    cy={`${y}%`}
                    r="3"
                    fill={colors[resourceType as keyof typeof colors] || '#6B7280'}
                    className="hover:r-4 transition-all duration-200"
                  >
                    <title>${point.value.toFixed(2)} - {new Date(point.timestamp).toLocaleDateString()}</title>
                  </circle>
                );
              })}
            </g>
          );
        })}
      </svg>
      
      {/* Legend */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-center space-x-4 mt-2">
        {Object.keys(pointsByResource).map(resourceType => (
          <div key={resourceType} className="flex items-center">
            <div
              className="w-3 h-3 rounded-full mr-1"
              style={{ backgroundColor: colors[resourceType as keyof typeof colors] || '#6B7280' }}
            />
            <span className="text-xs text-gray-600 capitalize">{resourceType}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TrendSummary({ trend }: { trend: CostTrend }) {
  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'increasing':
        return 'text-red-600';
      case 'decreasing':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing':
        return '↗';
      case 'decreasing':
        return '↘';
      default:
        return '→';
    }
  };

  const currentValue = trend.dataPoints[trend.dataPoints.length - 1]?.value || 0;

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm font-medium text-gray-900 capitalize">
          {trend.resourceType}
        </span>
        <span className={`text-sm font-medium ${getTrendColor(trend.trendDirection)}`}>
          {getTrendIcon(trend.trendDirection)} {Math.abs(trend.trendPercentage).toFixed(1)}%
        </span>
      </div>
      <div className="text-lg font-bold text-gray-900">
        ${currentValue.toFixed(2)}
      </div>
      <div className="text-xs text-gray-500">
        {trend.namespace} {trend.workload && `• ${trend.workload}`}
      </div>
    </div>
  );
}