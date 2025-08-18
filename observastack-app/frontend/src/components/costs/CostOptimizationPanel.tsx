/**
 * Cost optimization recommendations panel component
 */

import React, { useState } from 'react';
import type { CostOptimization, OptimizationType, ImplementationEffort, RiskLevel } from '../../types/costs';

interface CostOptimizationPanelProps {
  optimizations: CostOptimization[];
  loading?: boolean;
  onRefresh?: () => void;
  className?: string;
}

export function CostOptimizationPanel({
  optimizations,
  loading = false,
  onRefresh,
  className = ''
}: CostOptimizationPanelProps) {
  const [selectedType, setSelectedType] = useState<OptimizationType | 'all'>('all');
  const [sortBy, setSortBy] = useState<'savings' | 'effort' | 'risk'>('savings');

  const filteredOptimizations = optimizations.filter(opt => 
    selectedType === 'all' || opt.type === selectedType
  );

  const sortedOptimizations = [...filteredOptimizations].sort((a, b) => {
    switch (sortBy) {
      case 'savings':
        return b.potentialSavings - a.potentialSavings;
      case 'effort':
        return getEffortValue(a.implementationEffort) - getEffortValue(b.implementationEffort);
      case 'risk':
        return getRiskValue(a.riskLevel) - getRiskValue(b.riskLevel);
      default:
        return 0;
    }
  });

  const totalSavings = optimizations.reduce((sum, opt) => sum + opt.potentialSavings, 0);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4 animate-pulse"></div>
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className="border rounded-lg p-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Cost Optimization</h3>
          <p className="text-sm text-gray-600">
            {optimizations.length} recommendations • ${totalSavings.toFixed(2)} potential savings
          </p>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Filters and sorting */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Type:</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as OptimizationType | 'all')}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Types</option>
            <option value="rightsizing">Rightsizing</option>
            <option value="scheduling">Scheduling</option>
            <option value="storage">Storage</option>
            <option value="networking">Networking</option>
            <option value="workload_optimization">Workload</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'savings' | 'effort' | 'risk')}
            className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="savings">Potential Savings</option>
            <option value="effort">Implementation Effort</option>
            <option value="risk">Risk Level</option>
          </select>
        </div>
      </div>

      {/* Optimization recommendations */}
      <div className="space-y-4">
        {sortedOptimizations.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No optimization recommendations available
          </div>
        ) : (
          sortedOptimizations.map((optimization, index) => (
            <OptimizationCard key={index} optimization={optimization} />
          ))
        )}
      </div>
    </div>
  );
}

interface OptimizationCardProps {
  optimization: CostOptimization;
}

function OptimizationCard({ optimization }: OptimizationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getTypeColor = (type: OptimizationType) => {
    switch (type) {
      case 'rightsizing':
        return 'bg-blue-100 text-blue-800';
      case 'scheduling':
        return 'bg-green-100 text-green-800';
      case 'storage':
        return 'bg-yellow-100 text-yellow-800';
      case 'networking':
        return 'bg-purple-100 text-purple-800';
      case 'workload_optimization':
        return 'bg-indigo-100 text-indigo-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getEffortColor = (effort: ImplementationEffort) => {
    switch (effort) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getRiskColor = (risk: RiskLevel) => {
    switch (risk) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${getTypeColor(optimization.type)}`}>
              {optimization.type.replace('_', ' ')}
            </span>
            <span className="text-lg font-semibold text-green-600">
              ${optimization.potentialSavings.toFixed(2)}
            </span>
            <span className="text-sm text-gray-500">savings</span>
          </div>
          
          <h4 className="text-md font-medium text-gray-900 mb-1">
            {optimization.title}
          </h4>
          
          <p className="text-sm text-gray-600 mb-3">
            {optimization.description}
          </p>
          
          <div className="flex items-center space-x-4 text-sm">
            <div className="flex items-center">
              <span className="text-gray-500 mr-1">Effort:</span>
              <span className={`font-medium capitalize ${getEffortColor(optimization.implementationEffort)}`}>
                {optimization.implementationEffort}
              </span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-500 mr-1">Risk:</span>
              <span className={`font-medium capitalize ${getRiskColor(optimization.riskLevel)}`}>
                {optimization.riskLevel}
              </span>
            </div>
            <div className="flex items-center">
              <span className="text-gray-500 mr-1">Confidence:</span>
              <span className="font-medium text-gray-900">
                {(optimization.confidenceScore * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
        
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="ml-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg
            className={`w-5 h-5 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {/* Resource recommendations */}
          {Object.keys(optimization.currentResources).length > 0 && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-900 mb-2">Resource Changes</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Current</span>
                  <div className="mt-1 space-y-1">
                    {Object.entries(optimization.currentResources).map(([resource, value]) => (
                      <div key={resource} className="flex justify-between text-sm">
                        <span className="text-gray-600 capitalize">{resource}:</span>
                        <span className="font-medium">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Recommended</span>
                  <div className="mt-1 space-y-1">
                    {Object.entries(optimization.recommendedResources).map(([resource, value]) => (
                      <div key={resource} className="flex justify-between text-sm">
                        <span className="text-gray-600 capitalize">{resource}:</span>
                        <span className="font-medium text-green-600">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Implementation steps */}
          <div>
            <h5 className="text-sm font-medium text-gray-900 mb-2">Implementation Steps</h5>
            <ol className="list-decimal list-inside space-y-1">
              {optimization.steps.map((step, index) => (
                <li key={index} className="text-sm text-gray-600">
                  {step}
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper functions
function getEffortValue(effort: ImplementationEffort): number {
  switch (effort) {
    case 'low': return 1;
    case 'medium': return 2;
    case 'high': return 3;
    default: return 2;
  }
}

function getRiskValue(risk: RiskLevel): number {
  switch (risk) {
    case 'low': return 1;
    case 'medium': return 2;
    case 'high': return 3;
    default: return 2;
  }
}