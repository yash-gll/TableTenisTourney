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
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request.headers.get("x-request-id", ""),
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
    return AppError(status.HTTP_422_UNPROCESSABLE_ENTITY, "REASON_REQUIRED", "A reason is required.")


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
