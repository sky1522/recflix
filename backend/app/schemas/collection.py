"""
Collection Pydantic Schemas
"""
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.movie import MovieListItem


class CollectionBase(BaseModel):
    """Base collection schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    is_public: bool = False


class CollectionCreate(CollectionBase):
    """Schema for collection creation"""
    pass


class CollectionUpdate(BaseModel):
    """Schema for collection update"""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    is_public: bool | None = None


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
    movies: list[MovieListItem] = []


class AddMovieToCollection(BaseModel):
    """Schema for adding movie to collection"""
    movie_id: int
