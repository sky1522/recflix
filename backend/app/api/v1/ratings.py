"""
Rating API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.models import User, Movie, Rating
from app.schemas import (
    RatingCreate, RatingUpdate, RatingResponse, RatingWithMovie, MovieListItem
)

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.get("/me", response_model=List[RatingWithMovie])
def get_my_ratings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's ratings"""
    offset = (page - 1) * page_size
    ratings = db.query(Rating).filter(
        Rating.user_id == current_user.id
    ).order_by(Rating.created_at.desc()).offset(offset).limit(page_size).all()

    result = []
    for r in ratings:
        result.append(RatingWithMovie(
            id=r.id,
            user_id=r.user_id,
            movie_id=r.movie_id,
            score=r.score,
            weather_context=r.weather_context,
            created_at=r.created_at,
            movie=MovieListItem.from_orm_with_genres(r.movie)
        ))

    return result


@router.post("", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_rating(
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update a rating"""
    # Check if movie exists
    movie = db.query(Movie).filter(Movie.id == rating_data.movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )

    # Check for existing rating
    existing = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == rating_data.movie_id
    ).first()

    if existing:
        # Update existing rating
        existing.score = rating_data.score
        existing.weather_context = rating_data.weather_context
        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new rating
        rating = Rating(
            user_id=current_user.id,
            movie_id=rating_data.movie_id,
            score=rating_data.score,
            weather_context=rating_data.weather_context
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
        return rating


@router.get("/{movie_id}", response_model=RatingResponse)
def get_my_rating_for_movie(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's rating for a specific movie"""
    rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == movie_id
    ).first()

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )

    return rating


@router.put("/{movie_id}", response_model=RatingResponse)
def update_rating(
    movie_id: int,
    rating_data: RatingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update rating for a movie"""
    rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == movie_id
    ).first()

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )

    rating.score = rating_data.score
    if rating_data.weather_context is not None:
        rating.weather_context = rating_data.weather_context

    db.commit()
    db.refresh(rating)

    return rating


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rating(
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete rating for a movie"""
    rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == movie_id
    ).first()

    if not rating:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rating not found"
        )

    db.delete(rating)
    db.commit()
