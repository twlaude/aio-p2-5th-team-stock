from app.services.analysis_builder.scoring import calculate_evidence_level, calculate_market_temperature
from tests.helpers import collected_data


def test_calculates_attention_score_without_predicting_direction():
    data = collected_data()
    temperature = calculate_market_temperature(data)

    assert temperature.score == 51
    assert temperature.label == "보통"
    assert temperature.components == {
        "price_movement": 10,
        "news_attention": 12,
        "community_activity": 10,
        "fear_greed_intensity": 10,
        "disclosure_activity": 9,
    }


def test_evidence_is_high_when_all_sources_and_official_evidence_exist():
    data = collected_data()
    temperature = calculate_market_temperature(data)
    evidence = calculate_evidence_level(data, temperature.data_coverage)

    assert evidence.level == "high"
