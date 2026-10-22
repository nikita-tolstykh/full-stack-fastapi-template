# Role-Based Access Control

This branch adds three roles, **admin**, **manager** and **member**, to the Full Stack FastAPI Template.

## Initial setup

Prerequisites: [Docker](https://www.docker.com), [uv](https://docs.astral.sh/uv/) and [bun](https://bun.sh).

From the project root, start Postgres and Mailpit:

```bash
docker compose up -d db mailpit
```

Set up and run the backend. `prestart.sh` runs the database migrations and creates the accounts listed below.

```bash
cd backend
uv sync
uv run bash scripts/prestart.sh
uv run fastapi dev
```

In a second terminal, from the project root, run the frontend:

```bash
bun install
bun run dev
```

- Frontend: <http://localhost:5173>
- API docs: <http://localhost:8000/docs>

Seeded accounts (the password is `FIRST_SUPERUSER_PASSWORD` from `.env`):

| Role | Email | Password |
|---|---|---|
| admin | `admin@example.com` | `changethis` |
| manager | `manager@example.com` | `changethis` |
| member | `member@example.com` | `changethis` |

The manager and member accounts are created only when `FASTAPI_ENV=development`, which is the default in `.env`.

If port 8000 is already in use, start the backend with `uv run fastapi dev --port 8010` and the frontend with `VITE_API_URL=http://localhost:8010 bun run dev`.

To run the full stack in Docker instead, use `docker compose run --rm backend bash scripts/prestart.sh && docker compose watch` and open <http://localhost:8000>.

## How authorization works

**Where the checks live.** `backend/app/core/permissions.py` is the only place that says which role can do what. It defines `Role`, `Permission` and a single `ROLE_PERMISSIONS` map. Routes ask for a permission, not a role name, through a FastAPI dependency: `dependencies=[Depends(require_permission(Permission.USERS_READ))]` reads as "this endpoint needs `users:read`". Some rules depend on the request itself: you can always read your own record, owners can edit their own items, and nobody can change their own role. Those rules call the same `ensure_permission()` / `has_permission()` helpers inside the route. The only check by role name is that admins can't delete their own account. A failed permission check returns 403 and logs a warning with the user id, role and permission. A missing or invalid token returns 401.

**How roles are stored and validated.** `user.role` is a `VARCHAR(20)` column (default `member`), validated by the `Role` enum. It is not a native Postgres enum, so adding a role needs no database migration. Migration `7c3e9a1d5b20` turns existing superusers into admins and everyone else into members. Signup always creates a `member`, `PATCH /users/me` has no `role` field, and only `users:manage` can set roles. The JWT carries only the user id and the role is read from the database on every request, so a role change takes effect on the user's next request.

**How the frontend learns what the user can do.** `GET /users/me` returns the user's `role` and their effective `permissions`, for example `["metrics:read", "users:read"]`. The frontend never duplicates the role map. `usePermissions().can(...)` hides nav links and buttons, and `<RequirePermission>` wraps a page so that opening it directly shows an Access denied page instead of a silent redirect. The UI logs the user out only on a 401; a 403 shows the error and keeps the session. Hiding things in the UI is only a convenience, and the API remains the source of truth.

**Adding a role.** Add it to `Role` and `ROLE_PERMISSIONS`, then regenerate the frontend client (`bash scripts/generate-client.sh`). TypeScript then flags the one remaining place to update, the label in `frontend/src/components/Admin/RoleSelect.tsx`.

## Running the test matrix

Both suites need the database running (`docker compose up -d db mailpit`).

### Backend (pytest)

```bash
cd backend
uv run bash scripts/test.sh
```

To run only the authorization matrix:

```bash
uv run pytest tests/api/routes/test_rbac.py -v
```

The suite deletes all users when it finishes. Run `uv run bash scripts/prestart.sh` again to restore the seeded accounts.

To run the backend suite entirely in Docker instead (only Docker is needed), run this from the project root:

```bash
bash scripts/test.sh
```

It builds the backend image, recreates the database, runs all migrations and tests in a container, then removes the containers and the database volume. Afterwards, run `docker compose up -d db mailpit` and `uv run bash scripts/prestart.sh` to get the seeded accounts back.

### Frontend (Playwright)

The backend must be running as described in [Initial setup](#initial-setup). The tests create users through the development-only API, and Playwright starts the Vite dev server itself.

```bash
cd frontend
bunx playwright install chromium
bunx playwright test
```

To run only the authorization matrix:

```bash
bunx playwright test tests/rbac.spec.ts
```

If the backend runs on another port, prefix the command, for example `VITE_API_URL=http://localhost:8010 bunx playwright test`.

### Requirements coverage

Each rule from the assignment brief, the expected result for each role, and the tests that check it. Backend tests are in `backend/tests/api/routes/test_rbac.py`. Frontend tests are in `frontend/tests/rbac.spec.ts` unless noted, and each one runs once per role.

**Role permissions.** In the API, ✓ means 200 (201 for the settings endpoint) and ✗ means 403. In the UI, ✗ means the link or button is hidden and opening the page shows Access denied.

| Requirement | admin | manager | member | Backend tests | Frontend tests |
|---|:-:|:-:|:-:|---|---|
| List users | ✓ | ✓ | ✗ | `test_list_users`, `test_read_another_user` | sidebar shows only permitted links, users page |
| Create user | ✓ | ✗ | ✗ | `test_create_user` | users page (Add User button); `admin.spec.ts`: Create a new user successfully, Create a manager |
| Update or delete any user, change roles | ✓ | ✗ | ✗ | `test_update_another_user`, `test_delete_another_user`, `test_admin_can_change_another_users_role` | users page (row actions) |
| View metrics page | ✓ | ✓ | ✗ | `test_read_metrics` | sidebar shows only permitted links, metrics page |
| View and update own profile | ✓ | ✓ | ✓ | `test_update_own_profile`, `test_me_returns_role_permissions` | can edit own profile |
| Change global settings (`POST /utils/test-email/`) | ✓ | ✗ | ✗ | `test_send_test_email` | – (no settings page in the UI) |
| Access other users' items (everyone keeps their own) | ✓ | ✗ | ✗ | `test_read_another_users_item` | – |

`test_me_returns_role_permissions` also checks the permission list each role receives: all six for admin, `metrics:read` and `users:read` for manager, none for member.

**Security, UX and setup.**

| Requirement | Tests |
|---|---|
| No privilege escalation | `test_signup_ignores_requested_role`, `test_member_cannot_change_own_role_via_profile`, `test_manager_cannot_promote_themselves`, `test_admin_cannot_change_own_role` |
| Correct HTTP status codes | `test_missing_token_is_unauthorized` and `test_invalid_token_is_unauthorized` (401); every ✗ in the role table (403) |
| Hide links and buttons the user can't use | sidebar shows only permitted links, users page |
| Friendly message when opening a forbidden page directly | users page and metrics page as member; `admin.spec.ts`: Member sees Access Denied on admin page |
| No silent failures or cryptic errors | a 403 from the API shows the error and keeps the user signed in |
| Log denied attempts | `test_denied_request_is_logged` |
| Every role has a permission set (guard for new roles) | `backend/tests/core/test_permissions.py`: `test_every_role_has_a_permission_set` |
| Migrations and seed data (admin and non-admin users) | `bash scripts/test.sh` runs every migration and the seed on a fresh database before the tests |

---

*The rest of this README is the original template documentation.*

# Full Stack FastAPI Template

[![Test Docker Compose](../../actions/workflows/test-docker-compose.yml/badge.svg)](../../actions/workflows/test-docker-compose.yml)
[![Test Backend](../../actions/workflows/test-backend.yml/badge.svg)](../../actions/workflows/test-backend.yml)

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
  - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
  - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
  - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🚀 [React](https://react.dev) for the frontend.
  - 🧩 Built into the backend application and served by FastAPI on the same domain as the API.
  - 💃 Using TypeScript, hooks, [Vite](https://vitejs.dev), and other parts of a modern frontend stack.
  - 🎨 [Tailwind CSS](https://tailwindcss.com) and [shadcn/ui](https://ui.shadcn.com) for the frontend components.
  - 🤖 An automatically generated frontend client.
  - 🧪 [Playwright](https://playwright.dev) for end-to-end testing.
  - 🦇 Dark mode support.
- ☁️ [FastAPI Cloud](https://fastapicloud.com) for deployment.
- 🐋 [Docker Compose](https://www.docker.com) for local services and self-hosted deployment.
  - 📞 [Traefik](https://traefik.io) as a reverse proxy with automatic HTTPS.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email-based password recovery.
- ✉️ [React Email](https://react.email) for email templates.
- 📬 [Mailpit](https://mailpit.axllent.org) for local email testing during development.
- ✅ Tests with [Pytest](https://pytest.org).
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

### Dashboard Login

![Dashboard login screenshot](img/login.png)

### Dashboard - Admin

![Admin dashboard screenshot](img/dashboard.png)

### Dashboard - Items

![Items dashboard screenshot](img/dashboard-items.png)

### Dashboard - Dark Mode

![Dark mode dashboard screenshot](img/dashboard-dark.png)

### React Email Templates

![Email templates screenshot](img/react-email.png)

### Mailpit - Local Email Testing

![Mailpit screenshot](img/mailpit.png)

### Interactive API Documentation

![API docs](img/docs.png)

## How to Use It

Click the **Use this template** button at the top of this page to create a new repository.

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

FastAPI Cloud deployment: [deployment.md](./deployment.md).

Self-hosted deployment with Docker Compose: [deployment-docker-compose.md](./deployment-docker-compose.md).

## Development

General development docs: [development.md](./development.md).

This includes the local FastAPI and Vite workflow, Docker Compose services, `.env` configuration, and more.

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.
