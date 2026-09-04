from dataclasses import dataclass
from uuid import uuid4

import psycopg2.errors

from app.core.db import get_cursor
from app.core.security import hash_password
from app.schemas.profile import InvestmentProfile


@dataclass
class UserRecord:
    user_id: str
    username: str
    password_hash: str
    display_name: str
    profile: InvestmentProfile | None


_SELECT = """
    SELECT u.user_id, u.username, u.password_hash, u.display_name,
           p.experience_level, p.risk_profile, p.investment_horizon, p.preferred_evidence
    FROM users u
    LEFT JOIN user_profiles p ON p.user_id = u.user_id
    WHERE {column} = %s
"""


def _row_to_record(row) -> UserRecord:
    profile = None
    if row["experience_level"] is not None:
        profile = InvestmentProfile(
            experience_level=row["experience_level"],
            risk_profile=row["risk_profile"],
            investment_horizon=row["investment_horizon"],
            preferred_evidence=row["preferred_evidence"],
        )
    return UserRecord(
        user_id=row["user_id"],
        username=row["username"],
        password_hash=row["password_hash"],
        display_name=row["display_name"],
        profile=profile,
    )


def get_by_username(username: str) -> UserRecord | None:
    with get_cursor() as cur:
        cur.execute(_SELECT.format(column="u.username"), (username,))
        row = cur.fetchone()
    return _row_to_record(row) if row else None


def get_by_id(user_id: str) -> UserRecord | None:
    with get_cursor() as cur:
        cur.execute(_SELECT.format(column="u.user_id"), (user_id,))
        row = cur.fetchone()
    return _row_to_record(row) if row else None


def create_user(username: str, password: str, display_name: str, profile: InvestmentProfile) -> UserRecord:
    user_id = f"user-{uuid4()}"
    password_hash = hash_password(password)
    with get_cursor(commit=True) as cur:
        try:
            cur.execute(
                "INSERT INTO users (user_id, username, password_hash, display_name) VALUES (%s, %s, %s, %s)",
                (user_id, username, password_hash, display_name),
            )
        except psycopg2.errors.UniqueViolation as exc:
            raise ValueError(f"이미 존재하는 사용자명이다: {username}") from exc
        cur.execute(
            """
            INSERT INTO user_profiles
                (user_id, experience_level, risk_profile, investment_horizon, preferred_evidence)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, profile.experience_level, profile.risk_profile, profile.investment_horizon, profile.preferred_evidence),
        )
    return UserRecord(
        user_id=user_id, username=username, password_hash=password_hash, display_name=display_name, profile=profile
    )


def update_profile(user_id: str, profile: InvestmentProfile) -> UserRecord | None:
    with get_cursor(commit=True) as cur:
        try:
            cur.execute(
                """
                INSERT INTO user_profiles
                    (user_id, experience_level, risk_profile, investment_horizon, preferred_evidence, updated_at)
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (user_id) DO UPDATE SET
                    experience_level = EXCLUDED.experience_level,
                    risk_profile = EXCLUDED.risk_profile,
                    investment_horizon = EXCLUDED.investment_horizon,
                    preferred_evidence = EXCLUDED.preferred_evidence,
                    updated_at = now()
                """,
                (user_id, profile.experience_level, profile.risk_profile, profile.investment_horizon, profile.preferred_evidence),
            )
        except psycopg2.errors.ForeignKeyViolation:
            return None
    return get_by_id(user_id)


def delete_profile(user_id: str) -> None:
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
