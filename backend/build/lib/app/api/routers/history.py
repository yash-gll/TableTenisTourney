import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import TournamentStatus
from app.db.models.tournament import Tournament
from app.db.models.tournament_result import TournamentResult
from app.db.session import get_db
from app.schemas.mappers import to_match_out
from app.schemas.match import MatchOut
from app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/history", tags=["history"])


def _champion_name(result: TournamentResult | None) -> str | None:
    if result is None or not result.final_bracket:
        return None
    for p in result.final_bracket.get("placements", []):
        if p.get("place") == 1:
            return p.get("team_name")
    return None


def _result(db: Session, tournament_id: uuid.UUID) -> TournamentResult | None:
    return db.execute(
        select(TournamentResult).where(TournamentResult.tournament_id == tournament_id)
    ).scalar_one_or_none()


@router.get("/tournaments")
def list_history(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.execute(
        select(Tournament)
        .where(Tournament.status == TournamentStatus.FINALIZED)
        .order_by(Tournament.finalized_at.desc())
    ).scalars()
    out = []
    for t in rows:
        result = _result(db, t.id)
        out.append(
            {
                "id": str(t.id), "name": t.name, "slug": t.slug, "location": t.location,
                "finalized_at": t.finalized_at.isoformat() if t.finalized_at else None,
                "champion_team_id": str(result.champion_team_id)
                if result and result.champion_team_id else None,
                "champion_name": _champion_name(result),
            }
        )
    return out


@router.get("/tournaments/{tournament_id}")
def history_detail(tournament_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    t = db.get(Tournament, tournament_id)
    if t is None:
        raise errors.tournament_not_found()
    result = _result(db, tournament_id)
    return {
        "id": str(t.id), "name": t.name, "slug": t.slug, "location": t.location,
        "status": t.status.value,
        "finalized_at": t.finalized_at.isoformat() if t.finalized_at else None,
        "champion_name": _champion_name(result),
        "placements": (result.final_bracket or {}).get("placements", []) if result else [],
    }


@router.get("/tournaments/{tournament_id}/leaderboard")
def history_leaderboard(tournament_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    result = _result(db, tournament_id)
    if result is None:
        raise errors.tournament_not_found()
    return result.final_group_leaderboard or {"standings": []}


@router.get("/tournaments/{tournament_id}/bracket")
def history_bracket(tournament_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    result = _result(db, tournament_id)
    if result is None:
        raise errors.tournament_not_found()
    return result.final_bracket or {"matches": [], "placements": []}


@router.get("/tournaments/{tournament_id}/matches", response_model=list[MatchOut])
def history_matches(tournament_id: uuid.UUID, db: Session = Depends(get_db)) -> list[MatchOut]:
    matches = ScheduleService(db).list_matches(tournament_id)
    return [to_match_out(m) for m in matches]
