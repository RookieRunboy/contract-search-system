# Personnel Management Spec

## ADDED Requirements

### Requirement: Three-tier role system
The system shall support three user roles: `superadmin`, `admin`, and `normal`.

#### Scenario: Role-based menu visibility
Given a logged-in user
When the user views the sidebar menu
Then the menu items visible shall depend on the user's role:
- `superadmin`: Document Search, Document Management, Personnel Management
- `admin`: Document Search, Document Management
- `normal`: Document Search only

---

### Requirement: User listing for superadmins
The system shall provide an API endpoint to list all users.

#### Scenario: Superadmin fetches user list
Given a user with role `superadmin`
When the user calls `GET /admin/users`
Then the response shall contain all registered users with their ID, role, status, and creation timestamp

#### Scenario: Non-superadmin denied access
Given a user with role `admin` or `normal`
When the user calls `GET /admin/users`
Then the response shall be 403 Forbidden

---

### Requirement: Role modification by superadmins
The system shall allow superadmins to change any user's role.

#### Scenario: Superadmin changes user role
Given a user with role `superadmin`
When the user calls `PUT /admin/users/{user_id}/role` with a valid role
Then the target user's role shall be updated

#### Scenario: Superadmin cannot modify own role
Given a user with role `superadmin`
When the user attempts to modify their own role via the UI
Then the modification button shall be disabled

---

## MODIFIED Requirements

### Requirement: Admin permission check
The `require_admin` dependency shall accept both `admin` and `superadmin` roles.

#### Scenario: Superadmin access to admin endpoints
Given a user with role `superadmin`
When the user calls an endpoint protected by `require_admin`
Then access shall be granted
