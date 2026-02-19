"""RecFlix Pydantic Schemas Package"""
from app.schemas.user import (
    UserBase, UserCreate, UserUpdate, UserResponse,
    UserLogin, Token, TokenRefresh, MBTIUpdate,
    SocialLoginRequest, SocialLoginResponse, OnboardingComplete,
)
from app.schemas.movie import (
    GenreResponse, PersonResponse, MovieBase, MovieListItem,
    MovieDetail, MovieSearchParams, PaginatedMovies
)
from app.schemas.collection import (
    CollectionBase, CollectionCreate, CollectionUpdate,
    CollectionResponse, CollectionDetail, AddMovieToCollection
)
from app.schemas.rating import (
    RatingBase, RatingCreate, RatingUpdate,
    RatingResponse, RatingWithMovie
)
from app.schemas.recommendation import (
    RecommendationParams, RecommendationRow,
    HomeRecommendations, WeatherInfo
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
