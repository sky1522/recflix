"""RecFlix Database Models Package"""
from app.models.collection import Collection, collection_movies
from app.models.country import Country
from app.models.genre import GENRE_MAPPING, Genre
from app.models.keyword import Keyword
from app.models.movie import Movie, movie_cast, movie_countries, movie_genres, movie_keywords, similar_movies
from app.models.person import Person
from app.models.rating import Rating
from app.models.user import User
from app.models.user_event import UserEvent

__all__ = [
    'Movie',
    'Genre',
    'Person',
    'Keyword',
    'Country',
    'User',
    'Collection',
    'Rating',
    'UserEvent',
    'GENRE_MAPPING',
    'movie_genres',
    'movie_cast',
    'movie_keywords',
    'movie_countries',
    'similar_movies',
    'collection_movies',
]
