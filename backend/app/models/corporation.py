from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Corporation(Base):
    __tablename__ = "corporations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    business_category: Mapped[str] = mapped_column(String(200), default="")
    region: Mapped[str] = mapped_column(String(100), default="")
    certifications_json: Mapped[str] = mapped_column(Text, default="[]")
    company_size_classification: Mapped[str] = mapped_column(String(100), default="")
    internal_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = relationship("Project", back_populates="corporation", cascade="all,delete")
