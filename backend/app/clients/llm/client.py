from typing import Any

from app.schemas.profile import InvestmentProfile

_EVIDENCE_LABEL = {
    "market": "시세와 수급",
    "news": "최근 뉴스",
    "financial": "재무·공시 지표",
    "risk": "위험 요인",
}
_HORIZON_LABEL = {"short": "단기", "medium": "중기", "long": "장기"}


def generate_personalized_checkpoints(
    profile: InvestmentProfile, common_analysis: dict[str, Any]
) -> dict[str, Any]:
    """실제 OpenAI 호출 전까지 성향 값을 규칙 기반으로 조합한 표본 개인화 결과다."""
    one_line = common_analysis.get("one_line_summary", "")
    evidence_label = _EVIDENCE_LABEL.get(profile.preferred_evidence, profile.preferred_evidence)
    horizon_label = _HORIZON_LABEL.get(profile.investment_horizon, profile.investment_horizon)

    return {
        "personal_summary": f"{horizon_label} 관점에서 보면: {one_line}",
        "priority_checks": [
            f"선호 근거인 {evidence_label}부터 확인해보자.",
            f"{profile.risk_profile} 성향에 맞는 변동성 수준인지 점검해보자.",
        ],
        "caution": "이 확인 포인트는 매수·매도를 추천하지 않으며 참고용 설명이다.",
    }
