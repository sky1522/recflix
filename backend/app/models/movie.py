"""
Movie Model
"""
from datetime import date
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, Date,
    Table, ForeignKey, ARRAY
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


# Association tables for many-to-many relationships
movie_genres = Table(
    'movie_genres',
    Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

movie_cast = Table(
    'movie_cast',
    Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True),
    Column('person_id', Integer, ForeignKey('persons.id', ondelete='CASCADE'), primary_key=True),
    Column('role', String(50), default='actor')  # actor, director
)

movie_keywords = Table(
    'movie_keywords',
    Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True),
    Column('keyword_id', Integer, ForeignKey('keywords.id', ondelete='CASCADE'), primary_key=True)
)

movie_countries = Table(
    'movie_countries',
    Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True),
    Column('country_id', Integer, ForeignKey('countries.id', ondelete='CASCADE'), primary_key=True)
)

similar_movies = Table(
    'similar_movies',
    Base.metadata,
    Column('movie_id', Integer, ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True),
    Column('similar_movie_id', Integer, ForeignKey('movies.id', ondelete='CASCADE'), primary_key=True)
)


class Movie(Base):
    """Movie model"""
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True, index=True)  # TMDB ID
    title = Column(String(500), nullable=False, index=True)
    title_ko = Column(String(500), index=True)
    certification = Column(String(20))
    runtime = Column(Integer)
    vote_average = Column(Float, default=0.0)
    vote_count = Column(Integer, default=0)
    overview = Column(Text)
    tagline = Column(String(500))
    release_date = Column(Date, index=True)
    popularity = Column(Float, default=0.0, index=True)
    poster_path = Column(String(200))
    is_adult = Column(Boolean, default=False)

    # New columns from CSV update
    director = Column(String(500))               # Director name (English/original)
    director_ko = Column(String(500))            # Director name (Korean)
    cast_ko = Column(Text)                       # Cast names in Korean (comma-separated)
    production_countries_ko = Column(Text)        # Production countries in Korean
    release_season = Column(String(10))           # 봄/여름/가을/겨울
    weighted_score = Column(Float, default=0.0)   # Pre-calculated weighted score

    # Recommendation scores (JSONB)
    mbti_scores = Column(JSONB, default={})      # {"INTJ": 0.8, "ENFP": 0.6, ...}
    weather_scores = Column(JSONB, default={})   # {"sunny": 0.7, "rainy": 0.9, ...}
    emotion_tags = Column(JSONB, default={})     # {"healing": 0.8, "tension": 0.3, ...}

    # Relationships
    genres = relationship('Genre', secondary=movie_genres, back_populates='movies')
    cast_members = relationship('Person', secondary=movie_cast, back_populates='movies')
    keywords = relationship('Keyword', secondary=movie_keywords, back_populates='movies')
    countries = relationship('Country', secondary=movie_countries, back_populates='movies')

    # Self-referential many-to-many for similar movies
    similar = relationship(
        'Movie',
        secondary=similar_movies,
        primaryjoin=id == similar_movies.c.movie_id,
        secondaryjoin=id == similar_movies.c.similar_movie_id,
        backref='similar_to'
    )

    def __repr__(self):
        return f"<Movie(id={self.id}, title='{self.title}')>"
