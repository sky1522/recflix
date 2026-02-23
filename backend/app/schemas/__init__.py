"""RecFlix Pydantic Schemas Package"""
from app.schemas.collection import (
    AddMovieToCollection,
    CollectionBase,
    CollectionCreate,
    CollectionDetail,
    CollectionResponse,
    CollectionUpdate,
)
from app.schemas.movie import (
    GenreResponse,
    MovieBase,
    MovieDetail,
    MovieListItem,
    MovieSearchParams,
    PaginatedMovies,
    PersonResponse,
)
from app.schemas.rating import RatingBase, RatingCreate, RatingResponse, RatingUpdate, RatingWithMovie
from app.schemas.recommendation import HomeRecommendations, RecommendationParams, RecommendationRow, WeatherInfo
from app.schemas.user import (
    MBTIUpdate,
    OnboardingComplete,
    SocialLoginRequest,
    SocialLoginResponse,
    Token,
    TokenRefresh,
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)

__all__ = [
    # User
    'UserBase', 'UserCreate', 'UserUpdate', 'UserResponse',
    'UserLogin', 'Token', 'TokenRefresh', 'MBTIUpdate',
    'SocialLoginRequest', 'SocialLoginResponse', 'OnboardingComplete',
    # Movie
    'GenreResponse', 'PersonResponse', 'MovieBase', 'MovieListItem',
    'MovieDetail', 'MovieSearchParams', 'PaginatedMovies',
    # Collection
    'CollectionBase', 'CollectionCreate', 'CollectionUpdate',
    'CollectionResponse', 'CollectionDetail', 'AddMovieToCollection',
    # Rating
    'RatingBase', 'RatingCreate', 'RatingUpdate',
    'RatingResponse', 'RatingWithMovie',
    # Recommendation
    'RecommendationParams', 'RecommendationRow',
    'HomeRecommendations', 'WeatherInfo',
]
