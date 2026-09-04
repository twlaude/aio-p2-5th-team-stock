from app.schemas.analysis import CollectedData, SourceItem


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
            )
        )

    for disclosure in (data.disclosures.get("disclosures") or [])[:2]:
        sources.append(
            SourceItem(
                source_type="disclosure",
                title=str(disclosure.get("report_name") or "전자공시"),
                url=disclosure.get("source_url") or None,
                published_at=disclosure.get("published_at") or None,
            )
        )

    if data.annual_report.get("status") == "success":
        sources.append(
            SourceItem(
                source_type="disclosure",
                title=str(data.annual_report.get("report_name") or "최신 사업보고서"),
                url=data.annual_report.get("source_url") or None,
            )
        )

    if data.community.get("status") in {"success", "partial_success"}:
        sources.append(
            SourceItem(
                source_type="community",
                title=str(data.community.get("source_name") or "커뮤니티 반응"),
            )
        )
    return sources
