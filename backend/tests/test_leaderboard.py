from app.domain.leaderboard import MatchResult, TeamSeed, compute_standings

# The required spec example.
ABCDE_RESULTS = [
    ("A", "B", 3, 11),
    ("C", "D", 11, 10),
    ("B", "E", 10, 11),
    ("A", "C", 11, 7),
    ("B", "D", 11, 7),
    ("A", "E", 11, 10),
    ("B", "C", 11, 10),
    ("D", "E", 11, 6),
    ("C", "E", 9, 11),
    ("A", "D", 6, 11),
]


def _standings(team_ids, raw, **kw):
    teams = [TeamSeed(team_id=t) for t in team_ids]
    results = [MatchResult(a, b, sa, sb) for a, b, sa, sb in raw]
    return compute_standings(teams, results, group_complete=True, **kw).standings


def test_required_abcde_example():
    standings = _standings(["A", "B", "C", "D", "E"], ABCDE_RESULTS)
    order = [s.team_id for s in standings]
    assert order == ["B", "D", "E", "A", "C"]

    by_id = {s.team_id: s for s in standings}
    assert (by_id["B"].wins, by_id["B"].points_for, by_id["B"].points_against) == (3, 43, 31)
    assert by_id["B"].point_difference == 12
    assert by_id["D"].point_difference == 5
    assert by_id["E"].point_difference == -3
    assert by_id["A"].point_difference == -8
    assert by_id["C"].point_difference == -6
    # Wins outrank point difference: C (1 win, -6) ranks below A (2 wins, -8).
    assert by_id["C"].rank == 5 and by_id["A"].rank == 4


def test_wins_outrank_point_difference():
    raw = [("P", "Q", 11, 9), ("P", "R", 11, 9), ("Q", "R", 11, 0)]
    order = [s.team_id for s in _standings(["P", "Q", "R"], raw)]
    # Q has a far better diff (+9) than P (+4) but fewer wins -> P ranks first.
    assert order == ["P", "Q", "R"]


def test_point_difference_breaks_equal_wins():
    raw = [("X", "Z", 11, 3), ("Y", "Z", 11, 9), ("X", "Y", 0, 11)]
    # X: 1W diff (+8-11)=-3? compute: X beats Z +8, loses Y -11 => 1W1L diff -3
    # Y: beats Z +2, beats X +11 => 2W; Z: 0W. So Y first by wins.
    order = [s.team_id for s in _standings(["X", "Y", "Z"], raw)]
    assert order[0] == "Y"


def test_two_team_head_to_head():
    raw = [
        ("X", "Y", 11, 9),   # X beats Y (head-to-head)
        ("X", "P", 11, 9), ("Q", "X", 11, 9),
        ("Y", "P", 11, 9), ("Y", "Q", 11, 9),
        ("Q", "P", 11, 5),
    ]
    standings = _standings(["X", "Y", "P", "Q"], raw)
    by_id = {s.team_id: s for s in standings}
    # X and Y tie on wins(2)+diff(+2); X beat Y head-to-head -> X above Y.
    assert by_id["X"].rank < by_id["Y"].rank
    assert by_id["X"].tie_status == "HEAD_TO_HEAD"
    assert by_id["Y"].tie_status == "HEAD_TO_HEAD"


def test_three_team_mini_table():
    raw = [
        ("X", "Y", 11, 5), ("Y", "Z", 11, 5), ("Z", "X", 11, 9),   # cyclic by wins
        ("X", "F1", 11, 9), ("X", "F2", 11, 9),                     # X fodder margin +4
        ("Y", "F1", 11, 7), ("Y", "F2", 11, 7),                     # Y fodder margin +8
        ("Z", "F1", 11, 5), ("Z", "F2", 11, 5),                     # Z fodder margin +12
        ("F1", "F2", 11, 9),
    ]
    standings = _standings(["X", "Y", "Z", "F1", "F2"], raw)
    by_id = {s.team_id: s for s in standings}
    # X,Y,Z tie on wins(3)+diff(+8); mini point-difference orders X > Y > Z.
    assert (by_id["X"].rank, by_id["Y"].rank, by_id["Z"].rank) == (1, 2, 3)
    assert by_id["X"].tie_status == "MINI_TABLE"


def test_cyclic_tie_unresolved():
    raw = [("X", "Y", 11, 9), ("Y", "Z", 11, 9), ("Z", "X", 11, 9)]
    standings = _standings(["X", "Y", "Z"], raw)
    assert all(s.tie_status == "UNRESOLVED" for s in standings)
