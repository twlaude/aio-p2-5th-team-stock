from typing import Any

from app.schemas.analysis import CollectedData, EvidenceLevel, MarketTemperature


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _temperature_label(score: int) -> str:
    if score < 20:
        return "관심 낮음"
    if score < 40:
        return "관심 다소 낮음"
    if score < 60:
        return "보통"
    if score < 80:
        return "관심 높음"
    return "관심 매우 높음"


def calculate_market_temperature(data: CollectedData) -> MarketTemperature:
    price_score = round(min(abs(_float(data.price.get("change_rate"))) / 5.0, 1.0) * 20)
    news_score = round(min(_int(data.news.get("result_count")) / 10.0, 1.0) * 25)
    community_score = round(min(_int(data.community.get("sample_size")) / 100.0, 1.0) * 20)

    fgi_latest = data.community.get("fgi_latest") or {}
    fgi = _float(fgi_latest.get("fgi"), 50.0)
    fgi_score = round(min(abs(fgi - 50.0) / 50.0, 1.0) * 20)

    disclosure_count = len(data.disclosures.get("disclosures") or [])
    passage_count = len(data.annual_report.get("matched_passages") or [])
    disclosure_score = round(min((disclosure_count + passage_count) / 5.0, 1.0) * 15)

    components = {
        "price_movement": price_score,
        "news_attention": news_score,
        "community_activity": community_score,
        "fear_greed_intensity": fgi_score,
        "disclosure_activity": disclosure_score,
    }
    score = max(0, min(100, sum(components.values())))
    coverage = []
    if data.price.get("status") == "success":
        coverage.append("price")
    if data.news.get("status") == "success":
        coverage.append("news")
    if data.disclosures.get("status") == "success" or data.annual_report.get("status") == "success":
        coverage.append("disclosure")
    if data.community.get("status") in {"success", "partial_success"}:
        coverage.append("community")

    return MarketTemperature(
        score=score,
        label=_temperature_label(score),
        data_coverage=coverage,
        components=components,
    )


def calculate_evidence_level(data: CollectedData, coverage: list[str]) -> EvidenceLevel:
    has_official_evidence = bool(data.annual_report.get("matched_passages")) or bool(
        data.disclosures.get("disclosures")
    )
    community_sufficient = data.community.get("sample_status") == "sufficient"
    count = len(set(coverage))

    if count == 4 and has_official_evidence:
        level = "high"
        reason = "가격·뉴스·공식 공시·커뮤니티 자료가 모두 확인되었습니다."
    elif count >= 2:
        level = "medium"
        reason = "여러 자료를 확인했지만 일부 출처가 없거나 표본이 충분하지 않습니다."
    else:
        level = "low"
        reason = "확인 가능한 출처가 적어 제한적인 해석만 제공합니다."

    if level == "high" and not community_sufficient:
        level = "medium"
        reason = "공식 자료는 확인했지만 커뮤니티 표본이 충분하지 않습니다."
    return EvidenceLevel(level=level, reason=reason)
