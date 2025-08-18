/**
 * Cost breakdown chart component for visualizing cost distribution
 */

import React from 'react';
import type { CostChartData } from '../../types/costs';

interface CostBreakdownChartProps {
  data: CostChartData;
  title: string;
  type?: 'pie' | 'bar' | 'doughnut';
  loading?: boolean;
  className?: string;
}

export function CostBreakdownChart({
  data,
  title,
  type = 'pie',
  loading = false,
  className = ''
}: CostBreakdownChartProps) {
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="h-64 bg-gray-200 rounded animate-pulse"></div>
      </div>
    );
  }

  // For now, we'll create a simple visual representation
  // In a real implementation, you'd use a charting library like Chart.js or Recharts
  const renderSimpleChart = () => {
    if (type === 'pie' || type === 'doughnut') {
      return <PieChart data={data} isDoughnut={type === 'doughnut'} />;
    } else {
      return <BarChart data={data} />;
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <div className="h-64">
        {renderSimpleChart()}
      </div>
    </div>
  );
}

// Simple pie chart implementation
function PieChart({ data, isDoughnut = false }: { data: CostChartData; isDoughnut?: boolean }) {
  const dataset = data.datasets[0];
  const total = dataset.data.reduce((sum, value) => sum + value, 0);
  
  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No cost data available
      </div>
    );
  }

  const colors = dataset.backgroundColor || [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'
  ];

  let cumulativePercentage = 0;

  return (
    <div className="flex items-center justify-center h-full">
      <div className="relative">
        <svg width="200" height="200" className="transform -rotate-90">
          <circle
            cx="100"
            cy="100"
            r={isDoughnut ? "80" : "90"}
            fill="none"
            stroke="#E5E7EB"
            strokeWidth={isDoughnut ? "20" : "180"}
          />
          {dataset.data.map((value, index) => {
            const percentage = (value / total) * 100;
            const strokeDasharray = `${percentage * (isDoughnut ? 5.03 : 5.65)} ${isDoughnut ? 503 : 565}`;
            const strokeDashoffset = -cumulativePercentage * (isDoughnut ? 5.03 : 5.65);
            
            cumulativePercentage += percentage;
            
            return (
              <circle
                key={index}
                cx="100"
                cy="100"
                r={isDoughnut ? "80" : "90"}
                fill="none"
                stroke={colors[index % colors.length]}
                strokeWidth={isDoughnut ? "20" : "180"}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-300"
              />
            );
          })}
        </svg>
        {isDoughnut && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                ${total.toFixed(0)}
              </div>
              <div className="text-sm text-gray-500">Total</div>
            </div>
          </div>
        )}
      </div>
      <div className="ml-6 space-y-2">
        {data.labels.map((label, index) => (
          <div key={index} className="flex items-center">
            <div
              className="w-3 h-3 rounded-full mr-2"
              style={{ backgroundColor: colors[index % colors.length] }}
            />
            <span className="text-sm text-gray-700">{label}</span>
            <span className="ml-auto text-sm font-medium text-gray-900">
              ${dataset.data[index].toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Simple bar chart implementation
function BarChart({ data }: { data: CostChartData }) {
  const dataset = data.datasets[0];
  const maxValue = Math.max(...dataset.data);
  
  if (maxValue === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No cost data available
      </div>
    );
  }

  const colors = dataset.backgroundColor || [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'
  ];

  return (
    <div className="h-full flex items-end justify-between space-x-2 px-4 pb-8">
      {data.labels.map((label, index) => {
        const value = dataset.data[index];
        const height = (value / maxValue) * 200; // Max height of 200px
        
        return (
          <div key={index} className="flex flex-col items-center flex-1">
            <div className="relative group">
              <div
                className="w-full rounded-t transition-all duration-300 hover:opacity-80"
                style={{
                  height: `${height}px`,
                  backgroundColor: colors[index % colors.length],
                  minHeight: '4px'
                }}
              />
              <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-900 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                ${value.toFixed(2)}
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-600 text-center truncate w-full">
              {label}
            </div>
          </div>
        );
      })}
    </div>
  );
}