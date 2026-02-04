"""
API v1 Router
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, movies, recommendations, collections, ratings, weather, interactions, llm

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(movies.router)
api_router.include_router(recommendations.router)
api_router.include_router(collections.router)
api_router.include_router(ratings.router)
api_router.include_router(weather.router)
api_router.include_router(interactions.router)
api_router.include_router(llm.router)
