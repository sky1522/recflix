"""
User Event Model - 사용자 행동 이벤트 로깅
"""
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class UserEvent(Base):
    """사용자 행동 이벤트 (추천 품질 메트릭 수집용)"""
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(64), nullable=True)
    event_type = Column(String(50), nullable=False, index=True)
    movie_id = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_events_user_time", "user_id", "created_at"),
        Index("idx_events_type_time", "event_type", "created_at"),
        Index("idx_events_movie", "movie_id", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<UserEvent(id={self.id}, type={self.event_type}, user={self.user_id})>"
