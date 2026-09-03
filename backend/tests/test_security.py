from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token


def test_valid_token_decodes_to_user_id():
    token = create_access_token("demo-001")
    assert decode_access_token(token) == "demo-001"


def test_garbage_token_returns_none():
    assert decode_access_token("not-a-token") is None


def test_expired_token_returns_none():
    expired = jwt.encode(
        {"sub": "demo-001", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm="HS256",
    )
    assert decode_access_token(expired) is None


def test_token_signed_with_wrong_secret_is_rejected():
    forged = jwt.encode(
        {"sub": "demo-001", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "wrong-secret",
        algorithm="HS256",
    )
    assert decode_access_token(forged) is None
