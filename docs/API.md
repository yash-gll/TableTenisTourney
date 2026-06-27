# API Reference — Phases 0–7

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

## Player directory (public)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/players?search=<q>` | public | Approved players (public-safe: name + ratings, no email), name-filtered, ranked by rating. |
| GET | `/players/{id}` | public | Public profile: name, current/highest rating, and match stats (played, wins, losses, win %, tournaments played, titles). |

(`/players/me` resolves to the authenticated profile and is matched before `/{id}`.)

## Player skills (coaching attributes, 0–100)

Admin-curated skill card, separate from the competitive Elo rating. Default
attributes: Serve, Smash, Spin, Footwork, Consistency (edit `app/domain/skills.py`).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/players/{id}/skills` | public | Ordered, labelled skill values (null = unrated). |
| PATCH | `/admin/players/{id}/skills` | admin | `{ ratings: { serve: 80, ... } }` — partial, merged; values 0–100, keys must be known (`422 INVALID_SKILL_RATING` otherwise). |

A player's own values are also included as `skill_ratings` on `GET /players/me`.

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

All writes require **ADMIN**. Team creation, deletion, roster changes, and seed
edits require the tournament to be **editable** (`DRAFT`/`REGISTRATION_OPEN`).
**Team name and logo can be edited any time except after the tournament is
finalized/cancelled/archived** (renaming mid-tournament is allowed). Member
payloads are public-safe (no emails).

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

## Registrations (self sign-up)

Players request to join a tournament while it's `REGISTRATION_OPEN`; the admin
reviews and still forms the teams. Open public tournaments also appear in a
player's `/tournaments` list so they can find them.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/tournaments/{id}/registrations` | approved player | Request to join (`{ preferred_partner_id?, note? }`). Only when `REGISTRATION_OPEN`. |
| GET | `/tournaments/{id}/registrations/me` | approved player | Own status (or null). |
| DELETE | `/tournaments/{id}/registrations/me` | approved player | Withdraw. |
| GET | `/tournaments/{id}/registrations` | admin | All sign-ups (+ names). |
| POST | `/tournaments/{id}/registrations/{player_id}/accept` \| `decline` \| `waitlist` | admin | Set status. |

## Schedule & matches

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/tournaments/{id}/schedule/generate` | admin | Generate the single round-robin (requires `REGISTRATION_CLOSED`, ≥2 teams each with exactly 2 approved players). Idempotent. Moves status to `SCHEDULED`. |
| GET | `/tournaments/{id}/matches` | public | List all matches (group + bracket). |
| GET | `/matches/{match_id}` | public | One match. |
| POST | `/matches/{match_id}/start` | admin | `SCHEDULED → IN_PROGRESS`. |
| POST | `/matches/{match_id}/complete` | admin | `{ team_a_score, team_b_score, expected_version }`. Backend resolves the winner; bumps version; auto-completes the group when all done. |
| POST | `/matches/{match_id}/correct` | admin | `{ team_a_score, team_b_score, expected_version, reason, reset_dependents? }`. Re-resolves winner; for bracket matches, propagates/reset downstream. |

Optimistic locking: a stale `expected_version` returns `409 MATCH_VERSION_CONFLICT`
with the latest version. Invalid scores return `422 INVALID_MATCH_SCORE`.

## Predictions (pick'em)

Players predict match winners; correct picks score 1 point and feed a
per-tournament leaderboard. Predictions lock when a match completes and are
re-graded automatically if a result is corrected.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/matches/{match_id}/predict` | approved player | `{ winner_team_id }`. Only while scheduled/in-progress. Upserts. |
| GET | `/tournaments/{id}/predictions/me` | approved player | Your picks for the tournament. |
| GET | `/tournaments/{id}/predictions/leaderboard` | public | Ranked predictors (points, correct/total). |

## Leaderboard

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/tournaments/{id}/leaderboard` | public | Standings: wins → point-difference → head-to-head / mini-table → fallback. Top-four flagged `QUALIFIED` only once the group is complete. |
| GET | `/tournaments/{id}/leaderboard/explanation` | public | Human-readable tie-break trace. |
| POST | `/tournaments/{id}/leaderboard/resolve-tie` | admin | `{ ordering: [team_id…], reason }` — manual tie override. |

## Bracket

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/tournaments/{id}/bracket/generate` | admin | Requires `GROUP_COMPLETE`, ≥4 teams, no unresolved top tie. Creates QF1/QF2 from ranks 1–4 and QF3/Final via dependencies. Moves status to `QUALIFIERS_IN_PROGRESS`. Idempotent. |
| GET | `/tournaments/{id}/bracket` | public | Bracket matches + current placements. |
| POST | `/tournaments/{id}/bracket/rebuild` | admin | Wipe and regenerate (critical, audited). |

Dependency flow: QF1 winner → Final; QF1 loser → QF3; QF2 winner → QF3; QF3
winner → Final. Placements: 1st Final winner, 2nd Final loser, 3rd QF3 loser,
4th QF2 loser. Completing the Final moves the tournament to `COMPLETED`.

## Ratings (Elo)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/ratings/config` | public | Current Elo config (K values, bonuses, floor). |
| PATCH | `/admin/ratings/config` | admin | Update config fields. |
| GET | `/players/{id}/rating-events` | public | A player's (non-superseded) rating ledger. |
| POST | `/admin/players/{id}/rating-adjustment` | admin | `{ delta, reason }` manual adjustment (audited). |
| POST | `/admin/ratings/recalculate` | admin | `{ tournament_id }` — replay ratings from start snapshots. |

Match Elo is applied on completion (both teammates get the same delta; K varies
by stage: group 20, QF1/QF2 24, QF3 28, Final 32). A correction replays the whole
tournament from its start snapshots so ratings reflect the corrected history.

## Finalization

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/tournaments/{id}/finalize` | admin | From `COMPLETED`: apply placement bonuses (champion +50, runner-up +15, third +5), snapshot end ratings, persist results, set `FINALIZED` (read-only). |
| POST | `/tournaments/{id}/reopen` | admin | From `FINALIZED`: revert placement bonuses, delete the result record, back to `COMPLETED` (critical, audited). |

## History (public, finalized tournaments)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/history/tournaments` | List finalized tournaments with champion. |
| GET | `/history/tournaments/{id}` | Summary + placements. |
| GET | `/history/tournaments/{id}/leaderboard` | Final group leaderboard snapshot. |
| GET | `/history/tournaments/{id}/bracket` | Final bracket snapshot. |
| GET | `/history/tournaments/{id}/matches` | All match results. |

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
