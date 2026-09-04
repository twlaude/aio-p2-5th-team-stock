from dataclasses import dataclass


@dataclass(frozen=True)
class StockAnalysisAgent:
    agent_id: str = "stock-analysis"
    goal: str = "네 종류의 자료를 비교해 추천 없이 현재 관심 정도와 확인 근거를 설명한다."
    allowed_tools: frozenset[str] = frozenset({"get_disclosure_detail"})
