"""
Keyword Model
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.movie import movie_keywords


class Keyword(Base):
    """Keyword model for movie tags"""
    __tablename__ = 'keywords'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)

    # Relationships
    movies = relationship('Movie', secondary=movie_keywords, back_populates='keywords')

    def __repr__(self):
        return f"<Keyword(id={self.id}, name='{self.name}')>"
