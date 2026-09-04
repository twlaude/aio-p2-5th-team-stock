import math
from typing import Any

from app.schemas.analysis import CollectedData, EvidenceLevel, MarketTemperature


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _component_score(value: float, divisor: float, weight: int) -> int:
    normalized = max(0.0, min(value / divisor, 1.0))
    return round(normalized * weight)


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
    components: dict[str, int] = {}
    weight_covered = 0

    if data.price.get("status") == "success":
        volume_ratio = _optional_float(data.price.get("volume_ratio_20d"))
        if volume_ratio is None:
            volume_change_rate = _optional_float(data.price.get("volume_change_rate"))
            if volume_change_rate is not None:
                volume_ratio = 1.0 + volume_change_rate / 100.0
        if volume_ratio is not None:
            components["volume_activity"] = _component_score(volume_ratio, 3.0, 30)
            weight_covered += 30

    if data.news.get("status") == "success":
        news_count = _optional_float(data.news.get("relevant_count"))
        if news_count is None:
            news_count = _optional_float(data.news.get("result_count"))
        if news_count is not None:
            components["news_attention"] = _component_score(news_count, 30.0, 25)
            weight_covered += 25

    if data.community.get("status") == "success":
        activity = data.community.get("activity")
        activity_ratio = (
            _optional_float(activity.get("ratio")) if isinstance(activity, dict) else None
        )
        if activity_ratio is not None:
            components["community_activity"] = _component_score(activity_ratio, 3.0, 25)
            weight_covered += 25

        fgi_latest = data.community.get("fgi_latest")
        fgi = _optional_float(fgi_latest.get("fgi")) if isinstance(fgi_latest, dict) else None
        if fgi is not None:
            components["fear_greed_intensity"] = round(
                max(0.0, min(abs(fgi - 50.0) / 50.0, 1.0)) * 20
            )
            weight_covered += 20

    score = (
        max(0, min(100, round(sum(components.values()) / weight_covered * 100)))
        if weight_covered
        else 0
    )
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
        weight_covered=weight_covered,
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
