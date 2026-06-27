"""Pure score validation and winner resolution.

The backend determines the winner from the score — the client is never trusted
to supply it.
"""

from dataclasses import dataclass
from typing import Literal

WinnerSide = Literal["A", "B"]


@dataclass(frozen=True)
class ScoringRules:
    target_points: int
    win_by_two: bool
    maximum_points: int | None = None


class InvalidScore(ValueError):
    """Raised when a score is illegal for the configured rules."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def resolve_winner(rules: ScoringRules, a: int, b: int) -> WinnerSide:
    """Validate the score against the rules and return which side won.

    Raises InvalidScore for negative scores, draws, or scores that violate the
    target/win-by-two/maximum configuration.
    """
    if a < 0 or b < 0:
        raise InvalidScore("Scores must be non-negative.")
    if a == b:
        raise InvalidScore("Draws are not allowed.")

    winner_score = max(a, b)
    loser_score = min(a, b)
    side: WinnerSide = "A" if a > b else "B"

    if not rules.win_by_two:
        # Winner must reach exactly the target; loser strictly below it.
        if winner_score != rules.target_points:
            raise InvalidScore(
                f"The winning score must be exactly {rules.target_points}."
            )
        if loser_score >= rules.target_points:
            raise InvalidScore(
                f"The losing score must be below {rules.target_points}."
            )
        return side

    # win_by_two == True
    if winner_score < rules.target_points:
        raise InvalidScore(f"The winner must reach at least {rules.target_points}.")

    lead = winner_score - loser_score
    at_cap = rules.maximum_points is not None and winner_score >= rules.maximum_points
    if rules.maximum_points is not None and winner_score > rules.maximum_points:
        raise InvalidScore(f"The score cannot exceed {rules.maximum_points}.")

    # At the configured cap a one-point win is allowed; otherwise lead must be >= 2.
    if not at_cap and lead < 2:
        raise InvalidScore("The winner must lead by at least two points.")

    return side
