"""
Collection API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.rate_limit import limiter
from app.models import User, Movie, Collection
from app.schemas import (
    CollectionCreate, CollectionUpdate, CollectionResponse,
    CollectionDetail, AddMovieToCollection, MovieListItem
)

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.get("", response_model=List[CollectionResponse])
@limiter.limit("30/minute")
def get_my_collections(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's collections"""
    collections = db.query(Collection).filter(
        Collection.user_id == current_user.id
    ).order_by(Collection.created_at.desc()).all()

    result = []
    for c in collections:
        resp = CollectionResponse.model_validate(c)
        resp.movie_count = len(c.movies)
        result.append(resp)

    return result


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def create_collection(
    request: Request,
    collection_data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new collection"""
    collection = Collection(
        user_id=current_user.id,
        name=collection_data.name,
        description=collection_data.description,
        is_public=collection_data.is_public
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)

    resp = CollectionResponse.model_validate(collection)
    resp.movie_count = 0
    return resp


@router.get("/{collection_id}", response_model=CollectionDetail)
@limiter.limit("30/minute")
def get_collection(
    request: Request,
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get collection detail"""
    collection = db.query(Collection).filter(
        Collection.id == collection_id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    # Check access
    if collection.user_id != current_user.id and not collection.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return CollectionDetail(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        description=collection.description,
        is_public=collection.is_public,
        created_at=collection.created_at,
        movie_count=len(collection.movies),
        movies=[MovieListItem.from_orm_with_genres(m) for m in collection.movies]
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
@limiter.limit("30/minute")
def update_collection(
    request: Request,
    collection_id: int,
    collection_data: CollectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update collection"""
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    update_data = collection_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collection, field, value)

    db.commit()
    db.refresh(collection)

    resp = CollectionResponse.model_validate(collection)
    resp.movie_count = len(collection.movies)
    return resp


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
def delete_collection(
    request: Request,
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete collection"""
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    db.delete(collection)
    db.commit()


@router.post("/{collection_id}/movies", status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
def add_movie_to_collection(
    request: Request,
    collection_id: int,
    data: AddMovieToCollection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add movie to collection"""
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    movie = db.query(Movie).filter(Movie.id == data.movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )

    if movie in collection.movies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already in collection"
        )

    collection.movies.append(movie)
    db.commit()

    return {"message": "Movie added to collection"}


@router.delete("/{collection_id}/movies/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
def remove_movie_from_collection(
    request: Request,
    collection_id: int,
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove movie from collection"""
    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.user_id == current_user.id
    ).first()

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )

    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie or movie not in collection.movies:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not in collection"
        )

    collection.movies.remove(movie)
    db.commit()
