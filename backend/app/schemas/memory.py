from typing import Any

from pydantic import BaseModel

from app.schemas.profile import InvestmentProfile


class MemoryView(BaseModel):
    user_id: str
    long_term: InvestmentProfile | None
    short_term: dict[str, Any]
