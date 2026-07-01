import uuid
from collections import defaultdict

from sqlalchemy import and_, false, func, or_, select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import ApprovalStatus, MatchStatus
from app.db.models.match import Match
from app.db.models.match_point import MatchPoint
from app.db.models.player_profile import PlayerProfile
from app.db.models.team_member import TeamMember
from app.db.models.tournament_result import TournamentResult
from app.db.models.user import User
from app.domain import skills as skills_domain
from app.domain.achievements import AchievementInput, Badge, earned_badges
from app.schemas.player import PlayerStatsOut, ProfileUpdate


class PlayerService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def update_profile(self, *, user: User, data: ProfileUpdate) -> PlayerProfile:
        profile = user.profile
        if data.display_name is not None:
            profile.display_name = data.display_name.strip()
        if data.bio is not None:
            profile.bio = data.bio
        self.db.commit()
        self.db.refresh(profile)
        return profile

    # -- public directory --------------------------------------------------

    def search(self, *, query: str | None, limit: int = 100) -> list[PlayerProfile]:
        stmt = select(PlayerProfile).where(
            PlayerProfile.approval_status == ApprovalStatus.APPROVED
        )
        if query:
            stmt = stmt.where(PlayerProfile.display_name.ilike(f"%{query.strip()}%"))
        stmt = stmt.order_by(
            PlayerProfile.current_rating.desc(), PlayerProfile.display_name
        ).limit(limit)
        return list(self.db.execute(stmt).scalars())

    def get_profile(self, player_id: uuid.UUID) -> PlayerProfile:
        profile = self.db.get(PlayerProfile, player_id)
        if profile is None:
            raise errors.player_not_found()
        return profile

    def directory(self, *, query: str | None, limit: int = 100) -> list[dict]:
        """Search results plus each player's played/wins, computed in two queries
        so the ranked list can show basic stats without opening each profile."""
        profiles = self.search(query=query, limit=limit)
        if not profiles:
            return []
        pids = [p.id for p in profiles]

        player_teams: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
        all_team_ids: set[uuid.UUID] = set()
        for pid, tid in self.db.execute(
            select(TeamMember.player_id, TeamMember.team_id).where(TeamMember.player_id.in_(pids))
        ).all():
            player_teams[pid].add(tid)
            all_team_ids.add(tid)

        played: dict[uuid.UUID, int] = defaultdict(int)
        wins: dict[uuid.UUID, int] = defaultdict(int)
        if all_team_ids:
            matches = self.db.execute(
                select(Match.team_a_id, Match.team_b_id, Match.winner_team_id).where(
                    Match.status == MatchStatus.COMPLETED,
                    or_(Match.team_a_id.in_(all_team_ids), Match.team_b_id.in_(all_team_ids)),
                )
            ).all()
            for a_id, b_id, winner in matches:
                for pid, tids in player_teams.items():
                    if a_id in tids or b_id in tids:
                        played[pid] += 1
                        if winner in tids:
                            wins[pid] += 1

        # Rally-level: points this player personally decided (won/lost), one query.
        rally_won: dict[uuid.UUID, int] = defaultdict(int)
        rally_lost: dict[uuid.UUID, int] = defaultdict(int)
        for pid, kind, count in self.db.execute(
            select(MatchPoint.player_id, MatchPoint.kind, func.count())
            .join(Match, Match.id == MatchPoint.match_id)
            .where(Match.status == MatchStatus.COMPLETED, MatchPoint.player_id.in_(pids))
            .group_by(MatchPoint.player_id, MatchPoint.kind)
        ).all():
            if kind == "WIN":
                rally_won[pid] = int(count)
            elif kind == "FAULT":
                rally_lost[pid] = int(count)

        out = []
        for p in profiles:
            pl, wn = played.get(p.id, 0), wins.get(p.id, 0)
            rw, rl = rally_won.get(p.id, 0), rally_lost.get(p.id, 0)
            rp = rw + rl
            out.append(
                {
                    "profile": p,
                    "matches_played": pl,
                    "wins": wn,
                    "losses": pl - wn,
                    "win_pct": round(wn / pl * 100, 1) if pl else 0.0,
                    "rallies_played": rp,
                    "rallies_won": rw,
                    "rallies_lost": rl,
                    "rally_win_pct": round(rw / rp * 100, 1) if rp else 0.0,
                }
            )
        return out

    def stats(self, player_id: uuid.UUID) -> PlayerStatsOut:
        team_ids = list(
            self.db.execute(
                select(TeamMember.team_id).where(TeamMember.player_id == player_id)
            ).scalars()
        )
        tournaments_played = self.db.execute(
            select(func.count(func.distinct(TeamMember.tournament_id))).where(
                TeamMember.player_id == player_id
            )
        ).scalar_one()

        if not team_ids:
            return PlayerStatsOut(
                matches_played=0, wins=0, losses=0, win_pct=0.0,
                tournaments_played=int(tournaments_played), tournament_wins=0,
            )

        played = self.db.execute(
            select(func.count()).select_from(Match).where(
                Match.status == MatchStatus.COMPLETED,
                or_(Match.team_a_id.in_(team_ids), Match.team_b_id.in_(team_ids)),
            )
        ).scalar_one()
        wins = self.db.execute(
            select(func.count()).select_from(Match).where(
                Match.status == MatchStatus.COMPLETED,
                Match.winner_team_id.in_(team_ids),
            )
        ).scalar_one()
        tournament_wins = self.db.execute(
            select(func.count()).select_from(TournamentResult).where(
                TournamentResult.champion_team_id.in_(team_ids)
            )
        ).scalar_one()

        losses = int(played) - int(wins)
        win_pct = round(int(wins) / int(played) * 100, 1) if played else 0.0
        return PlayerStatsOut(
            matches_played=int(played),
            wins=int(wins),
            losses=losses,
            win_pct=win_pct,
            tournaments_played=int(tournaments_played),
            tournament_wins=int(tournament_wins),
        )

    def _team_ids(self, player_id: uuid.UUID) -> list[uuid.UUID]:
        return list(
            self.db.execute(
                select(TeamMember.team_id).where(TeamMember.player_id == player_id)
            ).scalars()
        )

    def recent_form(self, player_id: uuid.UUID, n: int = 5) -> list[str]:
        """Most-recent-first list of 'W'/'L' for the player's last n matches."""
        team_ids = self._team_ids(player_id)
        if not team_ids:
            return []
        matches = self.db.execute(
            select(Match)
            .where(
                Match.status == MatchStatus.COMPLETED,
                or_(Match.team_a_id.in_(team_ids), Match.team_b_id.in_(team_ids)),
            )
            .order_by(Match.completed_at.desc())
            .limit(n)
        ).scalars().all()
        return ["W" if m.winner_team_id in team_ids else "L" for m in matches]

    def rivals(self, player_id: uuid.UUID) -> list[dict]:
        """Head-to-head record vs each opponent player, most-played first."""
        team_ids = set(self._team_ids(player_id))
        if not team_ids:
            return []
        matches = self.db.execute(
            select(Match).where(
                Match.status == MatchStatus.COMPLETED,
                or_(Match.team_a_id.in_(team_ids), Match.team_b_id.in_(team_ids)),
            )
        ).scalars().all()

        encounters: list[tuple[uuid.UUID, bool]] = []  # (opponent_team_id, player_won)
        opp_team_ids: set[uuid.UUID] = set()
        for m in matches:
            if m.team_a_id in team_ids and m.team_b_id is not None:
                opp = m.team_b_id
            elif m.team_b_id in team_ids and m.team_a_id is not None:
                opp = m.team_a_id
            else:
                continue
            opp_team_ids.add(opp)
            encounters.append((opp, m.winner_team_id in team_ids))
        if not opp_team_ids:
            return []

        member_rows = self.db.execute(
            select(TeamMember.team_id, PlayerProfile.id, PlayerProfile.display_name)
            .join(PlayerProfile, PlayerProfile.id == TeamMember.player_id)
            .where(TeamMember.team_id.in_(opp_team_ids))
        ).all()
        team_members: dict[uuid.UUID, list[tuple[uuid.UUID, str]]] = defaultdict(list)
        for team_id, pid, name in member_rows:
            team_members[team_id].append((pid, name))

        agg: dict[uuid.UUID, dict] = defaultdict(lambda: {"name": "", "meetings": 0, "wins": 0})
        for opp_team, won in encounters:
            for pid, name in team_members.get(opp_team, []):
                rec = agg[pid]
                rec["name"] = name
                rec["meetings"] += 1
                if won:
                    rec["wins"] += 1

        rivals = [
            {
                "opponent_id": pid,
                "opponent_name": rec["name"],
                "meetings": rec["meetings"],
                "wins": rec["wins"],
                "losses": rec["meetings"] - rec["wins"],
            }
            for pid, rec in agg.items()
        ]
        rivals.sort(key=lambda r: (-r["meetings"], -r["wins"]))
        return rivals

    # -- shot / mistake breakdown -----------------------------------------

    def player_breakdown(
        self, player_id: uuid.UUID, match_ids: set[uuid.UUID] | None = None
    ) -> dict:
        """How a player wins and loses points, from logged rallies in completed
        matches. Pass match_ids to scope it (e.g. to a pair's shared matches)."""
        stmt = (
            select(MatchPoint)
            .join(Match, Match.id == MatchPoint.match_id)
            .where(
                Match.status == MatchStatus.COMPLETED,
                or_(MatchPoint.player_id == player_id, MatchPoint.forcer_id == player_id),
            )
        )
        if match_ids is not None:
            if not match_ids:
                stmt = stmt.where(false())
            else:
                stmt = stmt.where(MatchPoint.match_id.in_(match_ids))
        rows = self.db.execute(stmt).scalars().all()

        win_by_skill = {key: 0 for key, _ in skills_domain.SKILL_ATTRIBUTES}
        faults_by_type = {key: 0 for key, _, _ in skills_domain.FAULTS}
        fault_labels = {key: label for key, label, _ in skills_domain.FAULTS}
        wins = faults = forced = unforced = points_forced = other_faults = 0
        for r in rows:
            if r.player_id == player_id:
                if r.kind == "WIN":
                    wins += 1
                    if r.skill in win_by_skill:
                        win_by_skill[r.skill] += 1
                elif r.kind == "FAULT":
                    faults += 1
                    if r.forcer_id is not None:
                        forced += 1
                    else:
                        unforced += 1
                    if r.detail and r.detail in faults_by_type:
                        faults_by_type[r.detail] += 1
                    else:
                        other_faults += 1
            if r.forcer_id == player_id:
                points_forced += 1

        faults_list = [
            {"key": k, "label": fault_labels[k], "count": faults_by_type[k]}
            for k, _, _ in skills_domain.FAULTS
        ]
        if other_faults:
            faults_list.append({"key": "other", "label": "Other", "count": other_faults})
        return {
            "player_id": player_id,
            "total_points": wins + faults,
            "wins": wins,
            "faults": faults,
            "forced_faults": forced,
            "unforced_faults": unforced,
            "points_forced": points_forced,
            "win_by_skill": [
                {"key": key, "label": label, "count": win_by_skill[key]}
                for key, label in skills_domain.SKILL_ATTRIBUTES
            ],
            "faults_by_type": faults_list,
        }

    def _pair_match_ids(self, team_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        if not team_ids:
            return set()
        return set(
            self.db.execute(
                select(Match.id).where(
                    Match.status == MatchStatus.COMPLETED,
                    or_(Match.team_a_id.in_(team_ids), Match.team_b_id.in_(team_ids)),
                )
            ).scalars()
        )

    # -- pair (team) comparison -------------------------------------------

    def _pair_team_ids(self, player_ids: list[uuid.UUID]) -> list[uuid.UUID]:
        """Team ids whose roster is *exactly* this set of players — i.e. the
        matches these players contested together as a pair (not with anyone else)."""
        n = len(player_ids)
        if n == 0:
            return []
        # Teams that contain all the given players.
        contains_all = self.db.execute(
            select(TeamMember.team_id)
            .where(TeamMember.player_id.in_(player_ids))
            .group_by(TeamMember.team_id)
            .having(func.count(func.distinct(TeamMember.player_id)) == n)
        ).scalars().all()
        if not contains_all:
            return []
        # ...and whose total roster size is exactly n (so a single-player query
        # doesn't match a doubles team that merely includes them).
        exact = self.db.execute(
            select(TeamMember.team_id)
            .where(TeamMember.team_id.in_(contains_all))
            .group_by(TeamMember.team_id)
            .having(func.count() == n)
        ).scalars().all()
        return list(exact)

    def pair_side(self, player_ids: list[uuid.UUID]) -> dict:
        profiles = [self.get_profile(pid) for pid in player_ids]  # 404 if unknown
        team_ids = set(self._pair_team_ids(player_ids))

        # Combined skills = average of the members' per-skill ratings.
        skills = []
        for key, label in skills_domain.SKILL_ATTRIBUTES:
            vals: list[int] = []
            for p in profiles:
                v = (p.skill_ratings or {}).get(key)
                if v is not None:
                    vals.append(v)
            skills.append(
                {"key": key, "label": label, "value": round(sum(vals) / len(vals)) if vals else None}
            )

        side = {
            "player_ids": [p.id for p in profiles],
            "player_names": [p.display_name for p in profiles],
            "avg_rating": round(sum(p.current_rating for p in profiles) / len(profiles)),
            "avg_peak": round(sum(p.highest_rating for p in profiles) / len(profiles)),
            "skills": skills,
            "team_ids": list(team_ids),  # internal; used for head-to-head
        }

        if not team_ids:
            side["stats"] = {
                "matches_played": 0, "wins": 0, "losses": 0, "win_pct": 0.0,
                "points_for": 0, "points_against": 0,
            }
            side["recent_form"] = []
            return side

        matches = self.db.execute(
            select(Match)
            .where(
                Match.status == MatchStatus.COMPLETED,
                or_(Match.team_a_id.in_(team_ids), Match.team_b_id.in_(team_ids)),
            )
            .order_by(Match.completed_at.desc())
        ).scalars().all()

        played = wins = pf = pa = 0
        form: list[str] = []
        for m in matches:
            is_a = m.team_a_id in team_ids
            mine = (m.team_a_score if is_a else m.team_b_score) or 0
            theirs = (m.team_b_score if is_a else m.team_a_score) or 0
            won = m.winner_team_id in team_ids
            played += 1
            pf += mine
            pa += theirs
            if won:
                wins += 1
            if len(form) < 5:
                form.append("W" if won else "L")

        side["stats"] = {
            "matches_played": played,
            "wins": wins,
            "losses": played - wins,
            "win_pct": round(wins / played * 100, 1) if played else 0.0,
            "points_for": pf,
            "points_against": pa,
        }
        side["recent_form"] = form
        return side

    def pair_head_to_head(
        self, a_team_ids: list[uuid.UUID], b_team_ids: list[uuid.UUID]
    ) -> dict:
        a, b = set(a_team_ids), set(b_team_ids)
        if not a or not b:
            return {"meetings": 0, "a_wins": 0, "b_wins": 0}
        matches = self.db.execute(
            select(Match).where(
                Match.status == MatchStatus.COMPLETED,
                or_(
                    and_(Match.team_a_id.in_(a), Match.team_b_id.in_(b)),
                    and_(Match.team_a_id.in_(b), Match.team_b_id.in_(a)),
                ),
            )
        ).scalars().all()
        meetings = a_wins = b_wins = 0
        for m in matches:
            meetings += 1
            if m.winner_team_id in a:
                a_wins += 1
            elif m.winner_team_id in b:
                b_wins += 1
        return {"meetings": meetings, "a_wins": a_wins, "b_wins": b_wins}

    def compare_pairs(
        self, a_ids: list[uuid.UUID], b_ids: list[uuid.UUID]
    ) -> dict:
        a_ids = list(dict.fromkeys(a_ids))  # dedupe, keep order
        b_ids = list(dict.fromkeys(b_ids))
        if not 1 <= len(a_ids) <= 2 or not 1 <= len(b_ids) <= 2:
            raise errors.invalid_comparison("Each team needs 1–2 players.")
        if set(a_ids) == set(b_ids):
            raise errors.invalid_comparison("Pick two different teams to compare.")
        side_a = self.pair_side(a_ids)
        side_b = self.pair_side(b_ids)
        h2h = self.pair_head_to_head(side_a["team_ids"], side_b["team_ids"])
        # Per-player breakdown within each pair's shared matches — shows who on the
        # team is winning points vs. dragging it down.
        for side, ids in ((side_a, a_ids), (side_b, b_ids)):
            match_ids = self._pair_match_ids(side["team_ids"])
            names = {p.id: p.display_name for p in (self.get_profile(pid) for pid in ids)}
            side["players"] = [
                {
                    "player_id": pid,
                    "name": names[pid],
                    "breakdown": self.player_breakdown(pid, match_ids),
                }
                for pid in ids
            ]
        return {"team_a": side_a, "team_b": side_b, "head_to_head": h2h}

    def achievements(self, player_id: uuid.UUID) -> list[Badge]:
        team_ids = list(
            self.db.execute(
                select(TeamMember.team_id).where(TeamMember.player_id == player_id)
            ).scalars()
        )
        if not team_ids:
            return earned_badges(AchievementInput(0, 0, 0, 0, 0, 0))

        results = self.db.execute(
            select(TournamentResult).where(
                or_(
                    TournamentResult.champion_team_id.in_(team_ids),
                    TournamentResult.runner_up_team_id.in_(team_ids),
                    TournamentResult.third_place_team_id.in_(team_ids),
                    TournamentResult.fourth_place_team_id.in_(team_ids),
                )
            )
        ).scalars().all()
        titles = sum(1 for r in results if r.champion_team_id in team_ids)
        finals = sum(
            1 for r in results
            if r.champion_team_id in team_ids or r.runner_up_team_id in team_ids
        )
        podiums = len(results)

        matches = self.db.execute(
            select(Match).where(
                Match.status == MatchStatus.COMPLETED,
                or_(Match.team_a_id.in_(team_ids), Match.team_b_id.in_(team_ids)),
            ).order_by(Match.completed_at)
        ).scalars().all()
        played = len(matches)
        wins = 0
        streak = longest = 0
        for m in matches:
            if m.winner_team_id in team_ids:
                wins += 1
                streak += 1
                longest = max(longest, streak)
            else:
                streak = 0

        return earned_badges(
            AchievementInput(
                titles=titles, finals_reached=finals, podiums=podiums,
                matches_played=played, wins=wins, longest_win_streak=longest,
            )
        )
