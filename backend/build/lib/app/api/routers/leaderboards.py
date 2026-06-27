import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user, get_request_meta, is_admin_user, require_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import MessageResponse
from app.schemas.leaderboard import (
    ExplanationOut,
    LeaderboardOut,
    ResolveTieRequest,
    StandingOut,
)
from app.services.leaderboard_service import LeaderboardService
from app.services.tournament_service import TournamentService

router = APIRouter(prefix="/tournaments/{tournament_id}/leaderboard", tags=["leaderboard"])


@router.get("", response_model=LeaderboardOut)
def get_leaderboard(
    tournament_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> LeaderboardOut:
    TournamentService(db).get_visible(tournament_id, is_admin=is_admin_user(viewer))
    result, names, group_complete = LeaderboardService(db).compute(tournament_id)
    standings = [
        StandingOut(
            rank=s.rank,
            team_id=uuid.UUID(s.team_id),
            team_name=names.get(s.team_id, "?"),
            played=s.played,
            wins=s.wins,
            losses=s.losses,
            table_points=s.table_points,
            points_for=s.points_for,
            points_against=s.points_against,
            point_difference=s.point_difference,
            tie_status=s.tie_status,
            qualification_status=s.qualification_status,
        )
        for s in result.standings
    ]
    return LeaderboardOut(group_complete=group_complete, standings=standings)


@router.get("/explanation", response_model=ExplanationOut)
def get_explanation(
    tournament_id: uuid.UUID,
    viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ExplanationOut:
    TournamentService(db).get_visible(tournament_id, is_admin=is_admin_user(viewer))
    result, _, _ = LeaderboardService(db).compute(tournament_id)
    return ExplanationOut(explanation=result.explanation)


@router.post("/resolve-tie", response_model=MessageResponse)
def resolve_tie(
    tournament_id: uuid.UUID,
    body: ResolveTieRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> MessageResponse:
    LeaderboardService(db).resolve_tie(
        tournament_id=tournament_id, ordering=body.ordering, reason=body.reason, actor=actor, meta=meta
    )
    return MessageResponse(message="Tie resolution saved.")
