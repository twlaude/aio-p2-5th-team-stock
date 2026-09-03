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


_EXPERIENCE_LEVELS = ("beginner", "intermediate", "experienced")
_RISK_PROFILES = ("conservative", "balanced", "aggressive")
_INVESTMENT_HORIZONS = ("long", "medium", "short")
_PREFERRED_EVIDENCE = ("news", "market", "financial", "risk")


def _seed() -> dict[str, UserRecord]:
    """발표용 데모 계정 10개. shared/contracts/frontend_backend/README.md 기준 공용 비밀번호 Demo1234!를 쓴다."""
    demo_password = hash_password("Demo1234!")
    users: dict[str, UserRecord] = {}
    for i in range(1, 11):
        username = f"demo{i:03d}"
        users[username] = UserRecord(
            user_id=f"demo-{i:03d}",
            username=username,
            password_hash=demo_password,
            display_name=f"데모 사용자 {i}",
            profile=InvestmentProfile(
                experience_level=_EXPERIENCE_LEVELS[(i - 1) % len(_EXPERIENCE_LEVELS)],
                risk_profile=_RISK_PROFILES[(i - 1) % len(_RISK_PROFILES)],
                investment_horizon=_INVESTMENT_HORIZONS[(i - 1) % len(_INVESTMENT_HORIZONS)],
                preferred_evidence=_PREFERRED_EVIDENCE[(i - 1) % len(_PREFERRED_EVIDENCE)],
            ),
        )
    return users


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
