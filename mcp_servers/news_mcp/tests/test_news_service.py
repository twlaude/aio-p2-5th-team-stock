from datetime import datetime, timezone

from app.services.news import map_upstream_response

NOW = datetime(2026, 9, 1, 9, 0, 0, tzinfo=timezone.utc)
REQUEST = {
    "company_name": "삼성전자",
    "stock_code": "005930",
    "lookback_days": 7,
    "limit": 10,
}


def _item(title, description, link, pub_date):
    return {
        "title": title,
        "description": description,
        "originallink": link,
        "link": link,
        "pubDate": pub_date,
    }


def test_dedupes_and_filters_irrelevant_and_old_articles():
    payload = {
        "items": [
            _item(
                "<b>삼성전자</b> 실적 개선",
                "삼성전자 반도체 실적이 개선되었다.",
                "https://example.com/1",
                "Mon, 31 Aug 2026 09:00:00 +0000",
            ),
            _item(
                "삼성전자 실적 개선",
                "삼성전자 반도체 실적이 개선되었다.",
                "https://example.com/1",
                "Mon, 31 Aug 2026 09:00:00 +0000",
            ),
            _item(
                "무관한 뉴스",
                "다른 회사 이야기다.",
                "https://example.com/2",
                "Mon, 31 Aug 2026 09:00:00 +0000",
            ),
            _item(
                "삼성전자 오래된 뉴스",
                "삼성전자 옛날 소식이다.",
                "https://example.com/3",
                "Mon, 01 Jan 2024 09:00:00 +0000",
            ),
        ]
    }

    result = map_upstream_response(payload, REQUEST, now=NOW)

    assert result["status"] == "success"
    assert result["result_count"] == 1
    assert result["relevant_count"] == 1
    assert result["articles"][0]["source_url"] == "https://example.com/1"
    assert result["articles"][0]["headline"] == "삼성전자 실적 개선"


def test_no_data_when_nothing_relevant():
    payload = {"items": [_item("무관한 뉴스", "다른 회사 이야기다.", "https://example.com/9", "Mon, 31 Aug 2026 09:00:00 +0000")]}

    result = map_upstream_response(payload, REQUEST, now=NOW)

    assert result["status"] == "no_data"
    assert result["result_count"] == 0
    assert result["relevant_count"] == 0


def test_relevant_count_counts_high_relevance_within_lookback_before_output_limit():
    payload = {
        "items": [
            _item(
                "삼성전자 첫 번째 기사",
                "삼성전자 관련 내용이다.",
                "https://example.com/10",
                "Mon, 31 Aug 2026 09:00:00 +0000",
            ),
            _item(
                "삼성전자 두 번째 기사",
                "삼성전자 관련 추가 내용이다.",
                "https://example.com/11",
                "Mon, 31 Aug 2026 08:00:00 +0000",
            ),
            _item(
                "삼성전자 오래된 기사",
                "삼성전자 관련 과거 내용이다.",
                "https://example.com/12",
                "Mon, 01 Jan 2024 09:00:00 +0000",
            ),
            _item(
                "무관한 기사",
                "다른 회사 내용이다.",
                "https://example.com/13",
                "Mon, 31 Aug 2026 07:00:00 +0000",
            ),
        ]
    }
    request = {**REQUEST, "limit": 1}

    result = map_upstream_response(payload, request, now=NOW)

    assert result["result_count"] == 1
    assert result["relevant_count"] == 2
