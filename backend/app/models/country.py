"""
Country Model
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.movie import movie_countries


class Country(Base):
    """Country model for production countries"""
    __tablename__ = 'countries'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    # Relationships
    movies = relationship('Movie', secondary=movie_countries, back_populates='countries')

    def __repr__(self):
        return f"<Country(id={self.id}, name='{self.name}')>"
