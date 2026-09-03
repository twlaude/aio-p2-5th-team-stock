# Community MCP Core

- `config.py`: `.env` → `CommunityConfig`(원본 서버 URL·Token, 호스트·포트, 기본 조회 기간·개수, 타임아웃, Mock 모드). `get_config()` 한 곳에서만 읽는다.
