# Story 2.2: Session Management and Protected Routes

## Status
- Approved

## Story
- **As a** logged-in user,
- **I want** the application to keep me logged in and protect sensitive areas,
- **so that** I have a secure and seamless user experience.

## Acceptance Criteria
1.  The frontend securely stores the received JWT (e.g., in a secure, HttpOnly cookie).
2.  The JWT is automatically sent in the `Authorization` header for all subsequent API requests.
3.  The backend includes middleware that validates the JWT on protected endpoints and rejects requests with invalid or missing tokens.
4.  The frontend implements "protected route" logic, redirecting unauthenticated users from dashboards back to the login page.
5.  A "Logout" button is available that clears the JWT and redirects to the login page.

## Tasks / Subtasks
- [ ] Task 1: Implement secure JWT storage on the frontend (HttpOnly cookie). (AC: #1)
- [ ] Task 2: Ensure the JWT is sent automatically in API request headers. (AC: #2)
- [ ] Task 3: Develop backend middleware to validate JWTs on protected endpoints. (AC: #3)
- [ ] Task 4: Implement frontend protected route logic to redirect unauthenticated users. (AC: #4)
- [ ] Task 5: Create a logout button that clears the session and redirects. (AC: #5)

## Dev Notes
- **Dependency:** This story builds on **Story 2.1**.
- **Backend:** The JWT validation middleware should be added to the FastAPI application in `apps/backend/app/core/security.py`. It should decode the token using the shared secret and check for expiration.
- **Frontend:**
    - For secure JWT storage, the backend should set an `HttpOnly` cookie upon login. The frontend will not need to store the token manually in local storage.
    - Protected routes can be implemented using a wrapper component that checks for the user's authentication status (e.g., by calling a `/users/me` endpoint).
    - The logout button should call a backend endpoint (e.g., `/api/v1/auth/logout`) that clears the `HttpOnly` cookie.

### Testing
- **Backend:**
    - Write integration tests for the JWT middleware. Test scenarios should include requests with a valid token, an invalid/expired token, and no token.
- **Frontend:**
    - Write component tests to verify that a user is redirected from a protected route if they are not authenticated.
    - Test the logout functionality to ensure the user is redirected to the login page.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 2. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
