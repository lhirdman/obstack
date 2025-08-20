# Story 2.1: Local User Registration and Login

## Status
- Approved

## Story
- **As a** new user of the self-hosted Community edition,
- **I want** to be able to register an account and log in with a username and password,
- **so that** I can access the platform securely.

## Acceptance Criteria
1.  The backend provides API endpoints for user registration (`/api/v1/auth/register`) and login (`/api/v1/auth/login`).
2.  Passwords are securely hashed and salted before being stored in the PostgreSQL `users` table.
3.  Upon successful login, the backend returns a signed JWT containing the `user_id`, `tenant_id`, and `roles`.
4.  The frontend provides a clean UI for registration and login forms.
5.  All API documentation is updated in Redocly.

## Tasks / Subtasks
- [ ] Task 1: Implement backend API endpoints for registration and login. (AC: #1)
- [ ] Task 2: Ensure passwords are securely hashed and salted. (AC: #2)
- [ ] Task 3: Implement JWT generation upon successful login. (AC: #3)
- [ ] Task 4: Develop the frontend UI for registration and login forms. (AC: #4)
- [ ] Task 5: Update the Redocly API documentation. (AC: #5)

## Dev Notes
- **Dependency:** This story depends on **Story 1.4** for the database schema.
- The new auth endpoints should be located in `apps/backend/app/api/v1/auth.py`.
- Use a strong hashing algorithm like **bcrypt** for password storage.
- JWTs should be signed using a secret key read from environment variables.
- The frontend forms should be created as new components in `apps/frontend/src/components/auth/`.
- Use **TanStack Query** for handling the form submission and state management on the frontend.

### Testing
- **Backend:**
    - Create integration tests for the `/register` and `/login` endpoints.
    - Tests should verify correct user creation, password hashing, and JWT generation.
    - Tests should also cover error cases like duplicate usernames or incorrect login credentials.
- **Frontend:**
    - Create component tests for the registration and login forms using **Vitest** and **React Testing Library**.
    - Tests should validate form inputs and user interactions.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 2. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
