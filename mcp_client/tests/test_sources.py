from app.services.analysis_builder.sources import collect_sources
from tests.helpers import collected_data


def test_collect_sources_preserves_frontend_metadata():
    data = collected_data()
    data.disclosures["disclosures"][0]["document_type"] = "disclosure"
    data.annual_report.update({"receipt_number": "202509040001", "document_type": "annual_report"})

    sources = collect_sources(data)

    assert sources[1].meta == {"publisher": "example.com"}
    assert sources[8].meta == {"receipt_number": "202509040001", "document_type": "annual_report"}
    assert sources[9].meta == {
        "samples": 50,
        "positive": 20,
        "neutral": 20,
        "negative": 10,
        "fgi": 75.0,
        "fgi_label": "탐욕",
        "topics": [
            {"text": "신제품", "sentiment": "positive", "weight": 5},
            {"text": "업황", "sentiment": "negative", "weight": 5},
        ],
    }
