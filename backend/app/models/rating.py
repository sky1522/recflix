"""
Rating Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Rating(Base):
    """Rating model for user movie ratings"""
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete='CASCADE'), nullable=False, index=True)
    score = Column(Float, nullable=False)  # 0.5 ~ 5.0
    weather_context = Column(String(20), nullable=True)  # Weather at rating time
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one rating per user-movie pair
    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='uq_user_movie_rating'),
    )

    # Relationships
    user = relationship('User', back_populates='ratings')
    movie = relationship('Movie', backref='ratings')

    def __repr__(self):
        return f"<Rating(user_id={self.user_id}, movie_id={self.movie_id}, score={self.score})>"
