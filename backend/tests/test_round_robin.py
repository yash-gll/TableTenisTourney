import pytest

from app.domain.round_robin import (
    expected_match_count,
    generate_round_robin,
    validate_schedule,
)


@pytest.mark.parametrize("n,matches", [(4, 6), (5, 10), (6, 15), (8, 28)])
def test_match_counts(n, matches):
    ids = [str(i) for i in range(n)]
    rounds = generate_round_robin(ids)
    total = sum(len(r) for r in rounds)
    assert total == matches == expected_match_count(n)
    validate_schedule(ids, rounds)  # should not raise


def test_no_duplicate_pairs_no_self():
    ids = [f"t{i}" for i in range(6)]
    rounds = generate_round_robin(ids)
    seen = set()
    for rnd in rounds:
        for a, b in rnd:
            assert a != b
            key = frozenset((a, b))
            assert key not in seen
            seen.add(key)
    assert len(seen) == 15


def test_no_team_twice_in_a_round():
    ids = [f"t{i}" for i in range(6)]
    for rnd in generate_round_robin(ids):
        flat = [t for pair in rnd for t in pair]
        assert len(flat) == len(set(flat))


def test_odd_count_has_byes():
    ids = [f"t{i}" for i in range(5)]
    rounds = generate_round_robin(ids)
    # 5 teams -> 5 rounds, each with 2 matches (one team byes per round).
    assert len(rounds) == 5
    for rnd in rounds:
        assert len(rnd) == 2
    validate_schedule(ids, rounds)


def test_every_pair_appears_once_for_odd():
    ids = [f"t{i}" for i in range(5)]
    rounds = generate_round_robin(ids)
    assert sum(len(r) for r in rounds) == 10
