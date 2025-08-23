import '@testing-library/jest-dom';
import { vi } from 'vitest';
import React from 'react';

// Global test setup
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock echarts-for-react for chart components
vi.mock('echarts-for-react', () => {
  return {
    default: (props: any) => {
      return React.createElement('div', {
        'data-testid': 'echarts-mock',
        children: JSON.stringify(props.option)
      });
    }
  };
});

// Mock heroicons - COMPREHENSIVE LIST of all icons used in the application
vi.mock('@heroicons/react/24/outline', () => ({
  // Auth components
  EyeIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'eye-icon' }),
  EyeSlashIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'eye-slash-icon' }),
  
  // Navigation and UI
  ChevronDownIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'chevron-down-icon' }),
  HomeIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'home-icon' }),
  
  // Search and discovery
  MagnifyingGlassIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'magnifying-glass-icon' }),
  DocumentMagnifyingGlassIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'document-magnifying-glass-icon' }),
  
  // Time and scheduling
  CalendarIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'calendar-icon' }),
  ClockIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'clock-icon' }),
  
  // Charts and metrics
  ChartBarIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'chart-bar-icon' }),
  PlayIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'play-icon' }),
  
  // Code and documentation
  CodeBracketIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'code-bracket-icon' }),
  BookOpenIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'book-open-icon' }),
  
  // System and infrastructure
  CpuChipIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'cpu-chip-icon' }),
  ServerIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'server-icon' }),
  
  // Status and feedback
  XCircleIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'x-circle-icon' }),
  CheckCircleIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'check-circle-icon' }),
  ExclamationTriangleIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'exclamation-triangle-icon' }),
  
  // Tags and labels
  TagIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'tag-icon' }),
}));

vi.mock('@heroicons/react/24/solid', () => ({
  EyeIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'eye-icon-solid' }),
  EyeSlashIcon: (props: any) => React.createElement('svg', { ...props, 'data-testid': 'eye-slash-icon-solid' }),
}));