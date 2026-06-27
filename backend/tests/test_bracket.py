from app.db.models.enums import DependencyOutcome, DependencySlot, MatchStage
from app.domain.bracket import DEPENDENCIES, placement_map


def test_placement_map():
    places = placement_map(
        final_winner="W", final_loser="L", qf3_loser="T3", qf2_loser="T4"
    )
    assert places == {"W": 1, "L": 2, "T3": 3, "T4": 4}


def test_placement_map_partial():
    assert placement_map(final_winner=None, final_loser=None, qf3_loser="X", qf2_loser="Y") == {
        "X": 3,
        "Y": 4,
    }


def test_dependency_structure():
    deps = set(DEPENDENCIES)
    # QF3 = winner(QF2) vs loser(QF1); Final = winner(QF1) vs winner(QF3)
    assert (MatchStage.QF3, DependencySlot.TEAM_A, MatchStage.QF2, DependencyOutcome.WINNER) in deps
    assert (MatchStage.QF3, DependencySlot.TEAM_B, MatchStage.QF1, DependencyOutcome.LOSER) in deps
    assert (MatchStage.FINAL, DependencySlot.TEAM_A, MatchStage.QF1, DependencyOutcome.WINNER) in deps
    assert (MatchStage.FINAL, DependencySlot.TEAM_B, MatchStage.QF3, DependencyOutcome.WINNER) in deps
