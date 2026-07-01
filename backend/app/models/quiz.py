from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    questions: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
