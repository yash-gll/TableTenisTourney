import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_request_meta, require_admin
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.mappers import to_match_out
from app.schemas.match import MatchOut
from app.services.point_service import PointService
from app.services.scoring_service import ScoringService

router = APIRouter(prefix="/matches/{match_id}/points", tags=["points"])


class LogPointRequest(BaseModel):
    player_id: uuid.UUID
    skill: str


class RunningScore(BaseModel):
    team_a: int
    team_b: int


@router.get("", response_model=RunningScore)
def running_score(match_id: uuid.UUID, db: Session = Depends(get_db)) -> RunningScore:
    return RunningScore(**PointService(db).running_score(match_id))


@router.post("", response_model=RunningScore)
def log_point(
    match_id: uuid.UUID,
    body: LogPointRequest,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RunningScore:
    score = PointService(db).log_point(
        match_id=match_id, player_id=body.player_id, skill=body.skill, actor=actor
    )
    return RunningScore(**score)


@router.delete("/last", response_model=RunningScore)
def undo_last(
    match_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RunningScore:
    return RunningScore(**PointService(db).undo_last(match_id=match_id))


@router.post("/complete", response_model=MatchOut)
def complete_from_points(
    match_id: uuid.UUID,
    expected_version: int,
    actor: User = Depends(require_admin),
    db: Session = Depends(get_db),
    meta: dict = Depends(get_request_meta),
) -> MatchOut:
    match = ScoringService(db).complete_from_points(
        match_id=match_id, expected_version=expected_version, actor=actor, meta=meta
    )
    return to_match_out(match)
