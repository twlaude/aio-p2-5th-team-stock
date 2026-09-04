"""전자공시 MCP의 공통 로그 설정."""

import logging


def configure_logging(level: str = "INFO") -> None:
    """표준 출력에 서비스 로그를 남긴다.

    환경변수와 OpenDART 인증키는 로그 메시지에 기록하지 않는다.
    """

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
