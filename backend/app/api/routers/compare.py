from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.compare import TeamCompareOut, TeamCompareRequest
from app.services.player_service import PlayerService

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("/teams", response_model=TeamCompareOut)
def compare_teams(
    body: TeamCompareRequest,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TeamCompareOut:
    result = PlayerService(db).compare_pairs(body.team_a, body.team_b)
    return TeamCompareOut(**result)
