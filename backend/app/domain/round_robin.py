"""Single round-robin generation (circle method) — pure, no I/O.

Pairing is intentionally separate from court/time assignment.
"""


def generate_round_robin(team_ids: list[str]) -> list[list[tuple[str, str]]]:
    """Return a list of rounds; each round is a list of (team_a, team_b) pairs.

    Odd team counts get a bye each round (the team paired with the placeholder
    is simply omitted from that round).
    """
    teams: list[str | None] = list(team_ids)

    if len(teams) % 2 == 1:
        teams.append(None)

    rounds: list[list[tuple[str, str]]] = []
    n = len(teams)

    for _ in range(n - 1):
        round_matches: list[tuple[str, str]] = []
        for i in range(n // 2):
            team_a = teams[i]
            team_b = teams[n - 1 - i]
            if team_a is not None and team_b is not None:
                round_matches.append((team_a, team_b))
        rounds.append(round_matches)
        # Rotate, keeping the first element fixed.
        teams = [teams[0], teams[-1], *teams[1:-1]]

    return rounds


def expected_match_count(num_teams: int) -> int:
    return num_teams * (num_teams - 1) // 2


def validate_schedule(team_ids: list[str], rounds: list[list[tuple[str, str]]]) -> None:
    """Raise ValueError if the schedule violates round-robin invariants."""
    ids = set(team_ids)
    seen_pairs: set[frozenset[str]] = set()

    for rnd in rounds:
        in_round: set[str] = set()
        for a, b in rnd:
            if a == b:
                raise ValueError("team cannot play itself")
            if a not in ids or b not in ids:
                raise ValueError("unknown team in schedule")
            if a in in_round or b in in_round:
                raise ValueError("team appears twice in a round")
            in_round.update((a, b))
            pair = frozenset((a, b))
            if pair in seen_pairs:
                raise ValueError("duplicate pairing")
            seen_pairs.add(pair)

    if len(seen_pairs) != expected_match_count(len(ids)):
        raise ValueError("not every pair appears exactly once")
