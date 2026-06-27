import re
import secrets
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import AuditSeverity, TournamentStatus, TournamentVisibility
from app.db.models.tournament import Tournament
from app.db.models.tournament_result import TournamentResult
from app.db.models.user import User
from app.domain import tournament_state
from app.schemas.tournament import TournamentCreate, TournamentUpdate
from app.services.audit_service import AuditService


def _slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48] or "tournament"
    return f"{base}-{secrets.token_hex(3)}"


class TournamentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    # -- reads -------------------------------------------------------------

    def get(self, tournament_id: uuid.UUID) -> Tournament:
        t = self.db.get(Tournament, tournament_id)
        if t is None:
            raise errors.tournament_not_found()
        return t

    def get_visible(self, tournament_id: uuid.UUID, *, is_admin: bool) -> Tournament:
        t = self.get(tournament_id)
        if not is_admin and t.visibility == TournamentVisibility.PRIVATE:
            # Hide existence of private tournaments from non-admins.
            raise errors.tournament_not_found()
        return t

    def list_visible(self, *, is_admin: bool) -> list[Tournament]:
        stmt = select(Tournament).order_by(Tournament.created_at.desc())
        if not is_admin:
            # Guests/players only see public tournaments in listings.
            stmt = stmt.where(Tournament.visibility == TournamentVisibility.PUBLIC)
        return list(self.db.execute(stmt).scalars())

    # -- writes ------------------------------------------------------------

    def create(self, *, data: TournamentCreate, actor: User, meta: dict) -> Tournament:
        t = Tournament(
            name=data.name.strip(),
            slug=_slugify(data.name),
            description=data.description,
            location=data.location,
            start_at=data.start_at,
            end_at=data.end_at,
            visibility=data.visibility,
            status=TournamentStatus.DRAFT,
            target_points=data.scoring.target_points,
            win_by_two=data.scoring.win_by_two,
            maximum_points=data.scoring.maximum_points,
            win_table_points=data.scoring.win_table_points,
            loss_table_points=data.scoring.loss_table_points,
            created_by=actor.id,
            version=1,
        )
        self.db.add(t)
        self.db.flush()
        self.audit.record(
            actor_user_id=actor.id,
            action="tournament.create",
            entity_type="tournament",
            entity_id=str(t.id),
            after_data={"name": t.name, "slug": t.slug},
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(t)
        return t

    def update(
        self, *, tournament_id: uuid.UUID, data: TournamentUpdate, actor: User, meta: dict
    ) -> Tournament:
        t = self.get(tournament_id)
        if not tournament_state.is_editable(t.status):
            raise errors.tournament_not_editable()

        before = {
            "name": t.name,
            "visibility": t.visibility.value,
            "target_points": t.target_points,
            "win_by_two": t.win_by_two,
        }

        if data.name is not None:
            t.name = data.name.strip()
        if data.description is not None:
            t.description = data.description
        if data.location is not None:
            t.location = data.location
        if data.start_at is not None:
            t.start_at = data.start_at
        if data.end_at is not None:
            t.end_at = data.end_at
        if data.visibility is not None:
            t.visibility = data.visibility
        if data.scoring is not None:
            t.target_points = data.scoring.target_points
            t.win_by_two = data.scoring.win_by_two
            t.maximum_points = data.scoring.maximum_points
            t.win_table_points = data.scoring.win_table_points
            t.loss_table_points = data.scoring.loss_table_points

        t.version += 1
        self.audit.record(
            actor_user_id=actor.id,
            action="tournament.update",
            entity_type="tournament",
            entity_id=str(t.id),
            before_data=before,
            after_data={
                "name": t.name,
                "visibility": t.visibility.value,
                "target_points": t.target_points,
                "win_by_two": t.win_by_two,
            },
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(t)
        return t

    def transition(
        self,
        *,
        tournament_id: uuid.UUID,
        target: TournamentStatus,
        reason: str | None,
        actor: User,
        meta: dict,
    ) -> Tournament:
        t = self.get(tournament_id)
        if not tournament_state.is_manual_transition(target) or not tournament_state.can_transition(
            t.status, target
        ):
            raise errors.invalid_transition(t.status.value, target.value)

        before = t.status
        t.status = target
        self.audit.record(
            actor_user_id=actor.id,
            action="tournament.transition",
            entity_type="tournament",
            entity_id=str(t.id),
            before_data={"status": before.value},
            after_data={"status": target.value},
            reason=reason,
            severity=AuditSeverity.WARNING
            if target == TournamentStatus.CANCELLED
            else AuditSeverity.INFO,
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(t)
        return t

    def finalize(self, *, tournament_id: uuid.UUID, actor: User, meta: dict) -> Tournament:
        from app.services.bracket_service import BracketService
        from app.services.leaderboard_service import LeaderboardService
        from app.services.rating_service import RatingService

        t = self.get(tournament_id)
        if t.status != TournamentStatus.COMPLETED:
            raise errors.tournament_not_ready_to_finalize()

        lb_result, names, _ = LeaderboardService(self.db).compute(tournament_id)
        bracket_matches, placements = BracketService(self.db).get_bracket(tournament_id)
        if len(placements) < 4:
            raise errors.tournament_not_ready_to_finalize()

        rs = RatingService(self.db)
        rs.apply_placement_bonuses(tournament_id, placements)
        rs.snapshot_end(tournament_id)

        place_to_team = {place: tid for tid, place in placements.items()}
        final_lb = [
            {
                "rank": s.rank, "team_id": s.team_id, "team_name": names.get(s.team_id, "?"),
                "wins": s.wins, "losses": s.losses, "table_points": s.table_points,
                "points_for": s.points_for, "points_against": s.points_against,
                "point_difference": s.point_difference,
            }
            for s in lb_result.standings
        ]
        final_bracket = {
            "matches": [
                {
                    "stage": m.stage.value,
                    "team_a": m.team_a.name if m.team_a else None,
                    "team_b": m.team_b.name if m.team_b else None,
                    "team_a_score": m.team_a_score, "team_b_score": m.team_b_score,
                    "winner_team_id": str(m.winner_team_id) if m.winner_team_id else None,
                }
                for m in bracket_matches
            ],
            "placements": [
                {"place": p, "team_id": tid, "team_name": names.get(tid, "?")}
                for tid, p in sorted(placements.items(), key=lambda kv: kv[1])
            ],
        }

        result = TournamentResult(
            tournament_id=tournament_id,
            champion_team_id=uuid.UUID(place_to_team[1]) if 1 in place_to_team else None,
            runner_up_team_id=uuid.UUID(place_to_team[2]) if 2 in place_to_team else None,
            third_place_team_id=uuid.UUID(place_to_team[3]) if 3 in place_to_team else None,
            fourth_place_team_id=uuid.UUID(place_to_team[4]) if 4 in place_to_team else None,
            final_group_leaderboard={"standings": final_lb},
            final_bracket=final_bracket,
            finalized_at=datetime.now(tz=UTC),
            finalized_by=actor.id,
        )
        self.db.add(result)

        t.status = TournamentStatus.FINALIZED
        t.finalized_at = datetime.now(tz=UTC)
        t.rating_status = "FINALIZED"
        self.audit.record(
            actor_user_id=actor.id, action="tournament.finalize", entity_type="tournament",
            entity_id=str(tournament_id), after_data={"champion": place_to_team.get(1)},
            ip_address=meta.get("ip_address"), user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(t)
        return t

    def reopen(self, *, tournament_id: uuid.UUID, actor: User, meta: dict) -> Tournament:
        from app.services.rating_service import RatingService

        t = self.get(tournament_id)
        if t.status != TournamentStatus.FINALIZED:
            raise errors.tournament_not_finalized()

        RatingService(self.db).revert_placement_bonuses(tournament_id)
        result = self.db.execute(
            select(TournamentResult).where(TournamentResult.tournament_id == tournament_id)
        ).scalar_one_or_none()
        if result is not None:
            self.db.delete(result)

        t.status = TournamentStatus.COMPLETED
        t.finalized_at = None
        t.rating_status = None
        self.audit.record(
            actor_user_id=actor.id, action="tournament.reopen", entity_type="tournament",
            entity_id=str(tournament_id), severity=AuditSeverity.CRITICAL,
            ip_address=meta.get("ip_address"), user_agent=meta.get("user_agent"),
        )
        self.db.commit()
        self.db.refresh(t)
        return t

    def delete(self, *, tournament_id: uuid.UUID, actor: User, meta: dict) -> None:
        t = self.get(tournament_id)
        # Hard delete only before scheduling (no matches/results exist yet).
        deletable = {
            TournamentStatus.DRAFT,
            TournamentStatus.REGISTRATION_OPEN,
            TournamentStatus.REGISTRATION_CLOSED,
        }
        if t.status not in deletable:
            raise errors.tournament_not_editable()
        self.audit.record(
            actor_user_id=actor.id,
            action="tournament.delete",
            entity_type="tournament",
            entity_id=str(t.id),
            before_data={"name": t.name, "status": t.status.value},
            severity=AuditSeverity.WARNING,
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent"),
        )
        self.db.delete(t)
        self.db.commit()
