from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.workflows.analysis import RequiredPriceError
from app.workflows.factory import build_workflow, mcp_connection_status


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "mcp_client",
        "llm_provider": settings.llm_provider,
        "openai_configured": bool(settings.openai_api_key),
        "backend_progress_enabled": bool(settings.backend_event_url),
    }


@router.get("/internal/v1/mcp-status")
async def connection_status() -> dict[str, object]:
    return await mcp_connection_status(get_settings())


@router.post("/internal/v1/common-analyses", response_model=AnalysisResponse)
async def common_analysis(request: AnalysisRequest) -> AnalysisResponse:
    workflow = build_workflow(get_settings())
    try:
        return await workflow.run(request)
    except TimeoutError as error:
        raise HTTPException(status_code=504, detail="분석 시간이 초과되었습니다.") from error
    except RequiredPriceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="분석 중 내부 오류가 발생했습니다.") from error
