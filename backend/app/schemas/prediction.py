import uuid

from pydantic import BaseModel


class PredictRequest(BaseModel):
    winner_team_id: uuid.UUID


class MyPredictionOut(BaseModel):
    match_id: uuid.UUID
    predicted_winner_team_id: uuid.UUID
    is_correct: bool | None


class PredictionLeaderboardRow(BaseModel):
    player_id: uuid.UUID
    display_name: str
    points: int
    correct: int
    total: int
