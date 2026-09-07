from dataclasses import dataclass, field

from app.agents.policy import TOOL_RISK
from app.prompts import ANALYSIS_INSTRUCTIONS


@dataclass(frozen=True)
class StockAnalysisAgent:
    agent_id: str = "stock-analysis"
    name: str = "Stock Analysis Agent"
    goal: str = "네 종류의 자료를 비교해 추천 없이 현재 관심 정도와 확인 근거를 설명한다."
    description: str = "현재가·뉴스·공시·커뮤니티 반응을 근거로 현재 상황을 설명하는 주식 정보 도우미. 추천·목표주가·예측은 하지 않는다."
    example_question: str = "삼성전자"
    instructions: str = ANALYSIS_INSTRUCTIONS
    allowed_tools: frozenset[str] = frozenset({"get_disclosure_detail"})
    tool_risks: dict[str, str] = field(default_factory=lambda: TOOL_RISK.copy())
