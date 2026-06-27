import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.enums import MatchStatus, RatingEventType, SnapshotType
from app.db.models.match import Match
from app.db.models.player_profile import PlayerProfile
from app.db.models.rating_config import RatingConfig
from app.db.models.rating_event import RatingEvent
from app.db.models.rating_snapshot import RatingSnapshot
from app.db.models.team_member import TeamMember
from app.domain import rating as rt


class RatingService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # -- config ------------------------------------------------------------

    def get_config_row(self) -> RatingConfig:
        row = self.db.execute(
            select(RatingConfig).order_by(RatingConfig.effective_from.desc())
        ).scalars().first()
        if row is None:
            row = RatingConfig()
            self.db.add(row)
            self.db.flush()
        return row

    def get_config(self) -> rt.RatingConfigValues:
        r = self.get_config_row()
        return rt.RatingConfigValues(
            starting_rating=r.starting_rating,
            rating_floor=r.rating_floor,
            group_k=r.group_k,
            qf1_k=r.qf1_k,
            qf2_k=r.qf2_k,
            qf3_k=r.qf3_k,
            final_k=r.final_k,
            champion_bonus=r.champion_bonus,
            runner_up_bonus=r.runner_up_bonus,
            third_place_bonus=r.third_place_bonus,
        )

    # -- helpers -----------------------------------------------------------

    def _team_player_ids(self, team_id: uuid.UUID | None) -> list[uuid.UUID]:
        if team_id is None:
            return []
        return list(
            self.db.execute(
                select(TeamMember.player_id).where(TeamMember.team_id == team_id)
            ).scalars()
        )

    def _team_avg_rating(self, player_ids: list[uuid.UUID]) -> float:
        if not player_ids:
            return 1000.0
        ratings = [
            self.db.get(PlayerProfile, pid).current_rating for pid in player_ids  # type: ignore[union-attr]
        ]
        return sum(ratings) / len(ratings)

    def _next_sequence(self, tournament_id: uuid.UUID) -> int:
        current = self.db.execute(
            select(func.coalesce(func.max(RatingEvent.sequence_number), 0)).where(
                RatingEvent.tournament_id == tournament_id
            )
        ).scalar_one()
        return int(current) + 1

    def _record(
        self, *, player_id: uuid.UUID, tournament_id: uuid.UUID, match_id: uuid.UUID | None,
        event_type: RatingEventType, delta: int, calc: dict, sequence: int, reason: str | None = None,
    ) -> None:
        profile = self.db.get(PlayerProfile, player_id)
        if profile is None:
            return
        cfg = self.get_config()
        before = profile.current_rating
        after = rt.apply_floor(before + delta, cfg)
        self.db.add(
            RatingEvent(
                player_id=player_id, tournament_id=tournament_id, match_id=match_id,
                event_type=event_type, rating_before=before, delta=after - before,
                rating_after=after, calculation_data=calc, sequence_number=sequence, reason=reason,
            )
        )
        profile.current_rating = after
        if after > profile.highest_rating:
            profile.highest_rating = after

    # -- snapshots ---------------------------------------------------------

    def snapshot_start(self, tournament_id: uuid.UUID) -> None:
        existing = self.db.execute(
            select(RatingSnapshot.player_id).where(
                RatingSnapshot.tournament_id == tournament_id,
                RatingSnapshot.snapshot_type == SnapshotType.TOURNAMENT_START,
            )
        ).scalars().all()
        if existing:
            return
        player_ids = set(
            self.db.execute(
                select(TeamMember.player_id).where(TeamMember.tournament_id == tournament_id)
            ).scalars()
        )
        for pid in player_ids:
            profile = self.db.get(PlayerProfile, pid)
            if profile is not None:
                self.db.add(
                    RatingSnapshot(
                        player_id=pid, tournament_id=tournament_id,
                        snapshot_type=SnapshotType.TOURNAMENT_START, rating=profile.current_rating,
                    )
                )

    def snapshot_end(self, tournament_id: uuid.UUID) -> None:
        player_ids = set(
            self.db.execute(
                select(TeamMember.player_id).where(TeamMember.tournament_id == tournament_id)
            ).scalars()
        )
        for pid in player_ids:
            profile = self.db.get(PlayerProfile, pid)
            if profile is not None:
                self.db.add(
                    RatingSnapshot(
                        player_id=pid, tournament_id=tournament_id,
                        snapshot_type=SnapshotType.TOURNAMENT_END, rating=profile.current_rating,
                    )
                )

    # -- match ratings -----------------------------------------------------

    def apply_match(self, match: Match) -> None:
        if match.status != MatchStatus.COMPLETED or match.winner_team_id is None:
            return
        cfg = self.get_config()
        a_players = self._team_player_ids(match.team_a_id)
        b_players = self._team_player_ids(match.team_b_id)
        a_rating = self._team_avg_rating(a_players)
        b_rating = self._team_avg_rating(b_players)
        winner_is_a = match.winner_team_id == match.team_a_id
        k = rt.stage_k(match.stage, cfg)
        deltas = rt.match_deltas(
            team_a_rating=a_rating, team_b_rating=b_rating, winner_is_a=winner_is_a, k=k
        )
        seq = self._next_sequence(match.tournament_id)
        calc_base = {
            "team_a_rating": a_rating, "team_b_rating": b_rating,
            "expected_a": round(deltas.expected_a, 4), "expected_b": round(deltas.expected_b, 4),
            "k": k, "stage": match.stage.value,
        }
        for pid in a_players:
            self._record(
                player_id=pid, tournament_id=match.tournament_id, match_id=match.id,
                event_type=RatingEventType.MATCH_RESULT, delta=deltas.delta_a,
                calc={**calc_base, "actual": 1.0 if winner_is_a else 0.0}, sequence=seq,
            )
        for pid in b_players:
            self._record(
                player_id=pid, tournament_id=match.tournament_id, match_id=match.id,
                event_type=RatingEventType.MATCH_RESULT, delta=deltas.delta_b,
                calc={**calc_base, "actual": 0.0 if winner_is_a else 1.0}, sequence=seq,
            )
        self.db.flush()

    # -- placement bonuses -------------------------------------------------

    def apply_placement_bonuses(self, tournament_id: uuid.UUID, placements: dict[str, int]) -> None:
        cfg = self.get_config()
        seq = self._next_sequence(tournament_id)
        for team_id, place in placements.items():
            bonus = rt.placement_bonus(place, cfg)
            if bonus == 0:
                continue
            for pid in self._team_player_ids(uuid.UUID(team_id)):
                self._record(
                    player_id=pid, tournament_id=tournament_id, match_id=None,
                    event_type=RatingEventType.TOURNAMENT_PLACEMENT_BONUS, delta=bonus,
                    calc={"place": place, "bonus": bonus}, sequence=seq,
                    reason=f"Placement bonus (place {place})",
                )
        self.db.flush()

    def revert_placement_bonuses(self, tournament_id: uuid.UUID) -> None:
        """Undo placement bonuses (used on reopen): subtract each bonus delta and
        supersede the event."""
        events = self.db.execute(
            select(RatingEvent).where(
                RatingEvent.tournament_id == tournament_id,
                RatingEvent.event_type == RatingEventType.TOURNAMENT_PLACEMENT_BONUS,
                RatingEvent.is_superseded.is_(False),
            )
        ).scalars().all()
        cfg = self.get_config()
        for e in events:
            profile = self.db.get(PlayerProfile, e.player_id)
            if profile is not None:
                profile.current_rating = rt.apply_floor(profile.current_rating - e.delta, cfg)
            e.is_superseded = True
        self.db.flush()

    def admin_adjust(
        self, *, player_id: uuid.UUID, delta: int, reason: str
    ) -> PlayerProfile | None:
        profile = self.db.get(PlayerProfile, player_id)
        if profile is None:
            return None
        cfg = self.get_config()
        before = profile.current_rating
        after = rt.apply_floor(before + delta, cfg)
        self.db.add(
            RatingEvent(
                player_id=player_id, tournament_id=None, match_id=None,
                event_type=RatingEventType.ADMIN_ADJUSTMENT, rating_before=before,
                delta=after - before, rating_after=after, calculation_data={"manual": True},
                sequence_number=0, reason=reason,
            )
        )
        profile.current_rating = after
        if after > profile.highest_rating:
            profile.highest_rating = after
        self.db.commit()
        return profile

    # -- replay ------------------------------------------------------------

    def replay(self, tournament_id: uuid.UUID) -> None:
        """Restore players to their tournament-start ratings, supersede prior
        events for this tournament, and replay completed matches chronologically.
        (MVP: full active-tournament replay from start snapshots.)"""
        snapshots = self.db.execute(
            select(RatingSnapshot).where(
                RatingSnapshot.tournament_id == tournament_id,
                RatingSnapshot.snapshot_type == SnapshotType.TOURNAMENT_START,
            )
        ).scalars().all()
        if not snapshots:
            return

        # Supersede existing (non-superseded) events for this tournament.
        prior = self.db.execute(
            select(RatingEvent).where(
                RatingEvent.tournament_id == tournament_id,
                RatingEvent.is_superseded.is_(False),
            )
        ).scalars().all()
        for e in prior:
            e.is_superseded = True

        # Restore current ratings to the start snapshot.
        for snap in snapshots:
            profile = self.db.get(PlayerProfile, snap.player_id)
            if profile is not None:
                profile.current_rating = snap.rating
        self.db.flush()

        # Replay completed matches in chronological order.
        matches = self.db.execute(
            select(Match).where(
                Match.tournament_id == tournament_id,
                Match.status == MatchStatus.COMPLETED,
            ).order_by(Match.completed_at, Match.display_order)
        ).scalars().all()
        for m in matches:
            self.apply_match(m)

    # -- queries -----------------------------------------------------------

    def player_events(self, player_id: uuid.UUID) -> list[RatingEvent]:
        return list(
            self.db.execute(
                select(RatingEvent)
                .where(RatingEvent.player_id == player_id, RatingEvent.is_superseded.is_(False))
                .order_by(RatingEvent.created_at, RatingEvent.sequence_number)
            ).scalars()
        )
