# Contributing

We welcome contributions to ObservaStack! This guide will help you get started with contributing code, documentation, and other improvements.

## Getting Started

### Prerequisites

- **Git**: Version control system
- **Docker**: For running the development environment
- **Node.js**: 18+ for frontend development
- **Python**: 3.12+ for backend development
- **GitHub Account**: For submitting pull requests

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/observastack.git
   cd observastack
   ```

3. **Set up the development environment**:
   ```bash
   cd docker
   docker compose --profile init up mc && docker compose --profile init down
   docker compose up -d
   ```

4. **Install frontend dependencies**:
   ```bash
   cd observastack-app/frontend
   npm install
   npm start
   ```

5. **Set up backend development**:
   ```bash
   cd observastack-app/bff
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

## Development Workflow

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature development branches
- **bugfix/**: Bug fix branches
- **hotfix/**: Critical production fixes

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### Making Changes

1. **Write code** following our coding standards
2. **Add tests** for new functionality
3. **Update documentation** as needed
4. **Run tests** to ensure everything works
5. **Commit changes** with descriptive messages

### Commit Message Format

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```
feat(search): add unified search across data sources
fix(auth): resolve JWT token validation issue
docs(api): update authentication documentation
test(alerts): add unit tests for alert service
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `style`: Code style changes
- `chore`: Maintenance tasks

## Code Standards

### Frontend (React/TypeScript)

#### File Structure
```
src/
├── components/     # Reusable components
├── views/         # Page components
├── hooks/         # Custom hooks
├── services/      # API services
├── types/         # TypeScript types
└── utils/         # Utility functions
```

#### Naming Conventions
- **Components**: PascalCase (`SearchResults.tsx`)
- **Files**: kebab-case (`search-results.tsx`)
- **Functions**: camelCase (`handleSearch`)
- **Constants**: SCREAMING_SNAKE_CASE (`API_BASE_URL`)

#### Code Style
```typescript
// ✅ Good
interface SearchResultsProps {
  results: SearchResult[];
  loading: boolean;
  onResultClick: (result: SearchResult) => void;
}

export function SearchResults({ results, loading, onResultClick }: SearchResultsProps) {
  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="search-results">
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

### Backend (Python/FastAPI)

#### File Structure
```
app/
├── api/           # API routes
├── auth/          # Authentication
├── models/        # Pydantic models
├── services/      # Business logic
├── core/          # Configuration
└── utils/         # Utilities
```

#### Naming Conventions
- **Files**: snake_case (`search_service.py`)
- **Classes**: PascalCase (`SearchService`)
- **Functions**: snake_case (`get_search_results`)
- **Constants**: SCREAMING_SNAKE_CASE (`DATABASE_URL`)

#### Code Style
```python
# ✅ Good
from typing import List, Optional
from pydantic import BaseModel

class SearchQuery(BaseModel):
    free_text: str
    type: str
    time_range: TimeRange
    filters: Optional[dict] = None

class SearchService:
    def __init__(self, loki_client: LokiClient):
        self.loki = loki_client
    
    async def search(self, query: SearchQuery, tenant_id: str) -> SearchResults:
        """Search across data sources with tenant isolation."""
        if not query.free_text.strip():
            raise ValueError("Search query cannot be empty")
        
        results = await self.loki.query(query, tenant_id)
        return SearchResults(items=results)
```

## Testing

### Frontend Testing

#### Unit Tests (Vitest)
```typescript
// search-results.test.tsx
import { render, screen } from '@testing-library/react';
import { SearchResults } from './SearchResults';

describe('SearchResults', () => {
  it('displays loading spinner when loading', () => {
    render(<SearchResults results={[]} loading={true} onResultClick={vi.fn()} />);
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays results when loaded', () => {
    const results = [{ id: '1', message: 'Test log' }];
    render(<SearchResults results={results} loading={false} onResultClick={vi.fn()} />);
    expect(screen.getByText('Test log')).toBeInTheDocument();
  });
});
```

#### E2E Tests (Playwright)
```typescript
// search.spec.ts
import { test, expect } from '@playwright/test';

test('search functionality', async ({ page }) => {
  await page.goto('/search');
  
  await page.fill('[data-testid="search-input"]', 'error');
  await page.click('[data-testid="search-button"]');
  
  await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
});
```

### Backend Testing

#### Unit Tests (pytest)
```python
# test_search_service.py
import pytest
from app.services.search_service import SearchService
from app.models.search import SearchQuery, TimeRange

@pytest.fixture
def search_service():
    return SearchService(mock_loki_client)

@pytest.mark.asyncio
async def test_search_with_valid_query(search_service):
    query = SearchQuery(
        free_text="error",
        type="logs",
        time_range=TimeRange(start="2025-08-16T00:00:00Z", end="2025-08-16T23:59:59Z")
    )
    
    results = await search_service.search(query, "tenant-123")
    
    assert len(results.items) > 0
    assert results.items[0].message is not None

@pytest.mark.asyncio
async def test_search_with_empty_query_raises_error(search_service):
    query = SearchQuery(free_text="", type="logs", time_range=TimeRange(...))
    
    with pytest.raises(ValueError, match="Search query cannot be empty"):
        await search_service.search(query, "tenant-123")
```

### Running Tests

```bash
# Frontend tests
cd observastack-app/frontend
npm test                    # Unit tests
npm run test:e2e           # E2E tests

# Backend tests
cd observastack-app/bff
pytest                     # All tests
pytest -v tests/services/  # Specific directory
pytest -k "test_search"    # Specific test pattern
```

## Documentation

### Writing Documentation

- **Use clear, concise language**
- **Include code examples** for all features
- **Add screenshots** for UI features
- **Keep documentation up-to-date** with code changes

### Documentation Structure

```
docs/
├── getting-started/    # Installation and setup
├── user-guide/        # User documentation
├── developer-guide/   # Developer documentation
├── deployment/        # Deployment guides
└── troubleshooting/   # Troubleshooting guides
```

### Building Documentation

```bash
cd docs
npm install
npm start              # Development server
npm run build         # Production build
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   # Frontend
   npm test
   npm run lint
   npm run type-check
   
   # Backend
   pytest
   ruff check .
   mypy .
   ```

2. **Update documentation** if needed
3. **Add changelog entry** if applicable
4. **Rebase on latest develop** branch

### Submitting a Pull Request

1. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a pull request** on GitHub:
   - Use a descriptive title
   - Fill out the PR template
   - Link related issues
   - Add screenshots for UI changes

3. **Address review feedback**:
   - Make requested changes
   - Push updates to the same branch
   - Respond to comments

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Screenshots
(If applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Code Review Guidelines

### For Authors

- **Keep PRs small** and focused
- **Write clear descriptions** of changes
- **Respond promptly** to feedback
- **Test thoroughly** before submitting

### For Reviewers

- **Be constructive** and helpful
- **Focus on code quality** and maintainability
- **Check for security issues**
- **Verify tests are adequate**

### Review Checklist

- [ ] Code follows project standards
- [ ] Tests are comprehensive
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Workflow

1. **Create release branch** from develop
2. **Update version numbers** in relevant files
3. **Update CHANGELOG.md** with release notes
4. **Create release PR** to main branch
5. **Tag release** after merge
6. **Deploy to production**

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be respectful** and professional
- **Welcome newcomers** and help them get started
- **Focus on constructive feedback**
- **Respect different viewpoints** and experiences

### Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Discord**: For real-time chat and community support
- **Documentation**: Check existing docs first

### Reporting Issues

When reporting bugs:

1. **Search existing issues** first
2. **Use the issue template**
3. **Provide reproduction steps**
4. **Include system information**
5. **Add relevant logs** and screenshots

## Recognition

Contributors are recognized in several ways:

- **Contributors list** in README
- **Release notes** mention significant contributions
- **Community highlights** in blog posts
- **Contributor badges** on GitHub

## Next Steps

- **Join our Discord** for community discussions
- **Check the roadmap** for upcoming features
- **Look at "good first issue"** labels for beginner-friendly tasks
- **Read the architecture guide** to understand the codebase