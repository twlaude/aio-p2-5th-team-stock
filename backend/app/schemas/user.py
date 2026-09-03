from pydantic import BaseModel

from app.schemas.profile import InvestmentProfile


class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str
    password: str
    display_name: str
    profile: InvestmentProfile


class UserPublic(BaseModel):
    user_id: str
    username: str
    display_name: str


class AuthResponse(BaseModel):
    status: str
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
    profile_completed: bool


class CurrentUser(BaseModel):
    user_id: str
    username: str
    display_name: str
