"""
Movie Pydantic Schemas
"""
from datetime import date

from pydantic import BaseModel


class GenreResponse(BaseModel):
    """Schema for genre response"""
    id: int
    name: str
    name_ko: str | None

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
    title_ko: str | None
    certification: str | None
    runtime: int | None
    vote_average: float
    vote_count: int
    popularity: float
    poster_path: str | None
    release_date: date | None
    is_adult: bool


class MovieListItem(MovieBase):
    """Schema for movie list item (minimal)"""
    genres: list[str] = []
    trailer_key: str | None = None

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
            genres=[g.name for g in movie.genres],
            trailer_key=movie.trailer_key,
        )


class MovieDetail(MovieBase):
    """Schema for movie detail"""
    overview: str | None
    tagline: str | None
    director: str | None = None
    director_ko: str | None = None
    cast_ko: str | None = None
    production_countries_ko: str | None = None
    release_season: str | None = None
    weighted_score: float | None = None
    trailer_key: str | None = None
    genres: list[GenreResponse] = []
    cast_members: list[PersonResponse] = []
    keywords: list[str] = []
    countries: list[str] = []
    mbti_scores: dict[str, float] | None = None
    weather_scores: dict[str, float] | None = None
    emotion_tags: dict[str, float] | None = None

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
            tagline=movie.tagline,
            director=movie.director,
            director_ko=movie.director_ko,
            cast_ko=movie.cast_ko,
            production_countries_ko=movie.production_countries_ko,
            release_season=movie.release_season,
            weighted_score=movie.weighted_score,
            trailer_key=movie.trailer_key,
            genres=[GenreResponse.model_validate(g) for g in movie.genres],
            cast_members=[PersonResponse.model_validate(p) for p in movie.cast_members[:10]],
            keywords=[k.name for k in movie.keywords],
            countries=[c.name for c in movie.countries],
            mbti_scores=movie.mbti_scores,
            weather_scores=movie.weather_scores,
            emotion_tags=movie.emotion_tags,
        )


class MovieSearchParams(BaseModel):
    """Schema for movie search parameters"""
    query: str | None = None
    genres: list[str] | None = None
    min_rating: float | None = None
    max_rating: float | None = None
    year_from: int | None = None
    year_to: int | None = None
    sort_by: str = "popularity"  # popularity, weighted_score, release_date
    sort_order: str = "desc"  # asc, desc
    page: int = 1
    page_size: int = 20


class PaginatedMovies(BaseModel):
    """Schema for paginated movie list"""
    items: list[MovieListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
