# Tasks

- [x] Extend `auth_manager.py` with `superadmin` role, new `list_all_users` and `update_user_role` methods.
- [x] Update `contractApi.py` with `require_superadmin` dependency, `GET /admin/users` and `PUT /admin/users/{user_id}/role` endpoints.
- [x] Update frontend types (`UserRole`, `UserRecord`) and auth service (new API functions).
- [x] Create `PersonnelPage.tsx` with registration approval and user management table.
- [x] Update `App.tsx` routing and menu logic for three-tier roles.
- [x] Remove registration approval code from `UploadPage.tsx`.
- [x] Verify frontend build passes.
