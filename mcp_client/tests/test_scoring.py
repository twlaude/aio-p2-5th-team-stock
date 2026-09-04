from app.services.analysis_builder.scoring import calculate_evidence_level, calculate_market_temperature
from tests.helpers import collected_data


def test_calculates_attention_score_without_predicting_direction():
    data = collected_data()
    temperature = calculate_market_temperature(data)

    assert temperature.score == 42
    assert temperature.label == "보통"
    assert temperature.components == {
        "volume_activity": 15,
        "news_attention": 0,
        "community_activity": 17,
        "fear_greed_intensity": 10,
    }
    assert temperature.weight_covered == 100
    assert temperature.data_coverage == ["price", "news", "disclosure", "community"]


def test_uses_volume_change_rate_when_twenty_day_baseline_is_unavailable():
    data = collected_data()
    data.price["avg_volume_20d"] = None
    data.price["volume_ratio_20d"] = None

    temperature = calculate_market_temperature(data)

    assert temperature.components["volume_activity"] == 15
    assert temperature.weight_covered == 100


def test_renormalizes_when_community_source_is_unavailable():
    data = collected_data()
    data.community.pop("activity")

    temperature = calculate_market_temperature(data)

    assert temperature.components == {
        "volume_activity": 15,
        "news_attention": 0,
        "fear_greed_intensity": 10,
    }
    assert temperature.weight_covered == 75
    assert temperature.score == 33
    assert temperature.data_coverage == ["price", "news", "disclosure", "community"]


def test_returns_zero_when_all_temperature_inputs_are_unavailable():
    data = collected_data()
    data.price["status"] = "external_api_error"
    data.news["status"] = "external_api_error"
    data.community["status"] = "external_api_error"

    temperature = calculate_market_temperature(data)

    assert temperature.components == {}
    assert temperature.weight_covered == 0
    assert temperature.score == 0
    assert temperature.label == "관심 낮음"


def test_falls_back_to_result_count_when_relevant_count_is_missing():
    data = collected_data()
    data.news.pop("relevant_count")

    temperature = calculate_market_temperature(data)

    assert temperature.components["news_attention"] == 0
    assert temperature.weight_covered == 100


def test_prefers_relevant_count_over_total_result_count():
    data = collected_data()
    data.news["relevant_count"] = 100
    data.news["result_count"] = 1
    data.news["span_hours"] = 1.5  # 대형주: 100건이 1.5시간 만에 쌓임 → 만점

    temperature = calculate_market_temperature(data)

    assert temperature.components["news_attention"] == 25


def test_news_attention_uses_time_to_collect_100_articles():
    data = collected_data()
    # 92건이 36시간 → 100건 환산 39시간 → 로그 스케일 중간
    data.news["relevant_count"] = 92
    data.news["span_hours"] = 36.0
    assert calculate_market_temperature(data).components["news_attention"] == 11
    # 10건이 7일 → 100건 환산 1,680시간 → 0점
    data.news["relevant_count"] = 10
    data.news["span_hours"] = 168.0
    assert calculate_market_temperature(data).components["news_attention"] == 0
    # 구버전 MCP(span 없음)는 80건 만점 규칙으로 폴백
    data.news["relevant_count"] = 40
    data.news.pop("span_hours")
    assert calculate_market_temperature(data).components["news_attention"] == 12


def test_evidence_is_high_when_all_sources_and_official_evidence_exist():
    data = collected_data()
    temperature = calculate_market_temperature(data)
    evidence = calculate_evidence_level(data, temperature.data_coverage)

    assert evidence.level == "high"
    assert evidence.material_count == 1
    assert evidence.matched[0].issue == "대규모 공급계약 효과"
    assert evidence.matched[0].report_name == "단일판매ㆍ공급계약체결"
    assert "단일판매ㆍ공급계약체결 공시와 맞아요" in evidence.reason
    assert evidence.unmatched == ["업황", "삼성전자 관련 뉴스 0", "삼성전자 관련 뉴스 1"]


def test_evidence_is_medium_when_material_disclosure_does_not_match_current_issue():
    data = collected_data()
    data.material_disclosures["disclosures"][0].update(
        {"report_name": "최대주주변경", "disclosure_kind": "major"}
    )

    evidence = calculate_evidence_level(data, [])

    assert evidence.level == "medium"
    assert evidence.material_count == 1
    assert evidence.matched == []
    assert "지금 화제(대규모 공급계약 효과)와 직접 연결되진 않아요" in evidence.reason


def test_evidence_is_low_when_no_material_disclosure_exists():
    data = collected_data()
    data.material_disclosures = {"status": "success", "disclosures": []}

    evidence = calculate_evidence_level(data, ["price", "news", "community"])

    assert evidence.level == "low"
    assert evidence.material_count == 0
    assert evidence.reason == "최근 30일 안에 주요 공시가 없어요. 정기보고서만 있어요"


def test_evidence_is_low_with_explicit_reason_when_material_lookup_failed():
    data = collected_data()
    data.material_disclosures = {"status": "timeout"}

    evidence = calculate_evidence_level(data, ["price", "news", "disclosure", "community"])

    assert evidence.level == "low"
    assert evidence.reason == "최근 공시를 확인하지 못했어요"
    assert evidence.unmatched[0] == "대규모 공급계약 효과"


def test_evidence_mentions_missing_issue_when_no_issue_was_extracted():
    data = collected_data()
    data.community["top_topics"] = {"expectations": [], "concerns": []}
    data.news["articles"] = [{"headline": "시장 전체 뉴스"}]
    data.material_disclosures = {"status": "no_data", "disclosures": []}

    evidence = calculate_evidence_level(data, [])

    assert evidence.level == "low"
    assert evidence.reason == "화제로 잡힌 이슈가 없어요"
