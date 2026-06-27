"""Pure tournament lifecycle state machine.

No I/O — only data and predicates so it is trivially unit-testable. Services
combine these rules with DB state (team counts, schedule, etc.).
"""

from app.db.models.enums import TournamentStatus as S

# The full lifecycle graph. Later phases drive transitions into the scheduling /
# group / qualifier / finalize states; Phase 2 only exposes the manual subset
# below via the API.
ALLOWED_TRANSITIONS: dict[S, set[S]] = {
    S.DRAFT: {S.REGISTRATION_OPEN, S.CANCELLED},
    S.REGISTRATION_OPEN: {S.DRAFT, S.REGISTRATION_CLOSED, S.CANCELLED},
    S.REGISTRATION_CLOSED: {S.REGISTRATION_OPEN, S.SCHEDULED, S.CANCELLED},
    S.SCHEDULED: {S.GROUP_IN_PROGRESS, S.PAUSED, S.CANCELLED},
    S.GROUP_IN_PROGRESS: {S.GROUP_COMPLETE, S.PAUSED, S.CANCELLED},
    S.GROUP_COMPLETE: {S.QUALIFIERS_IN_PROGRESS, S.PAUSED, S.CANCELLED},
    S.QUALIFIERS_IN_PROGRESS: {S.COMPLETED, S.PAUSED, S.CANCELLED},
    S.COMPLETED: {S.FINALIZED},
    S.FINALIZED: {S.ARCHIVED},
    S.PAUSED: {S.SCHEDULED, S.GROUP_IN_PROGRESS, S.QUALIFIERS_IN_PROGRESS, S.CANCELLED},
    S.CANCELLED: {S.ARCHIVED},
    S.ARCHIVED: set(),
}

# Transitions an admin may trigger directly via POST /tournaments/{id}/transition
# in Phase 2. Other transitions are produced by later-phase services (schedule
# generation, match completion, bracket, finalize) and are not manually settable.
MANUALLY_TRIGGERABLE: set[S] = {
    S.DRAFT,
    S.REGISTRATION_OPEN,
    S.REGISTRATION_CLOSED,
    S.CANCELLED,
}

# Teams and tournament config may only be edited in these states.
EDITABLE_STATES: set[S] = {S.DRAFT, S.REGISTRATION_OPEN}


def can_transition(current: S, target: S) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def is_manual_transition(target: S) -> bool:
    return target in MANUALLY_TRIGGERABLE


def is_editable(status: S) -> bool:
    """True when tournament config and team rosters may be modified."""
    return status in EDITABLE_STATES


def is_roster_locked(status: S) -> bool:
    return not is_editable(status)
