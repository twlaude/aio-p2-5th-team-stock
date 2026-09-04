import re

from app.schemas.analysis import CollectedData


def _clean_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def extract_issues(data: CollectedData, company_name: str) -> list[str]:
    """현재 화제를 커뮤니티 중심으로 뽑고 회사명이 명시된 뉴스만 보탠다."""

    topics = data.community.get("top_topics") or {}
    candidates: list[object] = [
        *(topics.get("expectations") or [])[:3],
        *(topics.get("concerns") or [])[:2],
    ]

    normalized_company = _clean_text(company_name)
    if normalized_company:
        matching_headlines = []
        for article in data.news.get("articles") or []:
            headline = _clean_text(article.get("headline"))
            if headline and normalized_company in headline:
                matching_headlines.append(headline)
        candidates.extend(matching_headlines[:2])

    issues: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        issue = _clean_text(candidate)
        if not issue or issue in seen:
            continue
        seen.add(issue)
        issues.append(issue)
        if len(issues) == 6:
            break
    return issues
