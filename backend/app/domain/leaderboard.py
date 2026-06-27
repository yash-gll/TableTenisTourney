"""Pure leaderboard ranking.

Ranking priority (per spec):
  1. Wins (desc)
  2. Point difference (desc)
  3. Head-to-head (two-team) / mini-table (3+ teams)
  4. Fallback: overall points-for (desc), points-against (asc), seed, manual

A team with more wins always ranks above one with fewer wins, even if the
lower-win team has a better point difference.
"""

from dataclasses import dataclass, field

INF = float("inf")


@dataclass(frozen=True)
class TeamSeed:
    team_id: str
    seed: int | None = None


@dataclass(frozen=True)
class MatchResult:
    team_a: str
    team_b: str
    a_score: int
    b_score: int


@dataclass
class Stats:
    wins: int = 0
    losses: int = 0
    points_for: int = 0
    points_against: int = 0

    @property
    def played(self) -> int:
        return self.wins + self.losses

    @property
    def diff(self) -> int:
        return self.points_for - self.points_against


@dataclass
class Standing:
    team_id: str
    played: int
    wins: int
    losses: int
    points_for: int
    points_against: int
    point_difference: int
    table_points: int
    rank: int = 0
    tie_status: str = "CLEAR"
    qualification_status: str = "NONE"


@dataclass
class LeaderboardResult:
    standings: list[Standing]
    explanation: list[str] = field(default_factory=list)


def _aggregate(team_ids: set[str], results: list[MatchResult]) -> dict[str, Stats]:
    stats = {t: Stats() for t in team_ids}
    for r in results:
        if r.team_a not in team_ids or r.team_b not in team_ids:
            continue
        sa, sb = stats[r.team_a], stats[r.team_b]
        sa.points_for += r.a_score
        sa.points_against += r.b_score
        sb.points_for += r.b_score
        sb.points_against += r.a_score
        if r.a_score > r.b_score:
            sa.wins += 1
            sb.losses += 1
        else:
            sb.wins += 1
            sa.losses += 1
    return stats


def compute_standings(
    teams: list[TeamSeed],
    results: list[MatchResult],
    *,
    win_table_points: int = 2,
    loss_table_points: int = 0,
    manual_rankings: dict[str, int] | None = None,
    group_complete: bool = False,
    qualify_count: int = 4,
) -> LeaderboardResult:
    manual_rankings = manual_rankings or {}
    seeds = {t.team_id: t.seed for t in teams}
    all_ids = {t.team_id for t in teams}
    overall = _aggregate(all_ids, results)
    explanation: list[str] = []

    # Primary order: wins desc, then point difference desc.
    primary = sorted(all_ids, key=lambda t: (-overall[t].wins, -overall[t].diff))

    # Group teams equal on (wins, diff) — these need tie resolution.
    ordered: list[str] = []
    i = 0
    while i < len(primary):
        j = i
        key = (overall[primary[i]].wins, overall[primary[i]].diff)
        while j < len(primary) and (overall[primary[j]].wins, overall[primary[j]].diff) == key:
            j += 1
        group = primary[i:j]
        resolved, statuses = _resolve_group(group, results, overall, seeds, manual_rankings)
        if len(group) > 1:
            explanation.append(_explain(group, statuses, key))
        ordered.extend(resolved)
        i = j

    standings: list[Standing] = []
    statuses_by_team = _all_statuses(primary, results, overall, seeds, manual_rankings)
    for rank, tid in enumerate(ordered, start=1):
        s = overall[tid]
        qual = "NONE"
        if group_complete:
            qual = "QUALIFIED" if rank <= qualify_count else "ELIMINATED"
        else:
            qual = "PROVISIONAL"
        standings.append(
            Standing(
                team_id=tid,
                played=s.played,
                wins=s.wins,
                losses=s.losses,
                points_for=s.points_for,
                points_against=s.points_against,
                point_difference=s.diff,
                table_points=s.wins * win_table_points + s.losses * loss_table_points,
                rank=rank,
                tie_status=statuses_by_team.get(tid, "CLEAR"),
                qualification_status=qual,
            )
        )
    return LeaderboardResult(standings=standings, explanation=explanation)


def _full_key(
    t: str,
    mini: dict[str, Stats],
    overall: dict[str, Stats],
    seeds: dict[str, int | None],
    manual: dict[str, int],
) -> tuple:
    return (
        -mini[t].wins,
        -mini[t].diff,
        -mini[t].points_for,
        -overall[t].points_for,
        overall[t].points_against,
        seeds.get(t) if seeds.get(t) is not None else INF,
        manual.get(t, INF),
    )


def _resolve_group(
    group: list[str],
    results: list[MatchResult],
    overall: dict[str, Stats],
    seeds: dict[str, int | None],
    manual: dict[str, int],
) -> tuple[list[str], dict[str, str]]:
    if len(group) == 1:
        return group, {group[0]: "CLEAR"}

    members = set(group)
    mini = _aggregate(members, [r for r in results if r.team_a in members and r.team_b in members])

    ordered = sorted(group, key=lambda t: _full_key(t, mini, overall, seeds, manual))

    mini_keys = [(mini[t].wins, mini[t].diff, mini[t].points_for) for t in group]
    mini_distinct = len(set(mini_keys)) == len(group)

    statuses: dict[str, str] = {}
    # Members sharing an identical full key are genuinely unresolved.
    full_keys = {t: _full_key(t, mini, overall, seeds, manual) for t in group}
    seen: dict[tuple, list[str]] = {}
    for t in group:
        seen.setdefault(full_keys[t], []).append(t)

    if mini_distinct:
        method = "HEAD_TO_HEAD" if len(group) == 2 else "MINI_TABLE"
        for t in group:
            statuses[t] = method
    else:
        for _key, members_with_key in seen.items():
            if len(members_with_key) > 1:
                for t in members_with_key:
                    statuses[t] = "UNRESOLVED"
            else:
                t = members_with_key[0]
                statuses[t] = "MANUAL" if t in manual else "TIEBREAK"

    return ordered, statuses


def _all_statuses(
    primary: list[str],
    results: list[MatchResult],
    overall: dict[str, Stats],
    seeds: dict[str, int | None],
    manual: dict[str, int],
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    i = 0
    while i < len(primary):
        j = i
        key = (overall[primary[i]].wins, overall[primary[i]].diff)
        while j < len(primary) and (overall[primary[j]].wins, overall[primary[j]].diff) == key:
            j += 1
        group = primary[i:j]
        _, st = _resolve_group(group, results, overall, seeds, manual)
        statuses.update(st)
        i = j
    return statuses


def _explain(group: list[str], statuses: dict[str, str], key: tuple) -> str:
    wins, diff = key
    method = statuses.get(group[0], "CLEAR")
    label = {
        "HEAD_TO_HEAD": "resolved by head-to-head",
        "MINI_TABLE": "resolved by mini-table among tied teams",
        "TIEBREAK": "resolved by points-for / against / seed",
        "MANUAL": "resolved by manual administrator ranking",
        "UNRESOLVED": "UNRESOLVED — needs manual resolution",
    }.get(method, "resolved")
    return f"Teams [{', '.join(group)}] tied on {wins} wins / {diff:+d} diff — {label}."


def has_unresolved_top_tie(result: LeaderboardResult, qualify_count: int = 4) -> bool:
    """True if any unresolved tie touches the qualification boundary (top N)."""
    for s in result.standings:
        if s.tie_status == "UNRESOLVED" and s.rank <= qualify_count + 1:
            return True
    return False
