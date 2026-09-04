from app.services.analysis_builder.scoring import calculate_evidence_level, calculate_market_temperature
from tests.helpers import collected_data


def test_calculates_attention_score_without_predicting_direction():
    data = collected_data()
    temperature = calculate_market_temperature(data)

    assert temperature.score == 44
    assert temperature.label == "보통"
    assert temperature.components == {
        "volume_activity": 15,
        "news_attention": 2,
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
        "news_attention": 2,
        "fear_greed_intensity": 10,
    }
    assert temperature.weight_covered == 75
    assert temperature.score == 36
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

    assert temperature.components["news_attention"] == 2
    assert temperature.weight_covered == 100


def test_prefers_relevant_count_over_total_result_count():
    data = collected_data()
    data.news["relevant_count"] = 80
    data.news["result_count"] = 1

    temperature = calculate_market_temperature(data)

    assert temperature.components["news_attention"] == 25


def test_evidence_is_high_when_all_sources_and_official_evidence_exist():
    data = collected_data()
    temperature = calculate_market_temperature(data)
    evidence = calculate_evidence_level(data, temperature.data_coverage)

    assert evidence.level == "high"
