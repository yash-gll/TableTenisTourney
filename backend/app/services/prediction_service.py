import uuid

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.orm import Session

from app.core import errors
from app.db.models.enums import MatchStatus
from app.db.models.match import Match
from app.db.models.match_prediction import MatchPrediction
from app.db.models.player_profile import PlayerProfile

CLOSED_STATES = {MatchStatus.COMPLETED, MatchStatus.CANCELLED, MatchStatus.VOID}
POINTS_PER_CORRECT = 1


class PredictionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def predict(
        self, *, match_id: uuid.UUID, player_id: uuid.UUID, winner_team_id: uuid.UUID
    ) -> MatchPrediction:
        match = self.db.get(Match, match_id)
        if match is None:
            raise errors.match_not_found()
        if match.status in CLOSED_STATES:
            raise errors.match_not_predictable()
        if winner_team_id not in (match.team_a_id, match.team_b_id) or winner_team_id is None:
            raise errors.invalid_prediction()

        existing = self.db.execute(
            select(MatchPrediction).where(
                MatchPrediction.match_id == match_id, MatchPrediction.player_id == player_id
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.predicted_winner_team_id = winner_team_id
            existing.is_correct = None
            existing.points_awarded = 0
            self.db.commit()
            self.db.refresh(existing)
            return existing

        pred = MatchPrediction(
            match_id=match_id,
            tournament_id=match.tournament_id,
            player_id=player_id,
            predicted_winner_team_id=winner_team_id,
        )
        self.db.add(pred)
        self.db.commit()
        self.db.refresh(pred)
        return pred

    def my_predictions(
        self, tournament_id: uuid.UUID, player_id: uuid.UUID
    ) -> list[MatchPrediction]:
        return list(
            self.db.execute(
                select(MatchPrediction).where(
                    MatchPrediction.tournament_id == tournament_id,
                    MatchPrediction.player_id == player_id,
                )
            ).scalars()
        )

    def evaluate_match(self, match: Match) -> None:
        """Grade all predictions for a match against its (current) winner."""
        if match.winner_team_id is None:
            return
        preds = self.db.execute(
            select(MatchPrediction).where(MatchPrediction.match_id == match.id)
        ).scalars()
        for p in preds:
            p.is_correct = p.predicted_winner_team_id == match.winner_team_id
            p.points_awarded = POINTS_PER_CORRECT if p.is_correct else 0
        self.db.flush()

    def leaderboard(self, tournament_id: uuid.UUID) -> list[dict]:
        rows = self.db.execute(
            select(
                MatchPrediction.player_id,
                PlayerProfile.display_name,
                func.coalesce(func.sum(MatchPrediction.points_awarded), 0).label("points"),
                func.count(MatchPrediction.is_correct).label("graded"),
                func.coalesce(func.sum(cast(MatchPrediction.is_correct, Integer)), 0).label("correct"),
            )
            .join(PlayerProfile, PlayerProfile.id == MatchPrediction.player_id)
            .where(MatchPrediction.tournament_id == tournament_id)
            .group_by(MatchPrediction.player_id, PlayerProfile.display_name)
            .order_by(func.coalesce(func.sum(MatchPrediction.points_awarded), 0).desc())
        ).all()
        return [
            {
                "player_id": pid,
                "display_name": name,
                "points": int(points),
                "correct": int(correct),
                "total": int(graded),
            }
            for pid, name, points, graded, correct in rows
        ]
