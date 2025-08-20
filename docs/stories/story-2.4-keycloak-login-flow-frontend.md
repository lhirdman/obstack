# Story 2.4: Keycloak Login Flow Frontend

## Status
- Approved

## Story
- **As an** Enterprise user,
- **I want** to be redirected to my company's login page (via Keycloak) to authenticate,
- **so that** I can use my standard corporate credentials to access the platform.

## Acceptance Criteria
1.  When `AUTH_METHOD` is set to `keycloak`, the frontend login page redirects the user to the Keycloak login screen.
2.  After successful authentication with Keycloak, the user is redirected back to the application.
3.  The frontend correctly receives and stores the JWT issued by Keycloak.
4.  The user is successfully logged in and can access protected routes.

## Tasks / Subtasks
- [ ] Task 1: When `AUTH_METHOD` is `keycloak`, redirect the user from the login page to the Keycloak login screen. (AC: #1)
- [ ] Task 2: Handle the redirect back from Keycloak after successful authentication. (AC: #2)
- [ ] Task 3: Correctly receive and store the JWT issued by Keycloak. (AC: #3)
- [ ] Task 4: Ensure the user is logged in and can access protected routes post-authentication. (AC: #4)

## Dev Notes
- **[Enterprise]** This is an enterprise-level feature.
- The frontend will need a configuration service to read the `AUTH_METHOD` and the Keycloak instance details (URL, realm, client ID).
- Use a library like `keycloak-js` or a generic OIDC client library to handle the redirect-based login flow.
- The redirect URI will need to be configured and allowed in the Keycloak client settings.
- Upon successful redirect, the library will handle parsing the token from the URL fragment.

### Testing
- E2E tests using **Playwright** are essential for this story.
- The E2E test will need to:
    - Navigate to the login page.
    - Verify the redirect to the Keycloak login page.
    - Programmatically log in to Keycloak (this may require a separate test user in the Keycloak container).
    - Verify the redirect back to the application.
    - Confirm that the user is logged in and can access a protected route.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 2. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
