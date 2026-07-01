from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.match import LiveMatchOut
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/live", tags=["live"])


@router.get("", response_model=list[LiveMatchOut])
def list_live(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[LiveMatchOut]:
    return [
        LiveMatchOut(
            id=m.id,
            tournament_id=m.tournament_id,
            is_exhibition=t.is_exhibition,
            context_name="Exhibition" if t.is_exhibition else t.name,
            team_a_name=m.team_a.name if m.team_a else None,
            team_b_name=m.team_b.name if m.team_b else None,
            team_a_score=m.team_a_score,
            team_b_score=m.team_b_score,
            status=m.status,
            target_points=t.target_points,
        )
        for m, t in ScoringService(db).live_matches()
    ]
