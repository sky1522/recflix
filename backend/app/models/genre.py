"""
Genre Model
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.movie import movie_genres


class Genre(Base):
    """Genre model"""
    __tablename__ = 'genres'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    name_ko = Column(String(50))

    # Relationships
    movies = relationship('Movie', secondary=movie_genres, back_populates='genres')

    def __repr__(self):
        return f"<Genre(id={self.id}, name='{self.name}')>"


# Predefined genres mapping (English -> Korean)
GENRE_MAPPING = {
    'SF': 'SF',
    'TV 영화': 'TV 영화',
    '가족': '가족',
    '공포': '공포',
    '다큐멘터리': '다큐멘터리',
    '드라마': '드라마',
    '로맨스': '로맨스',
    '모험': '모험',
    '미스터리': '미스터리',
    '범죄': '범죄',
    '서부': '서부',
    '스릴러': '스릴러',
    '애니메이션': '애니메이션',
    '액션': '액션',
    '역사': '역사',
    '음악': '음악',
    '전쟁': '전쟁',
    '코미디': '코미디',
    '판타지': '판타지',
}
