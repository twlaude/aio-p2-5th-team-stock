from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CompanyRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(min_length=1, max_length=100)
    stock_code: str = Field(pattern=r"^\d{6}$")


class InvestmentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    experience_level: Literal["beginner", "intermediate", "experienced"]
    risk_profile: Literal["conservative", "balanced", "aggressive"]
    investment_horizon: Literal["short", "medium", "long"]
    preferred_evidence: Literal["market", "news", "financial", "risk"]


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=100)
    company: CompanyRef
    investment_profile: InvestmentProfile | None = None
    requested_at: str


class PriceSnapshot(BaseModel):
    current_price: int
    change: int
    change_rate: float
    as_of: str
    source_name: str | None = None
    volume_basis: str | None = None
    volume_as_of: str | None = None


class MarketTemperature(BaseModel):
    score: int = Field(ge=0, le=100)
    label: str
    data_coverage: list[str]
    components: dict[str, int] = Field(default_factory=dict)
    weight_covered: int = Field(ge=0, le=100)


class EvidenceLevel(BaseModel):
    level: Literal["low", "medium", "high"]
    reason: str


class PersonalizedCheckpoints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    personal_summary: str
    priority_checks: list[str] = Field(min_length=1, max_length=3)
    caution: str


class Narrative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    one_line_summary: str = Field(min_length=1, max_length=240)
    news_summary: str = Field(min_length=1, max_length=500)
    disclosure_summary: str = Field(min_length=1, max_length=500)
    community_summary: str = Field(min_length=1, max_length=500)
    personalized_checkpoints: PersonalizedCheckpoints | None


class CommonAnalysis(BaseModel):
    one_line_summary: str
    market_temperature: MarketTemperature
    evidence_level: EvidenceLevel
    news_summary: str
    disclosure_summary: str
    community_summary: str


class SourceItem(BaseModel):
    source_type: Literal["price", "news", "disclosure", "community"]
    title: str
    url: str | None = None
    published_at: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class PartialFailure(BaseModel):
    service: str
    status: str
    message: str


class TraceSummary(BaseModel):
    tool_calls: int
    llm_calls: int
    completed_tools: list[str]
    failed_tools: list[str]
    duration_ms: int


class AnalysisResponse(BaseModel):
    request_id: str
    run_id: str
    status: Literal["success", "partial_success"]
    termination_reason: str
    company: CompanyRef
    price: PriceSnapshot
    common_analysis: CommonAnalysis
    personalized_checkpoints: PersonalizedCheckpoints | None = None
    sources: list[SourceItem] = Field(default_factory=list)
    partial_failures: list[PartialFailure] = Field(default_factory=list)
    collected_at: str
    trace_summary: TraceSummary


class ToolFailure(BaseModel):
    service: str
    status: str
    message: str
    retryable: bool = False


class CollectedData(BaseModel):
    price: dict[str, Any]
    news: dict[str, Any]
    disclosures: dict[str, Any]
    annual_report: dict[str, Any]
    community: dict[str, Any]
    failures: list[ToolFailure] = Field(default_factory=list)
    completed_tools: list[str] = Field(default_factory=list)
    failed_tools: list[str] = Field(default_factory=list)
