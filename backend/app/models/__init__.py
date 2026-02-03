"""RecFlix Database Models Package"""
from app.models.movie import Movie, movie_genres, movie_cast, movie_keywords, movie_countries, similar_movies
from app.models.genre import Genre, GENRE_MAPPING
from app.models.person import Person
from app.models.keyword import Keyword
from app.models.country import Country
from app.models.user import User
from app.models.collection import Collection, collection_movies
from app.models.rating import Rating

__all__ = [
    'Movie',
    'Genre',
    'Person',
    'Keyword',
    'Country',
    'User',
    'Collection',
    'Rating',
    'GENRE_MAPPING',
    'movie_genres',
    'movie_cast',
    'movie_keywords',
    'movie_countries',
    'similar_movies',
    'collection_movies',
]
