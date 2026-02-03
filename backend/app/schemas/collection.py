"""
Collection Pydantic Schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.movie import MovieListItem


class CollectionBase(BaseModel):
    """Base collection schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: bool = False


class CollectionCreate(CollectionBase):
    """Schema for collection creation"""
    pass


class CollectionUpdate(BaseModel):
    """Schema for collection update"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: Optional[bool] = None


class CollectionResponse(CollectionBase):
    """Schema for collection response"""
    id: int
    user_id: int
    created_at: datetime
    movie_count: int = 0

    class Config:
        from_attributes = True


class CollectionDetail(CollectionResponse):
    """Schema for collection detail with movies"""
    movies: List[MovieListItem] = []


class AddMovieToCollection(BaseModel):
    """Schema for adding movie to collection"""
    movie_id: int
