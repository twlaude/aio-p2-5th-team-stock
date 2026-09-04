from app.schemas.analysis import CollectedData, SourceItem


def _meta(**values: object) -> dict[str, object]:
    return {key: value for key, value in values.items() if value not in (None, "", [], {})}


def _community_topics(data: CollectedData) -> list[dict[str, object]]:
    top_topics = data.community.get("top_topics") or {}
    topics: list[dict[str, object]] = []
    for key, sentiment in (("expectations", "positive"), ("concerns", "negative")):
        for rank, text in enumerate(top_topics.get(key) or []):
            if text:
                topics.append(
                    {"text": str(text), "sentiment": sentiment, "weight": max(5 - rank, 1)}
                )
    return topics


def collect_sources(data: CollectedData) -> list[SourceItem]:
    sources: list[SourceItem] = []
    if data.price.get("status") == "success":
        sources.append(
            SourceItem(source_type="price", title=str(data.price.get("source_name") or "현재 주가"))
        )

    for article in (data.news.get("articles") or [])[:5]:
        sources.append(
            SourceItem(
                source_type="news",
                title=str(article.get("headline") or "뉴스"),
                url=article.get("source_url") or None,
                published_at=article.get("published_at") or None,
                meta=_meta(publisher=article.get("publisher")),
            )
        )

    for disclosure in (data.disclosures.get("disclosures") or [])[:2]:
        sources.append(
            SourceItem(
                source_type="disclosure",
                title=str(disclosure.get("report_name") or "전자공시"),
                url=disclosure.get("source_url") or None,
                published_at=disclosure.get("published_at") or None,
                meta=_meta(
                    receipt_number=disclosure.get("receipt_number"),
                    document_type=disclosure.get("document_type"),
                ),
            )
        )

    if data.annual_report.get("status") == "success":
        sources.append(
            SourceItem(
                source_type="disclosure",
                title=str(data.annual_report.get("report_name") or "최신 사업보고서"),
                url=data.annual_report.get("source_url") or None,
                meta=_meta(
                    receipt_number=data.annual_report.get("receipt_number"),
                    document_type=data.annual_report.get("document_type"),
                ),
            )
        )

    if data.community.get("status") in {"success", "partial_success"}:
        sentiment = data.community.get("sentiment") or {}
        fgi_latest = data.community.get("fgi_latest") or {}
        sources.append(
            SourceItem(
                source_type="community",
                title=str(data.community.get("source_name") or "커뮤니티 반응"),
                meta=_meta(
                    samples=data.community.get("sample_size"),
                    positive=sentiment.get("positive_count"),
                    neutral=sentiment.get("neutral_count"),
                    negative=sentiment.get("negative_count"),
                    fgi=fgi_latest.get("fgi"),
                    fgi_label=fgi_latest.get("label"),
                    topics=_community_topics(data),
                ),
            )
        )
    return sources
