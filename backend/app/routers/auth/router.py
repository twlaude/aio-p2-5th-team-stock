from fastapi import APIRouter

from app.schemas.user import AuthResponse, LoginRequest, SignupRequest
from app.services.auth import service as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest) -> AuthResponse:
    return auth_service.login(body.username, body.password)


@router.post("/signup", response_model=AuthResponse)
def signup(body: SignupRequest) -> AuthResponse:
    return auth_service.signup(body.username, body.password, body.display_name, body.profile)
