"""임시 PostgreSQL 대체 저장소. 실제 DB 연결 전까지 프로세스 메모리에 보관한다."""
from dataclasses import dataclass
from uuid import uuid4

from app.core.security import hash_password
from app.schemas.profile import InvestmentProfile


@dataclass
class UserRecord:
    user_id: str
    username: str
    password_hash: str
    display_name: str
    profile: InvestmentProfile | None


def _seed() -> dict[str, UserRecord]:
    demo_password = hash_password("Demo1234!")
    return {
        "demo001": UserRecord(
            user_id="demo-001",
            username="demo001",
            password_hash=demo_password,
            display_name="데모 사용자 1",
            profile=InvestmentProfile(
                experience_level="beginner",
                risk_profile="conservative",
                investment_horizon="long",
                preferred_evidence="news",
            ),
        ),
        "demo002": UserRecord(
            user_id="demo-002",
            username="demo002",
            password_hash=demo_password,
            display_name="데모 사용자 2",
            profile=InvestmentProfile(
                experience_level="experienced",
                risk_profile="aggressive",
                investment_horizon="short",
                preferred_evidence="market",
            ),
        ),
    }


_USERS_BY_USERNAME: dict[str, UserRecord] = _seed()
_USERS_BY_ID: dict[str, UserRecord] = {u.user_id: u for u in _USERS_BY_USERNAME.values()}


def get_by_username(username: str) -> UserRecord | None:
    return _USERS_BY_USERNAME.get(username)


def get_by_id(user_id: str) -> UserRecord | None:
    return _USERS_BY_ID.get(user_id)


def create_user(username: str, password: str, display_name: str, profile: InvestmentProfile) -> UserRecord:
    if username in _USERS_BY_USERNAME:
        raise ValueError(f"이미 존재하는 사용자명이다: {username}")
    record = UserRecord(
        user_id=f"user-{uuid4()}",
        username=username,
        password_hash=hash_password(password),
        display_name=display_name,
        profile=profile,
    )
    _USERS_BY_USERNAME[username] = record
    _USERS_BY_ID[record.user_id] = record
    return record


def update_profile(user_id: str, profile: InvestmentProfile) -> UserRecord | None:
    record = _USERS_BY_ID.get(user_id)
    if record is None:
        return None
    record.profile = profile
    return record


def delete_profile(user_id: str) -> None:
    record = _USERS_BY_ID.get(user_id)
    if record is not None:
        record.profile = None
