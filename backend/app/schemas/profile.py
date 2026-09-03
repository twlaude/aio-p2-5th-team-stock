from typing import Literal

from pydantic import BaseModel

ExperienceLevel = Literal["beginner", "intermediate", "experienced"]
RiskProfile = Literal["conservative", "balanced", "aggressive"]
InvestmentHorizon = Literal["short", "medium", "long"]
PreferredEvidence = Literal["market", "news", "financial", "risk"]


class InvestmentProfile(BaseModel):
    experience_level: ExperienceLevel
    risk_profile: RiskProfile
    investment_horizon: InvestmentHorizon
    preferred_evidence: PreferredEvidence
