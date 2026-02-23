"""
Recommendation Pydantic Schemas
"""

from pydantic import BaseModel

from app.schemas.movie import MovieListItem


class RecommendationParams(BaseModel):
    """Parameters for recommendation request"""
    mbti: str | None = None
    weather: str | None = None  # sunny, rainy, cloudy, snowy
    emotion: str | None = None  # healing, tension, touching, fun, horror, excitement, sadness
    limit: int = 20


class RecommendationTag(BaseModel):
    """Tag explaining why a movie was recommended"""
    type: str  # mbti, weather, personal, popular, rating
    label: str  # Display label like "#INTJ추천", "#비오는날"
    score: float | None = None  # Contribution score


class HybridMovieItem(MovieListItem):
    """Movie item with recommendation tags"""
    recommendation_tags: list[RecommendationTag] = []
    hybrid_score: float = 0.0  # Combined recommendation score
    recommendation_reason: str = ""  # Template-based reason sentence

    @classmethod
    def from_movie_with_tags(
        cls, movie, tags: list[RecommendationTag],
        hybrid_score: float = 0.0, reason: str = "",
    ):
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
            recommendation_tags=tags,
            hybrid_score=hybrid_score,
            recommendation_reason=reason,
        )


class RecommendationRow(BaseModel):
    """Schema for a recommendation row"""
    title: str
    description: str | None = None
    movies: list[MovieListItem]


class HybridRecommendationRow(BaseModel):
    """Schema for hybrid recommendation row with tags"""
    title: str
    description: str | None = None
    movies: list[HybridMovieItem]


class HomeRecommendations(BaseModel):
    """Schema for home page recommendations"""
    featured: MovieListItem | None = None
    rows: list[RecommendationRow]
    hybrid_row: HybridRecommendationRow | None = None  # Main personalized recommendation


class WeatherInfo(BaseModel):
    """Schema for weather information"""
    condition: str  # sunny, rainy, cloudy, snowy
    temperature: float
    city: str
    description: str
