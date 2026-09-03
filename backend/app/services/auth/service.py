from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import create_access_token, decode_access_token, verify_password
from app.repositories import user_repository
from app.schemas.profile import InvestmentProfile
from app.schemas.user import AuthResponse, CurrentUser, UserPublic

_bearer_required = HTTPBearer(auto_error=True)
_bearer_optional = HTTPBearer(auto_error=False)


def _issue_auth_response(record) -> AuthResponse:
    token = create_access_token(record.user_id)
    return AuthResponse(
        status="success",
        access_token=token,
        user=UserPublic(user_id=record.user_id, username=record.username, display_name=record.display_name),
        profile_completed=record.profile is not None,
    )


def login(username: str, password: str) -> AuthResponse:
    record = user_repository.get_by_username(username)
    if record is None or not verify_password(password, record.password_hash):
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않다.")
    return _issue_auth_response(record)


def signup(username: str, password: str, display_name: str, profile: InvestmentProfile) -> AuthResponse:
    try:
        record = user_repository.create_user(username, password, display_name, profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _issue_auth_response(record)


def _resolve_user(token: str) -> CurrentUser:
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="로그인이 필요하다.")
    record = user_repository.get_by_id(user_id)
    if record is None:
        raise HTTPException(status_code=401, detail="로그인이 필요하다.")
    return CurrentUser(user_id=record.user_id, username=record.username, display_name=record.display_name)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer_required)) -> CurrentUser:
    return _resolve_user(credentials.credentials)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> CurrentUser | None:
    if credentials is None:
        return None
    return _resolve_user(credentials.credentials)
