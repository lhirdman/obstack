# REST API Specification

The Obstack API is a RESTful service built with FastAPI. The specification follows the OpenAPI 3.0 standard. Documentation will be automatically generated and served by the backend at the /api/docs endpoint, rendered with Redocly. All endpoints are prefixed with /api/v1 and require a valid JWT for access, unless otherwise specified.

## REST API Specification (Initial Draft)
```yaml
openapi: 3.0.3
info:
  title: Obstack API
  version: 1.0.0
  description: The official REST API for the Obstack platform. Provides unified access to observability data, cost monitoring, and platform management.
servers:
  - url: /api/v1
    description: API Server

paths:
  /health:
    get:
      summary: Health Check
      description: Provides a simple health check of the API server. Does not require authentication.
      tags:
        - General
      responses:
        '200':
          description: API is healthy.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"

  /auth/register:
    post:
      summary: User Registration (Local Auth)
      description: Allows a new user to register for an account in the Community (self-hosted) edition. This endpoint is only available when `AUTH_METHOD=local`.
      tags:
        - Authentication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserRegistration'
      responses:
        '201':
          description: User successfully created.
        '400':
          description: Invalid input or user already exists.

  /auth/login:
    post:
      summary: User Login (Local Auth)
      description: Authenticates a user with email and password to get a JWT. This endpoint is only available when `AUTH_METHOD=local`.
      tags:
        - Authentication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserLogin'
      responses:
        '200':
          description: Login successful. Returns a JWT.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthToken'
        '401':
          description: Invalid credentials.

components:
  schemas:
    UserRegistration:
      type: object
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          format: password
        tenant_name:
          type: string
      required:
        - email
        - password
        - tenant_name

    UserLogin:
      type: object
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          format: password
      required:
        - email
        - password

    AuthToken:
      type: object
      properties:
        access_token:
          type: string
        token_type:
          type: string
          example: "bearer"
```
