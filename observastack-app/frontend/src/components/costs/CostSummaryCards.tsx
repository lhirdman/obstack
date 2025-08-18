/**
 * Cost summary cards component for displaying key cost metrics
 */

import React from 'react';
import type { CostSummaryCard } from '../../types/costs';

interface CostSummaryCardsProps {
  cards: CostSummaryCard[];
  loading?: boolean;
  className?: string;
}

export function CostSummaryCards({ 
  cards, 
  loading = false, 
  className = '' 
}: CostSummaryCardsProps) {
  if (loading) {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-1/4"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 ${className}`}>
      {cards.map((card, index) => (
        <CostSummaryCard key={index} card={card} />
      ))}
    </div>
  );
}

interface CostSummaryCardProps {
  card: CostSummaryCard;
}

function CostSummaryCard({ card }: CostSummaryCardProps) {
  const getColorClasses = (color?: string) => {
    switch (color) {
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'danger':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getTrendIcon = (direction?: 'up' | 'down' | 'stable') => {
    switch (direction) {
      case 'up':
        return (
          <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'down':
        return (
          <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M14.707 12.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        );
      case 'stable':
        return (
          <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  const formatValue = (value: number, unit: string) => {
    if (unit === 'USD' || unit === '$') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(value);
    }
    
    if (unit === '%') {
      return `${value.toFixed(1)}%`;
    }
    
    return `${value.toLocaleString()} ${unit}`;
  };

  return (
    <div className={`bg-white rounded-lg shadow border-l-4 p-6 ${getColorClasses(card.color)}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">
            {card.title}
          </p>
          <p className="text-2xl font-bold text-gray-900">
            {formatValue(card.value, card.unit)}
          </p>
          {card.trend && (
            <div className="flex items-center mt-2">
              {getTrendIcon(card.trend.direction)}
              <span className={`ml-1 text-sm font-medium ${
                card.trend.direction === 'up' ? 'text-red-600' :
                card.trend.direction === 'down' ? 'text-green-600' :
                'text-gray-600'
              }`}>
                {Math.abs(card.trend.percentage).toFixed(1)}%
              </span>
              <span className="ml-1 text-sm text-gray-500">
                vs last period
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}