import json
import os
from functools import lru_cache
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_REPO_ROOT = _BACKEND_ROOT.parent

# 로컬 실행: 모노레포에서 shared/를 직접 읽는다.
# Docker 실행: 빌드 컨텍스트가 backend/뿐이라 shared/ 밖 파일은 안 보이므로
# Dockerfile이 backend/data/에 복사해 둔 사본을 대신 읽는다.
_CANDIDATE_PATHS = [
    Path(os.environ["SUPPORTED_COMPANIES_PATH"]) if os.environ.get("SUPPORTED_COMPANIES_PATH") else None,
    _REPO_ROOT / "shared" / "supported_companies.json",
    _BACKEND_ROOT / "data" / "supported_companies.json",
]


def _resolve_path() -> Path:
    for candidate in _CANDIDATE_PATHS:
        if candidate is not None and candidate.exists():
            return candidate
    raise FileNotFoundError(
        "supported_companies.json을 찾지 못했다. SUPPORTED_COMPANIES_PATH를 지정하거나 "
        "shared/supported_companies.json 또는 backend/data/supported_companies.json을 확인해라."
    )


@lru_cache
def _load() -> dict:
    with _resolve_path().open(encoding="utf-8") as f:
        return json.load(f)


def list_companies() -> list[dict]:
    return _load()["companies"]


def snapshot_date() -> str:
    return _load()["snapshot_date"]


def resolve_company(query: str) -> dict | None:
    query = query.strip()
    for company in list_companies():
        if company["company_name"] == query or company["stock_code"] == query:
            return company
    return None
