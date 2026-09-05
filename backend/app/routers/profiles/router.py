from fastapi import APIRouter, Depends

from app.schemas.profile import InvestmentProfile
from app.schemas.user import CurrentUser
from app.services.auth.service import get_current_user
from app.services.profile import service as profile_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=InvestmentProfile)
async def get_profile(current_user: CurrentUser = Depends(get_current_user)) -> InvestmentProfile:
    return await profile_service.get_profile(current_user.user_id)


@router.put("", response_model=InvestmentProfile)
async def update_profile(
    body: InvestmentProfile, current_user: CurrentUser = Depends(get_current_user)
) -> InvestmentProfile:
    return await profile_service.update_profile(current_user.user_id, body)
