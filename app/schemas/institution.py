from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InstitutionResponse(BaseModel):
    id: int
    plaid_institution_id: str
    name: str
    country: str
    url: Optional[str] = None
    primary_color: Optional[str] = None
    logo: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True