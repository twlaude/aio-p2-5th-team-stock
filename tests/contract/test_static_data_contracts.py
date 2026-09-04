import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_supported_companies_snapshot_has_twenty_unique_companies() -> None:
    payload = _read_json(ROOT / "shared" / "supported_companies.json")
    companies = payload["companies"]

    assert payload["snapshot_date"] == "2026-09-01"
    assert len(companies) == 20
    assert [company["rank"] for company in companies] == list(range(1, 21))
    assert len({company["stock_code"] for company in companies}) == 20
    assert all(
        company["stock_code"].isdigit() and len(company["stock_code"]) == 6
        for company in companies
    )


def test_mock_users_match_user_profile_contract() -> None:
    payload = _read_json(ROOT / "backend" / "app" / "data" / "mock_users.json")
    users = payload["users"]

    allowed = {
        "experience_level": {"beginner", "intermediate", "experienced"},
        "risk_profile": {"conservative", "balanced", "aggressive"},
        "investment_horizon": {"short", "medium", "long"},
        "preferred_evidence": {"market", "news", "financial", "risk"},
    }

    assert len(users) == 10
    assert len({user["user_id"] for user in users}) == 10
    assert len({user["username"] for user in users}) == 10
    for user in users:
        for field, values in allowed.items():
            assert user[field] in values
