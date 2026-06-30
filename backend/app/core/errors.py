from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppError(HTTPException):
    """Domain error carrying a machine-readable code and optional details."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.details = details or {}


def _error_body(code: str, message: str, details: dict[str, Any], request: Request) -> dict:
    request_id = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id", ""
    )
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.message, exc.details, request),
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # Map plain HTTPExceptions (e.g. from dependencies) into the same envelope.
    code = {
        status.HTTP_401_UNAUTHORIZED: "UNAUTHENTICATED",
        status.HTTP_403_FORBIDDEN: "FORBIDDEN",
        status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    }.get(exc.status_code, "HTTP_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(code, str(exc.detail), {}, request),
    )


# Common domain errors -------------------------------------------------------


def email_already_registered() -> AppError:
    return AppError(status.HTTP_409_CONFLICT, "EMAIL_ALREADY_REGISTERED", "Email is already registered.")


def invalid_credentials() -> AppError:
    return AppError(status.HTTP_401_UNAUTHORIZED, "INVALID_CREDENTIALS", "Invalid email or password.")


def email_not_verified() -> AppError:
    return AppError(status.HTTP_403_FORBIDDEN, "EMAIL_NOT_VERIFIED", "Email address is not verified.")


def account_not_active() -> AppError:
    return AppError(status.HTTP_403_FORBIDDEN, "ACCOUNT_NOT_ACTIVE", "Account is not active.")


def invalid_token(message: str = "Token is invalid or expired.") -> AppError:
    return AppError(status.HTTP_400_BAD_REQUEST, "INVALID_TOKEN", message)


def player_not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "PLAYER_NOT_FOUND", "Player not found.")


def reason_required() -> AppError:
    return AppError(422, "REASON_REQUIRED", "A reason is required.")


def invalid_skill_rating(message: str) -> AppError:
    return AppError(422, "INVALID_SKILL_RATING", message)


# Tournaments / teams --------------------------------------------------------


def tournament_not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "TOURNAMENT_NOT_FOUND", "Tournament not found.")


def tournament_not_editable() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "TOURNAMENT_NOT_EDITABLE",
        "The tournament can no longer be edited in its current state.",
    )


def invalid_transition(current: str, target: str) -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "INVALID_TOURNAMENT_TRANSITION",
        f"Cannot transition from {current} to {target}.",
        {"current": current, "target": target},
    )


def team_not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "TEAM_NOT_FOUND", "Team not found.")


def team_name_taken(name: str) -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "TEAM_NAME_TAKEN",
        "A team with that name already exists in this tournament.",
        {"name": name},
    )


def team_already_full() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "TEAM_ALREADY_FULL",
        "A team may have at most two players.",
    )


def player_not_approved() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "PLAYER_NOT_APPROVED",
        "Only approved players can be added to a team.",
    )


def player_already_on_team() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "PLAYER_ALREADY_ON_TEAM",
        "This player is already on a team in this tournament.",
    )


# Schedule / matches ---------------------------------------------------------


def schedule_already_generated() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT, "SCHEDULE_ALREADY_GENERATED", "The schedule already exists."
    )


def team_requires_two_players() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "TEAM_REQUIRES_TWO_PLAYERS",
        "Every team must have exactly two approved players before scheduling.",
    )


def invalid_exhibition(message: str) -> AppError:
    return AppError(422, "INVALID_EXHIBITION", message)


def not_enough_teams(minimum: int) -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "NOT_ENOUGH_TEAMS",
        f"At least {minimum} teams are required.",
        {"minimum": minimum},
    )


def match_not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "MATCH_NOT_FOUND", "Match not found.")


def invalid_match_score(message: str, details: dict | None = None) -> AppError:
    return AppError(422, "INVALID_MATCH_SCORE", message, details)


def match_version_conflict(latest_version: int) -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "MATCH_VERSION_CONFLICT",
        "The match was modified by someone else. Reload and retry.",
        {"latest_version": latest_version},
    )


def match_not_editable(message: str = "This match cannot be modified in its current state.") -> AppError:
    return AppError(status.HTTP_409_CONFLICT, "MATCH_NOT_EDITABLE", message)


def dependent_match_already_started() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "DEPENDENT_MATCH_ALREADY_STARTED",
        "A dependent bracket match has already started; reset dependents to proceed.",
    )


def group_stage_incomplete() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT, "GROUP_STAGE_INCOMPLETE", "Not all group matches are complete."
    )


def qualification_tie_unresolved() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "QUALIFICATION_TIE_UNRESOLVED",
        "A tie affecting the top four is unresolved.",
    )


def bracket_already_generated() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT, "BRACKET_ALREADY_GENERATED", "The bracket already exists."
    )


# Finalization ---------------------------------------------------------------


def tournament_not_ready_to_finalize() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "TOURNAMENT_NOT_READY_TO_FINALIZE",
        "The tournament cannot be finalized until the Final is complete.",
    )


def tournament_not_finalized() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT, "TOURNAMENT_NOT_FINALIZED", "The tournament is not finalized."
    )


# Registrations --------------------------------------------------------------


def registration_not_open() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "REGISTRATION_NOT_OPEN",
        "This tournament is not open for registration.",
    )


def already_registered() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT, "ALREADY_REGISTERED", "You have already registered for this tournament."
    )


def registration_not_found() -> AppError:
    return AppError(
        status.HTTP_404_NOT_FOUND, "REGISTRATION_NOT_FOUND", "Registration not found."
    )


# Predictions ----------------------------------------------------------------


def match_not_predictable() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "MATCH_NOT_PREDICTABLE",
        "Predictions are closed for this match.",
    )


def invalid_prediction() -> AppError:
    return AppError(
        422, "INVALID_PREDICTION", "Pick must be one of the two teams in the match."
    )


def prediction_locked() -> AppError:
    return AppError(
        status.HTTP_409_CONFLICT,
        "PREDICTION_LOCKED",
        "Your pick is locked in and can't be changed.",
    )
