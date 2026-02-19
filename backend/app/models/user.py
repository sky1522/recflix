"""
User Model
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """User model"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(50), nullable=False)
    mbti = Column(String(4), nullable=True)
    birth_date = Column(Date, nullable=True)
    location_consent = Column(Boolean, default=False)
    experiment_group = Column(String(10), nullable=False, default="control", server_default="control")

    # Social login
    kakao_id = Column(String(50), unique=True, nullable=True)
    google_id = Column(String(100), unique=True, nullable=True)
    profile_image = Column(String(500), nullable=True)
    auth_provider = Column(String(20), default="email", server_default="email")

    # Onboarding
    onboarding_completed = Column(Boolean, default=False, server_default="false")
    preferred_genres = Column(Text, nullable=True)  # JSON 문자열 '["액션","SF"]'

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    collections = relationship('Collection', back_populates='user', cascade='all, delete-orphan')
    ratings = relationship('Rating', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
