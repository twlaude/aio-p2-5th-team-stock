from fastapi import APIRouter, Depends

from app.schemas.memory import MemoryView
from app.schemas.user import CurrentUser
from app.services.auth.service import get_current_user
from app.services.memory import service as memory_service

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("/me", response_model=MemoryView)
def get_my_memory(current_user: CurrentUser = Depends(get_current_user)) -> MemoryView:
    return memory_service.get_memory(current_user.user_id)


@router.delete("/me", status_code=204)
def delete_my_memory(current_user: CurrentUser = Depends(get_current_user)) -> None:
    memory_service.clear_memory(current_user.user_id)
