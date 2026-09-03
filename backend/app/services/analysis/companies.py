import json
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_COMPANIES_PATH = _REPO_ROOT / "shared" / "supported_companies.json"


@lru_cache
def _load() -> dict:
    with _COMPANIES_PATH.open(encoding="utf-8") as f:
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
