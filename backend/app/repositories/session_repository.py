"""임시 세션 저장소. 실제 JWT 검증 전까지 발급한 토큰을 프로세스 메모리에 보관한다."""
from uuid import uuid4

_TOKENS: dict[str, str] = {}


def issue_token(user_id: str) -> str:
    token = f"demo-access-token-{uuid4().hex}"
    _TOKENS[token] = user_id
    return token


def resolve_token(token: str) -> str | None:
    return _TOKENS.get(token)
