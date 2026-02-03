"""
Person Model (Actors, Directors)
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.movie import movie_cast


class Person(Base):
    """Person model for actors and directors"""
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)

    # Relationships
    movies = relationship('Movie', secondary=movie_cast, back_populates='cast_members')

    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name}')>"
