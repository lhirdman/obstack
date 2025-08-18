# Coding Standards and Best Practices

## Critical Rules for Code Quality

**FUNDAMENTAL PRINCIPLE**: Write code that is maintainable, testable, and follows established patterns. Avoid duplication, ensure consistency, and prioritize clarity over cleverness.

## Project Architecture Patterns

### **1. Directory Structure (MUST Follow)**

#### Frontend Structure
```
observastack-app/frontend/src/
├── components/           # Reusable UI components
│   ├── ui/              # Basic UI primitives (Button, Input, etc.)
│   ├── forms/           # Form-specific components
│   ├── charts/          # Data visualization components
│   └── layout/          # Layout components (Header, Sidebar, etc.)
├── views/               # Page-level components (Search, Alerts, etc.)
├── hooks/               # Custom React hooks
├── lib/                 # Utility functions and configurations
├── services/            # API service functions
├── types/               # TypeScript type definitions
├── contexts/            # React contexts
└── utils/               # Pure utility functions
```

#### Backend Structure
```
observastack-app/bff/app/
├── api/                 # API route handlers
│   ├── v1/             # API version 1 routes
│   └── dependencies/    # Shared dependencies
├── auth/               # Authentication and authorization
├── models/             # Pydantic models and database schemas
├── services/           # Business logic services
├── core/               # Core configuration and utilities
├── db/                 # Database connection and utilities
└── utils/              # Pure utility functions
```

### **2. Naming Conventions (STRICT)**

#### TypeScript/React
- **Files**: `kebab-case.ts`, `PascalCase.tsx` for components
- **Components**: `PascalCase` (SearchResults, AlertCard)
- **Functions**: `camelCase` (handleSearch, formatDate)
- **Constants**: `SCREAMING_SNAKE_CASE` (API_BASE_URL)
- **Types/Interfaces**: `PascalCase` with descriptive names (SearchQuery, UserProfile)

#### Python/FastAPI
- **Files**: `snake_case.py`
- **Classes**: `PascalCase` (UserService, AlertManager)
- **Functions**: `snake_case` (get_current_user, process_alert)
- **Constants**: `SCREAMING_SNAKE_CASE` (DATABASE_URL)
- **Private methods**: `_snake_case` (_validate_token)

## Code Organization Rules

### **1. Single Responsibility Principle**

#### ✅ DO: One responsibility per file/function
```typescript
// ✅ Good: Single purpose utility
export function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString();
}

// ✅ Good: Single purpose component
export function SearchInput({ onSearch, placeholder }: SearchInputProps) {
  // Only handles search input logic
}
```

#### ❌ DON'T: Multiple responsibilities
```typescript
// ❌ Bad: Mixed responsibilities
export function searchAndFormatResults(query: string) {
  // Don't mix API calls with formatting
  const results = api.search(query);
  return results.map(r => ({ ...r, formatted: formatResult(r) }));
}
```

### **2. DRY Principle (Don't Repeat Yourself)**

#### ✅ DO: Extract common patterns
```typescript
// ✅ Good: Reusable API client
export class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    // Common error handling, auth, etc.
  }
  
  async search(query: SearchQuery): Promise<SearchResponse> {
    return this.request('/api/search', { method: 'POST', body: JSON.stringify(query) });
  }
}
```

#### ❌ DON'T: Duplicate API logic
```typescript
// ❌ Bad: Repeated fetch logic
export async function searchLogs(query: string) {
  const response = await fetch('/api/search', { /* auth headers, error handling */ });
  // Duplicated logic
}

export async function searchMetrics(query: string) {
  const response = await fetch('/api/search', { /* same auth headers, error handling */ });
  // Duplicated logic
}
```

## Async/Await Standards

### **1. Consistent Async Patterns**

#### ✅ DO: Use async/await consistently
```typescript
// ✅ Good: Clear async pattern
export async function fetchUserData(userId: string): Promise<User> {
  try {
    const response = await apiClient.get(`/users/${userId}`);
    return response.data;
  } catch (error) {
    logger.error('Failed to fetch user data', { userId, error });
    throw new UserFetchError(`Failed to fetch user ${userId}`);
  }
}
```

#### ❌ DON'T: Mix promises and async/await
```typescript
// ❌ Bad: Inconsistent async handling
export async function fetchUserData(userId: string) {
  return apiClient.get(`/users/${userId}`)
    .then(response => response.data)
    .catch(error => {
      // Don't mix .then/.catch with async/await
    });
}
```

### **2. Error Handling Patterns**

#### ✅ DO: Consistent error handling
```python
# ✅ Good: Structured error handling
async def get_search_results(query: SearchQuery, user: User) -> SearchResponse:
    try:
        # Validate input
        if not query.freeText.strip():
            raise ValidationError("Search query cannot be empty")
        
        # Check permissions
        if not await rbac.can_search(user, query.type):
            raise PermissionError(f"User cannot search {query.type}")
        
        # Perform search
        results = await search_service.search(query)
        return SearchResponse(items=results.items, stats=results.stats)
        
    except ValidationError:
        raise  # Re-raise validation errors
    except PermissionError:
        raise  # Re-raise permission errors
    except Exception as e:
        logger.error(f"Search failed: {e}", extra={"query": query, "user_id": user.id})
        raise SearchError("Search operation failed") from e
```

## Component Design Patterns

### **1. React Component Standards**

#### ✅ DO: Proper component structure
```typescript
// ✅ Good: Well-structured component
interface SearchResultsProps {
  results: SearchResult[];
  loading: boolean;
  onResultClick: (result: SearchResult) => void;
  className?: string;
}

export function SearchResults({ 
  results, 
  loading, 
  onResultClick, 
  className 
}: SearchResultsProps) {
  // Early returns for loading/empty states
  if (loading) {
    return <SearchResultsSkeleton />;
  }
  
  if (results.length === 0) {
    return <EmptySearchResults />;
  }
  
  return (
    <div className={cn("search-results", className)}>
      {results.map(result => (
        <SearchResultCard
          key={result.id}
          result={result}
          onClick={() => onResultClick(result)}
        />
      ))}
    </div>
  );
}
```

#### ❌ DON'T: Monolithic components
```typescript
// ❌ Bad: Too many responsibilities
export function SearchPage() {
  // Don't put all logic in one component
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);
  const [alerts, setAlerts] = useState([]);
  // ... 50 more lines of mixed concerns
}
```

### **2. Custom Hooks Pattern**

#### ✅ DO: Extract reusable logic
```typescript
// ✅ Good: Reusable search hook
export function useSearch() {
  const [state, setState] = useState<SearchState>({
    results: [],
    loading: false,
    error: null
  });
  
  const search = useCallback(async (query: SearchQuery) => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      const results = await searchService.search(query);
      setState({ results, loading: false, error: null });
    } catch (error) {
      setState(prev => ({ ...prev, loading: false, error }));
    }
  }, []);
  
  return { ...state, search };
}
```

## API Design Standards

### **1. FastAPI Endpoint Patterns**

#### ✅ DO: Consistent endpoint structure
```python
# ✅ Good: Well-structured endpoint
@router.post("/search", response_model=SearchResponse)
async def search_unified(
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Perform unified search across logs, metrics, and traces.
    
    Args:
        query: Search parameters with filters and time range
        current_user: Authenticated user for tenant isolation
        search_service: Injected search service dependency
        
    Returns:
        SearchResponse with results, stats, and facets
        
    Raises:
        HTTPException: 400 for invalid query, 403 for permissions
    """
    # Validate tenant access
    await rbac.ensure_tenant_access(current_user, query.tenant_id)
    
    # Perform search with tenant context
    results = await search_service.search(query, current_user.tenant_id)
    
    return SearchResponse(
        items=results.items,
        stats=results.stats,
        facets=results.facets
    )
```

### **2. Service Layer Patterns**

#### ✅ DO: Clean service interfaces
```python
# ✅ Good: Clear service interface
class SearchService:
    def __init__(self, loki_client: LokiClient, prometheus_client: PrometheusClient):
        self.loki = loki_client
        self.prometheus = prometheus_client
    
    async def search(self, query: SearchQuery, tenant_id: str) -> SearchResults:
        """Search across all data sources with tenant isolation."""
        
        # Route to appropriate search method
        if query.type == "logs":
            return await self._search_logs(query, tenant_id)
        elif query.type == "metrics":
            return await self._search_metrics(query, tenant_id)
        else:
            return await self._search_unified(query, tenant_id)
    
    async def _search_logs(self, query: SearchQuery, tenant_id: str) -> SearchResults:
        # Tenant-isolated log search
        pass
```

## Error Handling Standards

### **1. Custom Exception Hierarchy**

#### ✅ DO: Structured exception hierarchy
```python
# ✅ Good: Clear exception hierarchy
class ObservaStackError(Exception):
    """Base exception for ObservaStack."""
    pass

class AuthenticationError(ObservaStackError):
    """Authentication related errors."""
    pass

class AuthorizationError(ObservaStackError):
    """Authorization/permission related errors."""
    pass

class SearchError(ObservaStackError):
    """Search operation errors."""
    pass

class TenantIsolationError(AuthorizationError):
    """Tenant isolation violation errors."""
    pass
```

### **2. Frontend Error Handling**

#### ✅ DO: Consistent error handling
```typescript
// ✅ Good: Structured error handling
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function handleApiCall<T>(
  apiCall: () => Promise<T>
): Promise<T> {
  try {
    return await apiCall();
  } catch (error) {
    if (error instanceof ApiError) {
      // Handle known API errors
      throw error;
    }
    
    // Handle unknown errors
    logger.error('Unexpected API error', error);
    throw new ApiError('An unexpected error occurred', 500);
  }
}
```

## Testing Standards

### **1. Test Organization**

#### ✅ DO: Organized test structure
```typescript
// ✅ Good: Clear test organization
describe('SearchService', () => {
  describe('search method', () => {
    it('should return results for valid query', async () => {
      // Arrange
      const query = createMockSearchQuery();
      const expectedResults = createMockSearchResults();
      
      // Act
      const results = await searchService.search(query);
      
      // Assert
      expect(results).toEqual(expectedResults);
    });
    
    it('should throw error for invalid tenant', async () => {
      // Arrange
      const query = createMockSearchQuery({ tenantId: 'invalid' });
      
      // Act & Assert
      await expect(searchService.search(query))
        .rejects
        .toThrow(TenantIsolationError);
    });
  });
});
```

## Performance Standards

### **1. React Performance**

#### ✅ DO: Optimize re-renders
```typescript
// ✅ Good: Memoized components
export const SearchResultCard = memo(function SearchResultCard({ 
  result, 
  onClick 
}: SearchResultCardProps) {
  const handleClick = useCallback(() => {
    onClick(result);
  }, [result, onClick]);
  
  return (
    <div onClick={handleClick}>
      {result.title}
    </div>
  );
});
```

### **2. Database Query Patterns**

#### ✅ DO: Efficient queries
```python
# ✅ Good: Efficient database queries
async def get_user_alerts(user_id: str, limit: int = 50) -> List[Alert]:
    """Get user alerts with proper indexing and limits."""
    query = """
    SELECT * FROM alerts 
    WHERE tenant_id = :tenant_id 
    AND status IN ('active', 'acknowledged')
    ORDER BY created_at DESC 
    LIMIT :limit
    """
    
    return await database.fetch_all(
        query, 
        values={"tenant_id": user.tenant_id, "limit": limit}
    )
```

## Code Review Checklist

### **Before Submitting Code**
- [ ] **No code duplication**: Check for repeated patterns
- [ ] **Single responsibility**: Each function/class has one job
- [ ] **Consistent naming**: Follows project conventions
- [ ] **Error handling**: Proper try/catch and error types
- [ ] **Type safety**: Full TypeScript/Python typing
- [ ] **Documentation**: All public APIs documented
- [ ] **Tests**: Unit tests for new functionality
- [ ] **Performance**: No obvious performance issues

### **Architecture Compliance**
- [ ] **Directory structure**: Files in correct locations
- [ ] **Import patterns**: No circular dependencies
- [ ] **Service boundaries**: Clear separation of concerns
- [ ] **Tenant isolation**: Multi-tenant patterns followed
- [ ] **Security**: No security vulnerabilities

## Enforcement

These standards are MANDATORY for all code contributions. Code that doesn't follow these standards will be rejected and must be refactored before acceptance.

**Remember**: Consistency is more important than personal preference. Follow the established patterns even if you prefer a different approach.