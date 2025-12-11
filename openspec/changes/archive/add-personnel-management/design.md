# Design Notes

## Role Hierarchy
- `superadmin`: Full access to all modules (search, upload, personnel management).
- `admin`: Access to search and document management only.
- `normal`: Access to search only.

## Key Decisions
- Root user defaults to `superadmin` role on initialization.
- Existing users with `admin` role retain document management access.
- Superadmins cannot modify their own role to prevent accidental lockout.
- Registration approval moved entirely to PersonnelPage; UploadPage focuses on document operations.

## API Design
- `GET /admin/users`: Returns all users (superadmin only).
- `PUT /admin/users/{user_id}/role`: Updates user role (superadmin only).
- `require_admin` now accepts both `admin` and `superadmin`.
