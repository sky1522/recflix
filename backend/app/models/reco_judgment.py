"""
RecoJudgment Model - 명시적 판단 기록 (평점, 관심없음 등)
"""
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class RecoJudgment(Base):
    """평점, 관심없음, 테스터 관련성 라벨 등 명시적 판단"""

    __tablename__ = "reco_judgments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(UUID(as_uuid=True), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    movie_id = Column(Integer, nullable=False)
    label_type = Column(String(16), nullable=False)
    label_value = Column(Float, nullable=False)
    judged_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_jdg_user", "user_id", "judged_at"),
        Index("idx_jdg_request", "request_id"),
    )

    def __repr__(self) -> str:
        return f"<RecoJudgment(id={self.id}, user={self.user_id}, movie={self.movie_id})>"
