"""
RecoInteraction Model - 사용자 반응 기록 (암묵적 피드백)
"""
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.database import Base


class RecoInteraction(Base):
    """클릭, 상세보기, 찜, 체류시간 등 암묵적 피드백"""

    __tablename__ = "reco_interactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(UUID(as_uuid=True), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(64), nullable=True)
    movie_id = Column(Integer, nullable=False)
    event_type = Column(String(32), nullable=False)
    dwell_ms = Column(Integer, nullable=True)
    position = Column(SmallInteger, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    interacted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_int_request", "request_id"),
        Index("idx_int_user_time", "user_id", "interacted_at"),
        Index("idx_int_movie", "movie_id", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<RecoInteraction(id={self.id}, type={self.event_type}, movie={self.movie_id})>"
