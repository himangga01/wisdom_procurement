from datetime import datetime

from pydantic import BaseModel


class AnalysisRead(BaseModel):
    id: int
    project_document_id: int
    analysis_type: str
    model_provider: str
    model_name: str
    prompt_version: str
    input_hash: str
    output_json: str
    output_markdown: str
    token_usage_json: str
    status: str
    error_message: str
    created_at: datetime

    class Config:
        from_attributes = True
