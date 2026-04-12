from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(100), default="general")
    original_file_name: Mapped[str] = mapped_column(String(300), nullable=False)
    stored_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    memo: Mapped[str] = mapped_column(Text, default="")
    revision_note: Mapped[str] = mapped_column(Text, default="")
    parsing_status: Mapped[str] = mapped_column(String(50), default="pending")
    ocr_status: Mapped[str] = mapped_column(String(50), default="pending")
    analysis_status: Mapped[str] = mapped_column(String(50), default="pending")
    latest_analysis_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="documents")
    analyses = relationship("Analysis", back_populates="project_document", cascade="all,delete")
