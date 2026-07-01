from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models.match import Match
from app.db.models.tournament import Tournament
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.match import LiveMatchOut, SpectatorBoard
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/live", tags=["live"])


def _to_live(m: Match, t: Tournament) -> LiveMatchOut:
    a_name = m.team_a.name if m.team_a else None
    b_name = m.team_b.name if m.team_b else None
    winner_name = None
    if m.winner_team_id == m.team_a_id:
        winner_name = a_name
    elif m.winner_team_id == m.team_b_id:
        winner_name = b_name
    return LiveMatchOut(
        id=m.id,
        tournament_id=m.tournament_id,
        is_exhibition=t.is_exhibition,
        context_name="Exhibition" if t.is_exhibition else t.name,
        team_a_name=a_name,
        team_b_name=b_name,
        team_a_score=m.team_a_score,
        team_b_score=m.team_b_score,
        status=m.status,
        target_points=t.target_points,
        winner_name=winner_name,
    )


@router.get("", response_model=SpectatorBoard)
def spectator_board(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SpectatorBoard:
    board = ScoringService(db).spectator_board()
    return SpectatorBoard(
        live=[_to_live(m, t) for m, t in board["live"]],
        upcoming=[_to_live(m, t) for m, t in board["upcoming"]],
        recent=[_to_live(m, t) for m, t in board["recent"]],
    )
