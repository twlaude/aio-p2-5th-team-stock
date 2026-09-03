from typing import Any

from app.clients.llm import client as llm_client
from app.schemas.analysis import PersonalizedCheckpoints
from app.schemas.profile import InvestmentProfile


def build_checkpoints(profile: InvestmentProfile, common_analysis: dict[str, Any]) -> PersonalizedCheckpoints:
    result = llm_client.generate_personalized_checkpoints(profile, common_analysis)
    return PersonalizedCheckpoints(**result)
