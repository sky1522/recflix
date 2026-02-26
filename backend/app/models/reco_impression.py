"""
RecoImpression Model - 추천 노출 기록
"""
from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.database import Base


class RecoImpression(Base):
    """추천 리스트가 사용자에게 보여질 때마다 기록"""

    __tablename__ = "reco_impressions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    request_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(64), nullable=True)
    experiment_group = Column(String(16), nullable=False)
    algorithm_version = Column(String(64), nullable=False)
    section = Column(String(32), nullable=False)
    movie_id = Column(Integer, nullable=False)
    rank = Column(SmallInteger, nullable=False)
    score = Column(Float, nullable=True)
    context = Column(JSONB, nullable=True)
    served_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("idx_imp_request", "request_id"),
        Index("idx_imp_user_time", "user_id", "served_at"),
        Index("idx_imp_algo", "algorithm_version", "served_at"),
    )

    def __repr__(self) -> str:
        return f"<RecoImpression(id={self.id}, request={self.request_id}, movie={self.movie_id})>"
