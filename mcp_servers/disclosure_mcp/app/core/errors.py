"""Disclosure MCP에서 공통으로 사용하는 오류 타입."""


class ConfigurationError(ValueError):
    """필수 환경변수가 없거나 허용 범위를 벗어났을 때 발생한다."""
