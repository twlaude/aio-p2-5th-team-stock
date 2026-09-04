from typing import Literal

from app.schemas.analysis import PersonalizedCheckpoints
from app.schemas.profile import InvestmentProfile

EvidenceLevelName = Literal["low", "medium", "high"]
GapState = Literal["large", "some", "small", "quiet"]

RISK_WORD = {"conservative": "손실을 피하는 걸 우선하는", "balanced": "적당한 위험은 감수하는", "aggressive": "큰 변동도 감수하는"}
HORIZON_WORD = {"long": "오래 들고 가는", "medium": "몇 달 보고 가는", "short": "짧게 치고 빠지는"}
PREFERRED_CHECK = {
    "financial": "최근 사업보고서의 매출·영업이익 흐름",
    "news": "최근 기사 내용이 공시로 확인되는지",
    "market": "거래량이 평소보다 늘었는지",
    "risk": "사업보고서의 위험 요인 중 지금 현실화된 게 있는지",
}


def josa(word: str, a: str, b: str) -> str:
    if word:
        code = ord(word[-1])
        if 0xAC00 <= code <= 0xD7A3:
            return f"{word}{a if (code - 0xAC00) % 28 else b}"
    return f"{word}{b}"


def gap_state(score: int, level: EvidenceLevelName) -> GapState:
    if score >= 70 and level == "low":
        return "large"
    if (score >= 65 and level == "medium") or (score >= 78 and level != "low"):
        return "some"
    if score < 50 and level == "high":
        return "quiet"
    return "small"


def pick_topic(sources: list[dict], fallback: str) -> str:
    candidates: list[tuple[float, str]] = []
    for source in sources:
        if source.get("source_type") != "community":
            continue
        for topic in (source.get("meta") or {}).get("topics") or []:
            text = topic.get("text") if isinstance(topic, dict) else None
            weight = topic.get("weight") if isinstance(topic, dict) else None
            if isinstance(text, str) and text.strip() and isinstance(weight, (int, float)):
                candidates.append((float(weight), text.strip()))
    return max(candidates, key=lambda item: item[0])[1] if candidates else fallback


def compose_one_liner(topic: str, evidence_level: EvidenceLevelName, temperature_score: int, change: int) -> str:
    if evidence_level == "low" and temperature_score >= 70:
        return f"뉴스는 {josa(topic, '으로', '로')} 시끄러운데, 공시로 확인된 건 거의 없어요. 기사만으로 띄우는 흐름일 수 있어요."
    news = f"뉴스는 {topic}에 쏠려 있고"
    if evidence_level == "high":
        disclosure = "관련 공시가 실제로 있어요"
    elif evidence_level == "medium":
        disclosure = "주요 공시는 있지만 지금 화제와는 달라요"
    else:
        disclosure = "공식 확인은 아직 조금이에요"
    community = "커뮤니티는 기대가 앞서요" if change >= 0 else "커뮤니티는 조심스러워요"
    return f"{news}, {disclosure}. {community}."


def compose_personal(company_name: str, topic: str, score: int, level: EvidenceLevelName, profile: InvestmentProfile) -> PersonalizedCheckpoints:
    state = gap_state(score, level)
    you = f"{RISK_WORD[profile.risk_profile]} {HORIZON_WORD[profile.investment_horizon]} 편"
    company = josa(company_name, "은", "는")
    topic_josa = lambda a, b: josa(topic, a, b)
    opinion = {
        "large": {
            "conservative": f"지금은 지켜보는 게 나아요. {company} {topic} 기대만 앞서 있고 공시로 확인된 건 거의 없어요. {you}인 당신에겐 맞지 않는 구간이에요.",
            "balanced": f"지금 사면 비싸게 살 수 있어요. {company} {topic} 기대가 앞서 있어서, {you}이라면 공시로 확인되는 걸 보고 나눠서 접근하는 게 맞아요.",
            "aggressive": f"들어간다면 나갈 기준부터 정하세요. {company} {topic} 기대만으로 움직이는 구간이라 크게 흔들릴 수 있어요. {you}이라도 기준 없이 들어가면 위험해요.",
        },
        "some": {
            "conservative": f"당신에겐 '아직'이에요. {company} 관심은 뜨겁고 {topic_josa('은', '는')} 절반쯤 확인됐어요. {you}이라면 다음 실적으로 확인되고 나서 봐도 늦지 않아요.",
            "balanced": f"한 번에 말고 나눠서 보세요. {company} {topic} 중 확인된 절반은 볼 만하고 나머지는 기대예요. {you}이라면 확인되는 만큼만 따라가는 게 맞아요.",
            "aggressive": f"해볼 만한 구간이에요. {company} {topic_josa('이', '가')} 절반은 확인됐어요. 다만 {you}이라도 기대가 꺾이면 빠르게 되돌아올 수 있다는 걸 기억하세요.",
        },
        "small": {
            "conservative": f"무리 없는 구간이에요. {company} 관심과 확인된 재료가 비슷해요. {you}인 당신은 {topic} 실적 흐름만 꾸준히 보면 돼요.",
            "balanced": f"평소 기준대로 보면 돼요. {company} 지금 앞서가는 신호가 없어요. {you}이라면 {topic_josa('을', '를')} 중심으로 차분히 접근해도 돼요.",
            "aggressive": f"급하게 움직일 이유는 없어요. {company} {topic} 대비 관심이 과하지 않아요. {you}이라면 새 촉매가 나오는지 지켜보세요.",
        },
        "quiet": {
            "conservative": f"당신에게 잘 맞는 편이에요. {company} 조용하지만 {topic_josa('이', '가')} 공식 자료로 탄탄해요. {you}이라면 서두르지 않고 천천히 봐도 돼요.",
            "balanced": f"관심 가져볼 만해요. {company} 관심이 낮아 가격 부담이 적고 {topic_josa('은', '는')} 확인돼 있어요. {you}이라면 지금 살펴보기 좋은 구간이에요.",
            "aggressive": f"기다릴지 먼저 정하세요. {company} 아직 관심이 없어서 움직임이 느릴 수 있어요. {you}이라면 촉매가 나올 때까지 지루할 수 있어요.",
        },
    }
    horizon_check = {
        "long": "배당·현금흐름이 유지되는지",
        "medium": "다음 분기 실적이 지난 분기보다 나아졌는지",
        "short": "하루 변동 폭과 거래량이 견딜 만한지",
    }
    state_check = {
        "large": f"{josa(topic, '이', '가')} 공시로 확인되는지 (지금은 기사뿐)",
        "some": f"{topic} 중 아직 확인 안 된 절반이 언제 확인되는지",
        "small": f"{topic} 관련 새 소식이 확인된 것인지",
        "quiet": f"{topic}에 시장이 언제 관심을 갖기 시작하는지",
    }
    caution = {
        "conservative": "기대가 높을 땐 급하게 따라 사지 않아도 괜찮아요. 확인하고 들어가도 늦지 않아요.",
        "balanced": "뉴스와 커뮤니티가 같이 뜨거우면 한 박자 쉬어가도 돼요.",
        "aggressive": "뉴스만으로 오른 종목은 되돌림이 빨라요. 욕심보다 기준이 먼저예요.",
    }
    return PersonalizedCheckpoints(
        personal_summary=opinion[state][profile.risk_profile],
        priority_checks=[PREFERRED_CHECK[profile.preferred_evidence], state_check[state], horizon_check[profile.investment_horizon]],
        caution=caution[profile.risk_profile],
    )
