from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: int
    project_id: int
    document_type: str
    original_file_name: str
    stored_file_path: str
    mime_type: str
    file_size: int
    memo: str
    revision_note: str
    parsing_status: str
    ocr_status: str
    analysis_status: str
    latest_analysis_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReanalyzeResponse(BaseModel):
    analysis_id: int
    status: str
    message: str
