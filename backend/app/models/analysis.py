from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_document_id: Mapped[int] = mapped_column(ForeignKey("project_documents.id"), nullable=False, index=True)
    analysis_type: Mapped[str] = mapped_column(String(50), default="summary")
    model_provider: Mapped[str] = mapped_column(String(100), default="openai")
    model_name: Mapped[str] = mapped_column(String(100), default="gpt-5.1")
    prompt_version: Mapped[str] = mapped_column(String(30), default="v1")
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    output_json: Mapped[str] = mapped_column(Text, default="{}")
    output_markdown: Mapped[str] = mapped_column(Text, default="")
    token_usage_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(50), default="completed")
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project_document = relationship("ProjectDocument", back_populates="analyses")
