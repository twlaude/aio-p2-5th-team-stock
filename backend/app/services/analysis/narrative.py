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
    # 평소 관심도 50과 라벨 경계 40/60/80을 기준으로 공시 근거와의 차이를 구분한다.
    if score >= 60 and level == "low":
        return "large"
    if (score >= 60 and level == "medium") or (score >= 80 and level != "low"):
        return "some"
    if score < 45 and level == "high":
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
    if evidence_level == "low" and temperature_score >= 60:
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
            "conservative": f"조금 더 지켜볼까요? {company} {topic} 기대만 있고, 공식적으로 확인된 건 아직 부족해요. {you}이라면 불확실성이 큰 상태예요.",
            "balanced": f"급하게 판단하지 않아도 돼요. {company} {topic} 기대가 앞서 있는 상황이에요. {you}이라면 분위기에 휩쓸리기보다 공시로 확인하면서 천천히 봐도 늦지 않아요.",
            "aggressive": f"변동 폭이 클 수 있어요. {company} 지금 {topic} 기대만으로 관심이 쏠린 상태예요. {you}이라도 나만의 기준이 없으면 흔들리기 쉬워요.",
        },
        "some": {
            "conservative": f"공식 발표를 기다려 보세요. {company} 관심은 뜨겁고 {topic_josa('은', '는')} 절반쯤 확인됐어요. {you}이라면 다음 실적이나 공시가 나온 뒤 봐도 늦지 않아요.",
            "balanced": f"확인되는 만큼만 따라가 보세요. {company} {topic} 중 절반은 공식 자료로 확인됐고 나머지는 아직 기대예요. {you}이라면 한 번에 판단하기보다 나눠서 살펴보는 게 좋아요.",
            "aggressive": f"공식 자료가 어느 정도 모였어요. {company} {topic_josa('이', '가')} 절반은 확인됐어요. 다만 {you}이라도 기대가 식으면 흐름이 빠르게 바뀔 수 있다는 건 기억해 두세요.",
        },
        "small": {
            "conservative": f"관심과 근거가 균형을 이루고 있어요. {company} 시장의 관심과 확인된 재료가 비슷해요. {you}이라면 {topic} 실제 흐름만 꾸준히 따라가면 돼요.",
            "balanced": f"평소 기준을 지키면 돼요. {company} 지금 눈에 띄게 앞서가는 신호가 없어요. {you}이라면 {topic_josa('을', '를')} 중심으로 차분히 살펴보세요.",
            "aggressive": f"서두르지 말고 지켜보세요. {company} {topic} 대비 관심이 과하지 않아요. {you}이라면 새로운 소식이 나오는지 차분히 기다려 보세요.",
        },
        "quiet": {
            "conservative": f"조용하지만 근거는 탄탄해요. {company} 관심은 적지만 {topic_josa('이', '가')} 공식 자료로 잘 갖춰져 있어요. {you}이라면 서두르지 않고 차분히 뜯어보기 좋아요.",
            "balanced": f"차분하게 살펴보기 좋은 상태예요. {company} 관심이 적어 들뜬 분위기가 없고 {topic_josa('은', '는')} 확인돼 있어요. {you}이라면 지금 천천히 재료를 점검해 보기 좋아요.",
            "aggressive": f"흐름이 느릴 수 있어요. {company} 시장의 관심이 낮아서 눈에 띄는 변화가 적을 수 있어요. {you}이라면 새로운 소식이 나올 때까지 좀 지루할 수 있어요.",
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
