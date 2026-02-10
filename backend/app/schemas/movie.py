"""
Movie Pydantic Schemas
"""
from datetime import date
from typing import Optional, List, Dict
from pydantic import BaseModel


class GenreResponse(BaseModel):
    """Schema for genre response"""
    id: int
    name: str
    name_ko: Optional[str]

    class Config:
        from_attributes = True


class PersonResponse(BaseModel):
    """Schema for person response"""
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieBase(BaseModel):
    """Base movie schema"""
    id: int
    title: str
    title_ko: Optional[str]
    certification: Optional[str]
    runtime: Optional[int]
    vote_average: float
    vote_count: int
    popularity: float
    poster_path: Optional[str]
    release_date: Optional[date]
    is_adult: bool


class MovieListItem(MovieBase):
    """Schema for movie list item (minimal)"""
    genres: List[str] = []

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_genres(cls, movie):
        return cls(
            id=movie.id,
            title=movie.title,
            title_ko=movie.title_ko,
            certification=movie.certification,
            runtime=movie.runtime,
            vote_average=movie.vote_average,
            vote_count=movie.vote_count,
            popularity=movie.popularity,
            poster_path=movie.poster_path,
            release_date=movie.release_date,
            is_adult=movie.is_adult,
            genres=[g.name for g in movie.genres]
        )


class MovieDetail(MovieBase):
    """Schema for movie detail"""
    overview: Optional[str]
    overview_ko: Optional[str]
    tagline: Optional[str]
    overview_lang: Optional[str]
    director: Optional[str] = None
    director_ko: Optional[str] = None
    cast_ko: Optional[str] = None
    production_countries_ko: Optional[str] = None
    release_season: Optional[str] = None
    weighted_score: Optional[float] = None
    genres: List[GenreResponse] = []
    cast_members: List[PersonResponse] = []
    keywords: List[str] = []
    countries: List[str] = []
    mbti_scores: Optional[Dict[str, float]] = None
    weather_scores: Optional[Dict[str, float]] = None
    emotion_tags: Optional[Dict[str, float]] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_relations(cls, movie):
        return cls(
            id=movie.id,
            title=movie.title,
            title_ko=movie.title_ko,
            certification=movie.certification,
            runtime=movie.runtime,
            vote_average=movie.vote_average,
            vote_count=movie.vote_count,
            popularity=movie.popularity,
            poster_path=movie.poster_path,
            release_date=movie.release_date,
            is_adult=movie.is_adult,
            overview=movie.overview,
            overview_ko=movie.overview_ko,
            tagline=movie.tagline,
            overview_lang=movie.overview_lang,
            director=movie.director,
            director_ko=movie.director_ko,
            cast_ko=movie.cast_ko,
            production_countries_ko=movie.production_countries_ko,
            release_season=movie.release_season,
            weighted_score=movie.weighted_score,
            genres=[GenreResponse.model_validate(g) for g in movie.genres],
            cast_members=[PersonResponse.model_validate(p) for p in movie.cast_members[:10]],
            keywords=[k.name for k in movie.keywords],
            countries=[c.name for c in movie.countries],
            mbti_scores=movie.mbti_scores,
            weather_scores=movie.weather_scores,
            emotion_tags=movie.emotion_tags
        )


class MovieSearchParams(BaseModel):
    """Schema for movie search parameters"""
    query: Optional[str] = None
    genres: Optional[List[str]] = None
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    sort_by: str = "popularity"  # popularity, vote_average, release_date
    sort_order: str = "desc"  # asc, desc
    page: int = 1
    page_size: int = 20


class PaginatedMovies(BaseModel):
    """Schema for paginated movie list"""
    items: List[MovieListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
