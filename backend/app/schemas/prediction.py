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


class MatchOddsOut(BaseModel):
    match_id: uuid.UUID
    team_a_prob: float
    team_b_prob: float
    team_a_points: int  # points if you pick A and it's right
    team_b_points: int
