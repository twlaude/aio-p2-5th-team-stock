from typing import Any

from app.schemas.analysis import Narrative, PersonalizedCheckpoints


def build_fallback_narrative(context: dict[str, Any]) -> Narrative:
    company_name = context["company"]["company_name"]
    temperature = context["market_temperature"]
    evidence = context["evidence_level"]
    news = context["data"].get("news") or {}
    disclosures = context["data"].get("disclosures") or {}
    annual_report = context["data"].get("annual_report") or {}
    community = context["data"].get("community") or {}

    news_count = int(news.get("result_count") or 0)
    disclosure_count = len(disclosures.get("disclosures") or [])
    passage_count = len(annual_report.get("matched_passages") or [])
    sample_size = int(community.get("sample_size") or 0)

    personalized = None
    profile = context.get("investment_profile")
    if profile:
        priorities = {
            "market": "현재 가격과 변동 폭",
            "news": "최근 뉴스의 사실관계",
            "financial": "공식 공시와 사업보고서",
            "risk": "공식 자료의 위험 요인",
        }
        horizons = {"short": "단기", "medium": "중기", "long": "장기"}
        personalized = PersonalizedCheckpoints(
            personal_summary=(
                f"{horizons.get(profile['investment_horizon'], profile['investment_horizon'])} 관점에서는 "
                f"{priorities.get(profile['preferred_evidence'], '공식 근거')}부터 확인해 보세요."
            ),
            priority_checks=[
                priorities.get(profile["preferred_evidence"], "공식 근거"),
                "현재 관심이 실제 기업 변화와 연결되는지",
            ],
            caution="관심 온도는 가격 방향이나 수익을 예측하는 지표가 아닙니다.",
        )

    return Narrative(
        one_line_summary=(
            f"{company_name}은 현재 '{temperature['label']}' 수준이며, "
            f"근거 확인 정도는 {evidence['level']}입니다. 추가 자료를 함께 확인해 보세요."
        ),
        news_summary=f"최근 확인된 관련 뉴스는 {news_count}건입니다. 기사 제목과 출처를 함께 확인해야 합니다.",
        disclosure_summary=(
            f"최근 공시 {disclosure_count}건과 사업보고서 관련 구절 {passage_count}개를 확인했습니다. "
            "공식 문서가 없는 부분은 판단 근거로 사용하지 않았습니다."
        ),
        community_summary=(
            f"최근 커뮤니티 표본은 {sample_size}건입니다. 커뮤니티 반응은 관심 분위기를 보여줄 뿐 사실 확인 자료는 아닙니다."
        ),
        personalized_checkpoints=personalized,
    )
