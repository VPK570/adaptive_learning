from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class FlashcardSet(Base):
    __tablename__ = "flashcard_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    cards: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
