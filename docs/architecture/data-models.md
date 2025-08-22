# Data Models

The following data models represent the core entities of the Obstack platform. They are defined here as TypeScript interfaces, which will be shared between the frontend and backend to ensure end-to-end type safety. The backend will use Pydantic models that are structurally identical to these interfaces.

## Tenant

Represents a customer in the system, providing the primary boundary for data isolation.

**Purpose**: To define a customer's subscription, features, and serve as the root for all tenant-specific data.

**TypeScript Interface (`packages/shared-types/src/tenant.ts`)**
```typescript
export interface Tenant {
  id: string;
  keycloak_realm_id?: string; // Optional as Community tier might not have one
  name: string;
  subscription_plan: 'community' | 'saas' | 'enterprise';
  is_active: boolean;
  created_at: string; // ISO 8601 date string
  updated_at: string; // ISO 8601 date string
}
```

## User

Represents an individual user within a specific tenant.

**Purpose**: To manage user identity, roles, and application-specific settings.

**TypeScript Interface (`packages/shared-types/src/user.ts`)**
```typescript
export interface User {
  id: string;
  keycloak_user_id?: string; // Optional as Community tier uses local auth
  tenant_id: string;
  email: string;
  roles: ('admin' | 'viewer' | string)[]; // Allows for custom roles
  created_at: string; // ISO 8601 date string
}
```

## Alert

Represents a single alert ingested from an external system like Prometheus Alertmanager.

**Purpose**: To provide a structured format for all alerts within the unified alert management system.

**TypeScript Interface (`packages/shared-types/src/alert.ts`)**
```typescript
export type AlertStatus = 'active' | 'acknowledged' | 'resolved';
export type AlertSeverity = 'critical' | 'high' | 'warning' | 'info';

export interface Alert {
  id: string;
  tenant_id: string;
  status: AlertStatus;
  severity: AlertSeverity;
  title: string;
  description: string;
  source: string;
  labels: Record<string, string>;
  created_at: string; // ISO 8601 date string
}
```
