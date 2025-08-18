# Search Components Documentation

This directory contains the enhanced search UI components for the ObservaStack unified observability platform. These components provide a comprehensive search experience across logs, metrics, and traces with advanced filtering, time range selection, and cross-signal navigation capabilities.

## Components Overview

### SearchForm
The main search interface component that provides:
- Free text search input with type selection (logs, metrics, traces, all)
- Advanced time range selector with quick ranges and custom date/time selection
- Dynamic filter system with field-based filtering
- Real-time search with debouncing support

**Key Features:**
- Supports all search types: logs, metrics, traces, and unified search
- Time range selection with common presets (15m, 1h, 24h, etc.)
- Advanced filtering with operators: equals, contains, regex, range, exists
- Form validation and error handling
- Loading states and disabled states

**Usage:**
```tsx
import { SearchForm } from '../components/search'

function MySearchPage() {
  const handleSearch = (query: SearchQuery) => {
    // Handle search execution
  }

  return (
    <SearchForm
      onSearch={handleSearch}
      loading={isSearching}
      initialQuery={savedQuery}
    />
  )
}
```

### SearchResults
Displays search results with source identification and cross-signal navigation:
- Unified display of logs, metrics, and traces
- Source-specific formatting and icons
- Cross-signal correlation links
- Search statistics and performance metrics
- Pagination support

**Key Features:**
- Source-aware result rendering (logs, metrics, traces)
- Correlation ID linking for cross-signal navigation
- Search performance statistics
- Empty state and loading skeleton
- Clickable results with custom handlers

**Usage:**
```tsx
import { SearchResults } from '../components/search'

function MySearchResults() {
  return (
    <SearchResults
      results={searchResults}
      loading={isLoading}
      onResultClick={handleResultClick}
      onCorrelationClick={handleCorrelationClick}
    />
  )
}
```

### SearchHistory
Manages search history and saved searches:
- Recent search history with automatic storage
- Saved searches with custom names
- Quick re-execution of previous searches
- History management (save, delete, filter)

**Key Features:**
- Automatic search history tracking
- Save searches with custom names
- Filter between all history and saved searches only
- Local storage persistence
- Bulk operations support

**Usage:**
```tsx
import { SearchHistory } from '../components/search'

function MySearchSidebar() {
  return (
    <SearchHistory
      onSelectQuery={handleQuerySelect}
      onSaveQuery={handleSaveQuery}
      onDeleteQuery={handleDeleteQuery}
    />
  )
}
```

### TimeRangeSelector
Advanced time range selection component:
- Quick range presets (15m, 1h, 24h, 7d, etc.)
- Custom date/time range selection
- Relative time support (now-1h, now-24h)
- ISO 8601 timestamp support

**Key Features:**
- Popover-based interface
- Quick range buttons for common time periods
- Custom date/time picker for precise ranges
- Relative time string support
- Formatted display of selected ranges

### SearchFilters
Dynamic filter management system:
- Add/remove filters dynamically
- Multiple filter operators (equals, contains, regex, range, exists)
- Common field suggestions
- Filter validation and error handling

**Key Features:**
- Dynamic filter addition/removal
- Field-specific operator suggestions
- Range value support for numeric fields
- Exists operator for field presence checking
- Visual filter management interface

## Data Models

### SearchQuery
```typescript
interface SearchQuery {
  freeText: string                    // Main search text
  type: 'logs' | 'metrics' | 'traces' | 'all'  // Search scope
  timeRange: TimeRange               // Time bounds
  filters: SearchFilter[]            // Additional filters
  tenantId: string                   // Tenant isolation
  limit?: number                     // Result limit
  offset?: number                    // Pagination offset
}
```

### SearchResult
```typescript
interface SearchResult {
  items: SearchItem[]                // Result items
  stats: SearchStats                 // Performance metrics
  facets: SearchFacet[]             // Aggregation facets
  nextToken?: string                 // Pagination token
}
```

### SearchItem
```typescript
interface SearchItem {
  id: string                         // Unique identifier
  timestamp: string                  // ISO 8601 timestamp
  source: 'logs' | 'metrics' | 'traces'  // Data source
  service: string                    // Service name
  content: LogItem | MetricItem | TraceItem  // Source-specific content
  correlationId?: string             // Cross-signal correlation
}
```

## Hooks

### useSearch
Primary search hook with history management:
```typescript
const {
  results,           // Current search results
  loading,           // Search in progress
  error,             // Search error
  search,            // Execute search function
  clearResults,      // Clear current results
  getSearchHistory,  // Get search history
  saveSearch,        // Save search with name
  deleteFromHistory  // Remove from history
} = useSearch({
  enableHistory: true,     // Enable history tracking
  enableAutoSearch: false, // Auto-search on query change
  debounceMs: 300         // Debounce delay
})
```

### useCrossSignalNavigation
Cross-signal correlation and navigation:
```typescript
const {
  navigateToCorrelatedData,  // Navigate to correlated data
  findRelatedTraces,         // Find traces for log item
  findRelatedLogs           // Find logs for trace item
} = useCrossSignalNavigation()
```

## Styling and Theming

All components use Tailwind CSS classes and follow the ObservaStack design system:

- **Colors**: Blue primary, gray neutrals, semantic colors for status
- **Typography**: System font stack with monospace for code/data
- **Spacing**: Consistent 4px grid system
- **Shadows**: Subtle shadows for depth and hierarchy
- **Borders**: Rounded corners and subtle borders

### Customization
Components accept `className` props for custom styling:
```tsx
<SearchForm className="custom-search-form" />
<SearchResults className="custom-results" />
```

## Accessibility

All components follow WCAG 2.1 AA guidelines:
- Proper ARIA labels and roles
- Keyboard navigation support
- Screen reader compatibility
- Focus management
- Color contrast compliance

### Keyboard Shortcuts
- `Enter`: Submit search form
- `Escape`: Close popovers/modals
- `Tab/Shift+Tab`: Navigate between elements
- `Arrow keys`: Navigate within lists

## Performance Considerations

### Search Debouncing
The search form includes debouncing to prevent excessive API calls:
```typescript
// Default 300ms debounce
const { search } = useSearch({ debounceMs: 300 })

// Immediate search (bypass debounce)
search(query, true)
```

### Result Virtualization
For large result sets, consider implementing virtualization:
- Use `react-window` or `react-virtualized`
- Implement pagination with `nextToken`
- Lazy load result details

### Memory Management
- Search history is limited to 50 items
- Results are cleared when component unmounts
- Debounce timers are properly cleaned up

## Testing

### Unit Tests
Components include comprehensive unit tests:
```bash
npm run test -- SearchForm.test.tsx
npm run test -- SearchResults.test.tsx
npm run test -- SearchHistory.test.tsx
```

### Storybook Stories
Interactive component documentation:
```bash
npm run storybook
```

Stories include:
- Default states
- Loading states
- Error states
- Edge cases
- Interactive examples

### Integration Tests
End-to-end testing with Playwright:
```bash
npm run test:e2e
```

## API Integration

### Search Endpoint
```typescript
POST /api/search
Content-Type: application/json

{
  "freeText": "error rate",
  "type": "logs",
  "timeRange": {
    "from": "now-1h",
    "to": "now"
  },
  "filters": [
    {
      "field": "level",
      "operator": "equals",
      "value": "error"
    }
  ]
}
```

### Response Format
```typescript
{
  "items": [...],
  "stats": {
    "matched": 42,
    "scanned": 1000,
    "latencyMs": 150,
    "sources": {
      "logs": 42
    }
  },
  "facets": [...],
  "nextToken": "..."
}
```

## Error Handling

### Search Errors
- Network errors with retry logic
- Validation errors with field-specific messages
- Rate limiting with backoff
- Service unavailable with fallback

### User Feedback
- Toast notifications for actions
- Inline error messages
- Loading states and progress indicators
- Empty states with helpful guidance

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Polyfills
- Date/time APIs for older browsers
- Fetch API polyfill if needed
- CSS Grid/Flexbox support

## Migration Guide

### From Legacy Search
1. Replace old search components with new ones
2. Update search query format
3. Implement new filter system
4. Add time range selection
5. Enable search history

### Breaking Changes
- Search query structure changed
- Filter format updated
- Time range format standardized
- Component props renamed

## Contributing

### Adding New Features
1. Create feature branch
2. Implement component with tests
3. Add Storybook stories
4. Update documentation
5. Submit pull request

### Code Style
- Use TypeScript for all components
- Follow ESLint configuration
- Use Prettier for formatting
- Include JSDoc comments
- Write comprehensive tests

## Support

For questions or issues:
- Check Storybook documentation
- Review component tests
- Consult API documentation
- File GitHub issues for bugs