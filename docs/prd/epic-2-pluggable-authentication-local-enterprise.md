# Epic 2: Pluggable Authentication (Local & Enterprise)

**Epic Goal:** To build a robust and flexible authentication system that supports both the open-source Community edition (local accounts) and the commercial Enterprise tier (SSO/SAML via Keycloak). The system will be designed to be "pluggable," allowing the authentication method to be selected via configuration.

## Stories for Epic 2

**Story 2.1: `[Community]` Local User Registration and Login**
*   **As a** new user of the self-hosted Community edition,
*   **I want** to be able to register an account and log in with a username and password,
*   **so that** I can access the platform securely.
*   **Acceptance Criteria:**
    1.  The backend provides API endpoints for user registration (`/api/v1/auth/register`) and login (`/api/v1/auth/login`).
    2.  Passwords are securely hashed and salted before being stored in the PostgreSQL `users` table.
    3.  Upon successful login, the backend returns a signed JWT containing the `user_id`, `tenant_id`, and `roles`.
    4.  The frontend provides a clean UI for registration and login forms.
    5.  All API documentation is updated in Redocly.

**Story 2.2: `[Community]` Session Management and Protected Routes**
*   **As a** logged-in user,
*   **I want** the application to keep me logged in and protect sensitive areas,
*   **so that** I have a secure and seamless user experience.
*   **Acceptance Criteria:**
    1.  The frontend securely stores the received JWT (e.g., in a secure cookie or local storage).
    2.  The JWT is automatically sent in the `Authorization` header for all subsequent API requests.
    3.  The backend includes middleware that validates the JWT on protected endpoints and rejects requests with invalid or missing tokens.
    4.  The frontend implements "protected route" logic, redirecting unauthenticated users from dashboards back to the login page.
    5.  A "Logout" button is available that clears the JWT and redirects to the login page.

**Story 2.3: `[Enterprise]` Keycloak Integration Backend**
*   **As a** Backend Developer,
*   **I want** to integrate the backend with Keycloak for OIDC-based authentication,
*   **so that** we can support Enterprise customers with SSO requirements.
*   **Acceptance Criteria:**
    1.  The backend can be configured (via environment variable `AUTH_METHOD=keycloak`) to use Keycloak for authentication.
    2.  When configured, the backend validates JWTs issued by a configured Keycloak instance.
    3.  The backend correctly extracts user information, roles, and tenant data from the Keycloak JWT claims.
    4.  The system can map Keycloak roles to internal application roles.
    5.  The implementation is documented in the developer guide on the Docusaurus site.

**Story 2.4: `[Enterprise]` Keycloak Login Flow Frontend**
*   **As an** Enterprise user,
*   **I want** to be redirected to my company's login page (via Keycloak) to authenticate,
*   **so that** I can use my standard corporate credentials to access the platform.
*   **Acceptance Criteria:**
    1.  When `AUTH_METHOD` is set to `keycloak`, the frontend login page redirects the user to the Keycloak login screen.
    2.  After successful authentication with Keycloak, the user is redirected back to the application.
    3.  The frontend correctly receives and stores the JWT issued by Keycloak.
    4.  The user is successfully logged in and can access protected routes.
