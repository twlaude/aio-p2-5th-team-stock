from pydantic import BaseModel


class Company(BaseModel):
    rank: int
    company_name: str
    stock_code: str
    market: str


class CompanyListResponse(BaseModel):
    status: str
    snapshot_date: str
    companies: list[Company]
