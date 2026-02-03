"""
Rating Pydantic Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.movie import MovieListItem


class RatingBase(BaseModel):
    """Base rating schema"""
    score: float = Field(..., ge=0.5, le=5.0)
    weather_context: Optional[str] = None


class RatingCreate(RatingBase):
    """Schema for rating creation"""
    movie_id: int


class RatingUpdate(BaseModel):
    """Schema for rating update"""
    score: float = Field(..., ge=0.5, le=5.0)
    weather_context: Optional[str] = None


class RatingResponse(RatingBase):
    """Schema for rating response"""
    id: int
    user_id: int
    movie_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RatingWithMovie(RatingResponse):
    """Schema for rating with movie info"""
    movie: MovieListItem
