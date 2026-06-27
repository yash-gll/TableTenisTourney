# API Reference — Phase 0 & 1

Base path: `/api/v1`. All requests/responses are JSON. Authenticated endpoints
expect `Authorization: Bearer <access_token>`.

## Error envelope

Every error returns:

```json
{
  "error": {
    "code": "EMAIL_NOT_VERIFIED",
    "message": "Email address is not verified.",
    "details": {},
    "request_id": ""
  }
}
```

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | — | `{ "status": "ok", "db": "ok" }` |

## Authentication

| Method | Path | Auth | Body |
|--------|------|------|------|
| POST | `/auth/register` | — | `{ email, password, display_name }` → 201 |
| POST | `/auth/verify-email` | — | `{ token }` |
| POST | `/auth/resend-verification` | — | `{ email }` |
| POST | `/auth/login` | — | `{ email, password }` → `{ access_token, refresh_token, token_type }` |
| POST | `/auth/refresh` | — | `{ refresh_token }` → new token pair (old refresh revoked) |
| POST | `/auth/logout` | — | `{ refresh_token }` (revokes it) |
| POST | `/auth/forgot-password` | — | `{ email }` |
| POST | `/auth/reset-password` | — | `{ token, password }` |
| GET | `/auth/me` | player | current identity + approval status |

Notes:

- Login requires a **verified** email and an **ACTIVE** account.
- Verification & reset tokens are **logged to the backend console** (no email service).
- Refresh tokens are **rotated**: refreshing revokes the old token; a password
  reset revokes all of the user's refresh tokens.

## Players (self-service)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/players/me` | player | Full own profile (email, ratings, approval status) |
| PATCH | `/players/me` | player | `{ display_name?, bio? }` |

## Admin — player approval

All require an **ADMIN** (or SUPER_ADMIN) token.

| Method | Path | Body | Description |
|--------|------|------|-------------|
| GET | `/admin/players?approval_status=PENDING` | — | List players, optional status filter |
| POST | `/admin/players/{player_id}/approve` | — | Set APPROVED |
| POST | `/admin/players/{player_id}/reject` | `{ reason }` | Set REJECTED (reason required) |
| POST | `/admin/players/{player_id}/suspend` | `{ reason }` | Set SUSPENDED + account SUSPENDED |
| POST | `/admin/players/{player_id}/restore` | — | Set APPROVED + account ACTIVE |

Every approve/reject/suspend/restore writes an `audit_logs` row (actor, before/after, reason, severity).

## Authorization model

- Deny-by-default. No token → `401 UNAUTHENTICATED`. Wrong role → `403 FORBIDDEN`.
- `require_admin` guards all `/admin/*` routes.
- `require_approved_player` exists for future tournament participation endpoints.

## Enums

- **role:** `PLAYER | ADMIN | SUPER_ADMIN`
- **account_status:** `ACTIVE | SUSPENDED | DISABLED`
- **approval_status:** `PENDING | APPROVED | REJECTED | SUSPENDED`
