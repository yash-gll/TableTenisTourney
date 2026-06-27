from app.db.models.enums import TournamentStatus as S
from app.domain import tournament_state as ts


def test_basic_forward_transitions_allowed():
    assert ts.can_transition(S.DRAFT, S.REGISTRATION_OPEN)
    assert ts.can_transition(S.REGISTRATION_OPEN, S.REGISTRATION_CLOSED)
    assert ts.can_transition(S.REGISTRATION_CLOSED, S.SCHEDULED)


def test_illegal_transitions_blocked():
    assert not ts.can_transition(S.DRAFT, S.SCHEDULED)
    assert not ts.can_transition(S.DRAFT, S.COMPLETED)
    assert not ts.can_transition(S.COMPLETED, S.DRAFT)
    assert not ts.can_transition(S.ARCHIVED, S.DRAFT)


def test_cancel_allowed_from_pre_start_states():
    for s in (S.DRAFT, S.REGISTRATION_OPEN, S.REGISTRATION_CLOSED):
        assert ts.can_transition(s, S.CANCELLED)


def test_manual_transition_subset():
    assert ts.is_manual_transition(S.REGISTRATION_CLOSED)
    assert ts.is_manual_transition(S.CANCELLED)
    # Later-phase states are not manually settable.
    assert not ts.is_manual_transition(S.SCHEDULED)
    assert not ts.is_manual_transition(S.GROUP_IN_PROGRESS)
    assert not ts.is_manual_transition(S.FINALIZED)


def test_editable_and_locked_states():
    assert ts.is_editable(S.DRAFT)
    assert ts.is_editable(S.REGISTRATION_OPEN)
    assert not ts.is_editable(S.REGISTRATION_CLOSED)
    assert ts.is_roster_locked(S.REGISTRATION_CLOSED)
    assert ts.is_roster_locked(S.SCHEDULED)
