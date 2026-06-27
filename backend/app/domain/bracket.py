"""Pure qualifier-bracket structure and placement rules.

    QF1: Rank 1 vs Rank 2
    QF2: Rank 3 vs Rank 4
    QF3: Winner of QF2 vs Loser of QF1
    Final: Winner of QF1 vs Winner of QF3

Placement: 1st = Final winner, 2nd = Final loser, 3rd = QF3 loser, 4th = QF2 loser.
"""

from app.db.models.enums import DependencyOutcome as Out
from app.db.models.enums import DependencySlot as Slot
from app.db.models.enums import MatchStage as Stage

# (target_stage, target_slot, source_stage, source_outcome)
DEPENDENCIES: list[tuple[Stage, Slot, Stage, Out]] = [
    (Stage.QF3, Slot.TEAM_A, Stage.QF2, Out.WINNER),
    (Stage.QF3, Slot.TEAM_B, Stage.QF1, Out.LOSER),
    (Stage.FINAL, Slot.TEAM_A, Stage.QF1, Out.WINNER),
    (Stage.FINAL, Slot.TEAM_B, Stage.QF3, Out.WINNER),
]

BRACKET_STAGES = (Stage.QF1, Stage.QF2, Stage.QF3, Stage.FINAL)


def placement_map(
    *,
    final_winner: str | None,
    final_loser: str | None,
    qf3_loser: str | None,
    qf2_loser: str | None,
) -> dict[str, int]:
    """Return {team_id: placement} for whichever results are known."""
    places: dict[str, int] = {}
    if final_winner:
        places[final_winner] = 1
    if final_loser:
        places[final_loser] = 2
    if qf3_loser:
        places[qf3_loser] = 3
    if qf2_loser:
        places[qf2_loser] = 4
    return places
