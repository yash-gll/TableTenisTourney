from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenPair,
    VerifyEmailRequest,
)
from app.schemas.mappers import to_me
from app.schemas.player import MeResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).register(
        email=body.email, password=body.password, display_name=body.display_name
    )
    return MessageResponse(
        message="Registration successful. Check the verification link, then wait for admin approval."
    )


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(body: VerifyEmailRequest, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).verify_email(token=body.token)
    return MessageResponse(message="Email verified. You can now log in.")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    body: ResendVerificationRequest, db: Session = Depends(get_db)
) -> MessageResponse:
    AuthService(db).resend_verification(email=body.email)
    return MessageResponse(message="If the account exists and is unverified, a new link was sent.")


@router.post("/login", response_model=TokenPair)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    _, tokens = AuthService(db).login(email=body.email, password=body.password)
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    return AuthService(db).refresh(refresh_token=body.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(body: LogoutRequest, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).logout(refresh_token=body.refresh_token)
    return MessageResponse(message="Logged out.")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).forgot_password(email=body.email)
    return MessageResponse(message="If the account exists, a reset link was sent.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).reset_password(token=body.token, password=body.password)
    return MessageResponse(message="Password updated. Please log in.")


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)) -> MeResponse:
    return to_me(user)
