import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_approved_player
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.prediction import MyPredictionOut, PredictionLeaderboardRow, PredictRequest
from app.services.prediction_service import PredictionService

router = APIRouter(tags=["predictions"])


@router.post("/matches/{match_id}/predict", response_model=MyPredictionOut)
def predict(
    match_id: uuid.UUID,
    body: PredictRequest,
    user: User = Depends(require_approved_player),
    db: Session = Depends(get_db),
) -> MyPredictionOut:
    pred = PredictionService(db).predict(
        match_id=match_id, player_id=user.profile.id, winner_team_id=body.winner_team_id
    )
    return MyPredictionOut(
        match_id=pred.match_id,
        predicted_winner_team_id=pred.predicted_winner_team_id,
        is_correct=pred.is_correct,
    )


@router.get("/tournaments/{tournament_id}/predictions/me", response_model=list[MyPredictionOut])
def my_predictions(
    tournament_id: uuid.UUID,
    user: User = Depends(require_approved_player),
    db: Session = Depends(get_db),
) -> list[MyPredictionOut]:
    preds = PredictionService(db).my_predictions(tournament_id, user.profile.id)
    return [
        MyPredictionOut(
            match_id=p.match_id,
            predicted_winner_team_id=p.predicted_winner_team_id,
            is_correct=p.is_correct,
        )
        for p in preds
    ]


@router.get(
    "/tournaments/{tournament_id}/predictions/leaderboard",
    response_model=list[PredictionLeaderboardRow],
)
def prediction_leaderboard(
    tournament_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[PredictionLeaderboardRow]:
    return [PredictionLeaderboardRow(**row) for row in PredictionService(db).leaderboard(tournament_id)]
