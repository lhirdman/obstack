# Coding Standards

This document outlines the mandatory coding standards and best practices for the Obstack project. Adherence to these standards is critical for maintaining code quality, readability, and maintainability.

## General Principles

-   **Clarity over Cleverness**: Write code that is easy for other developers to understand.
-   **DRY (Don't Repeat Yourself)**: Abstract and reuse common patterns and logic.
-   **Single Responsibility Principle**: Each function, class, and module should have one well-defined responsibility.
-   **Consistency**: Adhere to the established patterns and styles outlined in this document.

## Naming Conventions

### TypeScript / React (`apps/frontend`)

-   **Files**: Use `kebab-case.ts` for utilities and services. Use `PascalCase.tsx` for React components.
-   **Components**: `PascalCase` (e.g., `AlertCard`, `SearchResults`).
-   **Functions/Variables**: `camelCase` (e.g., `handleSearch`, `formatDate`).
-   **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `API_BASE_URL`).
-   **Types/Interfaces**: `PascalCase` (e.g., `SearchQuery`, `UserProfile`).

### Python / FastAPI (`apps/backend`)

-   **Files**: `snake_case.py`.
-   **Classes**: `PascalCase` (e.g., `UserService`, `AlertManager`).
-   **Functions/Variables**: `snake_case` (e.g., `get_current_user`, `process_alert`).
-   **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `DATABASE_URL`).
-   **Private Methods/Attributes**: Start with an underscore `_` (e.g., `_validate_token`).

## Code Style & Formatting

-   **Automation is Key**: Formatting is enforced automatically by Prettier (for TypeScript/JSON/YAML) and Ruff (for Python). All developers must use these tools.
-   **Line Length**: Maximum 120 characters.
-   **Imports**: Group and sort imports. Use absolute imports for modules within the application.

## Code-Level Documentation

-   **TypeScript/React**: Use **JSDoc** comments for all exported functions, classes, and complex types. This is especially important for reusable components and hooks.
-   **Python/FastAPI**: Use **Google-style docstrings** for all public modules, functions, classes, and methods.

## Component Design (React)

-   **Functional Components**: Use function components with hooks exclusively. Class components are not permitted.
-   **Props**: Use TypeScript interfaces for prop definitions. Keep prop interfaces specific and clear.
-   **State Management**: For server state, use TanStack Query. For global UI state, use React Context.
-   **Custom Hooks**: Extract any reusable, non-trivial logic into custom hooks (e.g., `useSearch`, `useAuth`).

## API Design (FastAPI)

-   **Dependency Injection**: Use FastAPI's `Depends` system to inject services and dependencies into API endpoints.
-   **Pydantic Models**: Define explicit Pydantic models for all request bodies and responses to ensure data validation.
-   **Service Layer**: Keep API endpoints thin. All business logic should reside in a separate service layer.

### 5. Error Handling

**Rule:** API endpoints (`apps/backend/app/api/`) MUST NOT implement generic `try...except Exception` blocks for the purpose of catching unexpected errors and returning a 500 response.

**Rationale:** The backend application has a centralized error handling middleware (`app/core/error_handling.py`) that automatically catches all unhandled exceptions. This middleware ensures that all unexpected errors are logged consistently and return a standardized JSON error response.

**Correct Usage:**

-   **DO NOT** wrap your entire endpoint logic in a generic `try...except`.
-   **DO** allow unexpected exceptions to propagate up to the middleware.
-   **DO** use specific `try...except` blocks only for *expected* exceptions that require unique business logic (e.g., catching a `KeyError` to return a `404 Not Found` instead of a generic `500`).

**Example:**

**WRONG:**
```python
@router.post("/query")
async def query_metrics(request: MetricsQueryRequest):
    try:
        # business logic...
        result = await metrics_service.query(...)
        return result
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

**CORRECT:**
```python
@router.post("/query")
async def query_metrics(request: MetricsQueryRequest):
    # Let the middleware handle unexpected errors.
    # The code is cleaner and focuses on the success path.
    result = await metrics_service.query(...)
    return result
```

## Testing

-   **Test Organization**: Tests should be co-located with the code they are testing (e.g., `my-component.test.tsx` next to `my-component.tsx`).
-   **Unit Tests**: Focus on testing a single unit (function, component) in isolation. Mock all external dependencies.
-   **Integration Tests**: Test the interaction between several components (e.g., an API endpoint and its service).
-   **E2E Tests**: Test critical user workflows from end-to-end in a browser environment.
-   **Coverage**: While not a strict metric, all new features must be accompanied by meaningful tests.

## Enforcement

These standards are enforced through automated tooling:
-   **Linting**: ESLint (TypeScript) and Ruff (Python) will run in CI.
-   **Formatting**: Prettier and Ruff formatters will run in CI.
-   **Type Checking**: `tsc --noEmit` and `mypy` will run in CI.

Pull requests that fail these checks will be blocked from merging until they are fixed.
