from typing import Literal

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    query: str


class CompanyRef(BaseModel):
    company_name: str
    stock_code: str
    supported: bool = True


class PriceSnapshot(BaseModel):
    current_price: int
    change: int
    change_rate: float
    as_of: str


class MarketTemperature(BaseModel):
    score: int
    label: str
    data_coverage: list[str]
    weight_covered: int = Field(default=100, ge=0, le=100)


class EvidenceLevel(BaseModel):
    level: Literal["low", "medium", "high"]
    reason: str


class AnalysisDetail(BaseModel):
    market_temperature: MarketTemperature
    evidence_level: EvidenceLevel
    news_summary: str
    disclosure_summary: str
    community_summary: str
    sources: list[dict] = []


class PersonalizedCheckpoints(BaseModel):
    personal_summary: str
    priority_checks: list[str]
    caution: str


class AnalysisResponse(BaseModel):
    request_id: str
    status: str
    access_level: Literal["guest", "member"]
    requires_login: bool
    company: CompanyRef
    price: PriceSnapshot
    one_line_summary: str
    detail: AnalysisDetail | None = None
    personalized_checkpoints: PersonalizedCheckpoints | None = None


class UnsupportedCompanyResponse(BaseModel):
    status: Literal["unsupported_company"] = "unsupported_company"
    message: str
    actions: list[str]
