from fastapi import APIRouter, Depends

from app.schemas.analysis import AnalysisRequest, AnalysisResponse, UnsupportedCompanyResponse
from app.schemas.company import Company, CompanyListResponse
from app.schemas.user import CurrentUser
from app.services.analysis import companies
from app.services.analysis.service import run_analysis
from app.services.auth.service import get_optional_user

router = APIRouter(tags=["analysis"])


@router.get("/companies", response_model=CompanyListResponse)
def list_companies() -> CompanyListResponse:
    return CompanyListResponse(
        status="success",
        snapshot_date=companies.snapshot_date(),
        companies=[Company(**c) for c in companies.list_companies()],
    )


@router.post("/analyses")
def create_analysis(
    body: AnalysisRequest, current_user: CurrentUser | None = Depends(get_optional_user)
) -> AnalysisResponse | UnsupportedCompanyResponse:
    return run_analysis(body.query, body.question, current_user)
