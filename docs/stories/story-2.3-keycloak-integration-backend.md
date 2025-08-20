# Story 2.3: Keycloak Integration Backend

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** to integrate the backend with Keycloak for OIDC-based authentication,
- **so that** we can support Enterprise customers with SSO requirements.

## Acceptance Criteria
1.  The backend can be configured (via environment variable `AUTH_METHOD=keycloak`) to use Keycloak for authentication.
2.  When configured, the backend validates JWTs issued by a configured Keycloak instance.
3.  The backend correctly extracts user information, roles, and tenant data from the Keycloak JWT claims.
4.  The system can map Keycloak roles to internal application roles.
5.  The implementation is documented in the developer guide on the Docusaurus site.

## Tasks / Subtasks
- [ ] Task 1: Implement configuration to switch auth method to `keycloak`. (AC: #1)
- [ ] Task 2: Develop logic to validate JWTs issued by the Keycloak instance. (AC: #2)
- [ ] Task 3: Implement extraction of user info, roles, and tenant data from JWT claims. (AC: #3)
- [ ] Task 4: Create a mapping system for Keycloak roles to internal application roles. (AC: #4)
- [ ] Task 5: Document the Keycloak backend integration in the Docusaurus developer guide. (AC: #5)

## Dev Notes
- **[Enterprise]** This is an enterprise-level feature.
- The auth method switching logic should be handled in `apps/backend/app/core/config.py`.
- Use a library like `python-jose` to decode and validate the OIDC JWTs from Keycloak.
- The backend will need to fetch the public keys from the Keycloak instance's JWKS URI to validate the token signature.
- A new service in `apps/backend/app/services/` should be created to handle the claims mapping logic.

### Testing
- Integration tests are critical for this story.
- The test setup should include a running Keycloak container.
- Tests should cover:
    - Successful validation of a valid Keycloak JWT.
    - Rejection of an invalid or expired JWT.
    - Correct extraction and mapping of user roles and tenant information.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 2. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
