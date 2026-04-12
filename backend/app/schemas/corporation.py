from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CorporationBase(BaseModel):
    name: str
    business_category: str = ""
    region: str = ""
    certifications_json: str = "[]"
    company_size_classification: str = ""
    internal_notes: str = ""


class CorporationCreate(CorporationBase):
    pass


class CorporationUpdate(BaseModel):
    name: Optional[str] = None
    business_category: Optional[str] = None
    region: Optional[str] = None
    certifications_json: Optional[str] = None
    company_size_classification: Optional[str] = None
    internal_notes: Optional[str] = None


class CorporationRead(CorporationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
