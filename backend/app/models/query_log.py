from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, DateTime, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    response_preview: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    out_of_scope: Mapped[bool] = mapped_column(Boolean, default=False)
    cited_sources: Mapped[list | None] = mapped_column(JSON, nullable=True)
