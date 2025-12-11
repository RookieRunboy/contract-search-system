# Change Proposal: Personnel Management Module

## Summary
- Add a new Personnel Management page for superadmin users to manage user registrations and roles.
- Introduce a three-tier role system: superadmin, admin, normal.
- Move registration approval from UploadPage to the new PersonnelPage.

## Motivation
- Centralize user management in a dedicated module for better separation of concerns.
- Enable finer-grained permission control with superadmin role.
- Allow superadmins to modify user roles without direct database access.

## Scope
- Backend: Add new API endpoints for user listing and role management.
- Frontend: Create PersonnelPage, update routing and permission logic.

## Out of Scope
- OAuth/SAML integration.
- Multi-factor authentication.
- Password reset functionality.
