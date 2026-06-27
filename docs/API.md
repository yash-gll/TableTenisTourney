# API Reference — Phases 0–2

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

## Tournaments

Reads are public (visibility-filtered); writes require **ADMIN**.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/tournaments` | public | List tournaments. Guests/players see `PUBLIC` only; admins see all. |
| GET | `/tournaments/{id}` | public | Get one. `PRIVATE` returns 404 to non-admins. |
| POST | `/tournaments` | admin | Create. Body: `{ name, description?, location?, start_at?, end_at?, visibility?, scoring? }`. Starts in `DRAFT`. |
| PATCH | `/tournaments/{id}` | admin | Update config (name, scoring, visibility, …). Only when editable (`DRAFT`/`REGISTRATION_OPEN`); bumps `version`. **Status is not patchable here.** |
| POST | `/tournaments/{id}/transition` | admin | `{ target, reason? }`. Validated state-machine command. |
| DELETE | `/tournaments/{id}` | admin | Hard delete (only before `SCHEDULED`); otherwise cancel via transition. |

`scoring`: `{ target_points=11, win_by_two=false, maximum_points?, win_table_points=2, loss_table_points=0 }`.

**State machine** (Phase 2 manual transitions): `DRAFT → REGISTRATION_OPEN ⇄
REGISTRATION_CLOSED`, and any pre-start state `→ CANCELLED`. Other targets
(`SCHEDULED`, `GROUP_*`, `FINALIZED`, …) are produced by later-phase services,
not this endpoint, and return `409 INVALID_TOURNAMENT_TRANSITION`.

## Teams

All writes require **ADMIN** and the tournament must be **editable**
(`DRAFT`/`REGISTRATION_OPEN`). Member payloads are public-safe (no emails).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/tournaments/{id}/teams` | public | List teams (+ members, `average_rating`, `is_complete`). |
| POST | `/tournaments/{id}/teams` | admin | `{ name, initial_seed?, logo_url? }`. Unique name per tournament. |
| PATCH | `/tournaments/{id}/teams/{team_id}` | admin | Update name/seed/logo. |
| DELETE | `/tournaments/{id}/teams/{team_id}` | admin | Remove a team. |
| POST | `/tournaments/{id}/teams/{team_id}/members` | admin | `{ player_id }`. Player must be **APPROVED**, not already on a team, team must have < 2 members. |
| DELETE | `/tournaments/{id}/teams/{team_id}/members/{player_id}` | admin | Remove a member. |

Team rule errors: `TEAM_NAME_TAKEN`, `TEAM_ALREADY_FULL`, `PLAYER_NOT_APPROVED`,
`PLAYER_ALREADY_ON_TEAM`, `TOURNAMENT_NOT_EDITABLE`.

## Authorization model

- Deny-by-default. No token → `401 UNAUTHENTICATED`. Wrong role → `403 FORBIDDEN`.
- `require_admin` guards all `/admin/*` routes.
- `require_approved_player` exists for future tournament participation endpoints.

## Enums

- **role:** `PLAYER | ADMIN | SUPER_ADMIN`
- **account_status:** `ACTIVE | SUSPENDED | DISABLED`
- **approval_status:** `PENDING | APPROVED | REJECTED | SUSPENDED`
- **tournament_status:** `DRAFT | REGISTRATION_OPEN | REGISTRATION_CLOSED | SCHEDULED | GROUP_IN_PROGRESS | GROUP_COMPLETE | QUALIFIERS_IN_PROGRESS | COMPLETED | FINALIZED | PAUSED | CANCELLED | ARCHIVED`
- **visibility:** `PUBLIC | PRIVATE | UNLISTED`
