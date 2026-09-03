from fastapi import HTTPException

from app.repositories import user_repository
from app.schemas.profile import InvestmentProfile


def get_profile(user_id: str) -> InvestmentProfile:
    record = user_repository.get_by_id(user_id)
    if record is None or record.profile is None:
        raise HTTPException(status_code=404, detail="등록된 투자 성향이 없다.")
    return record.profile


def update_profile(user_id: str, profile: InvestmentProfile) -> InvestmentProfile:
    record = user_repository.update_profile(user_id, profile)
    if record is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없다.")
    return record.profile


def delete_profile(user_id: str) -> None:
    user_repository.delete_profile(user_id)
