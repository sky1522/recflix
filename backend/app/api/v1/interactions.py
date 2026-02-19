"""
User Interactions API - 평점/찜 상태 통합 조회
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.core.deps import get_db, get_current_user, get_current_user_optional
from app.core.rate_limit import limiter
from app.models import User, Movie, Rating, Collection, collection_movies
from app.schemas import MovieListItem

router = APIRouter(prefix="/interactions", tags=["Interactions"])


class MovieInteraction(BaseModel):
    """사용자의 영화 상호작용 상태"""
    movie_id: int
    rating: Optional[float] = None  # 0.5 ~ 5.0, None if not rated
    is_favorited: bool = False  # 찜 여부

    class Config:
        from_attributes = True


class MovieInteractionBulk(BaseModel):
    """여러 영화의 상호작용 상태"""
    interactions: dict[int, MovieInteraction]  # movie_id -> interaction


@router.get("/movie/{movie_id}", response_model=MovieInteraction)
@limiter.limit("30/minute")
def get_movie_interaction(
    request: Request,
    movie_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """특정 영화에 대한 사용자의 평점/찜 상태 조회"""
    if not current_user:
        return MovieInteraction(movie_id=movie_id)

    # 평점 조회
    rating = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id == movie_id
    ).first()

    # 찜 여부 조회 (기본 찜 컬렉션에서)
    favorites = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.name == "찜한 영화"
    ).first()

    is_favorited = False
    if favorites:
        is_favorited = db.query(collection_movies).filter(
            collection_movies.c.collection_id == favorites.id,
            collection_movies.c.movie_id == movie_id
        ).first() is not None

    return MovieInteraction(
        movie_id=movie_id,
        rating=rating.score if rating else None,
        is_favorited=is_favorited
    )


@router.post("/movies", response_model=MovieInteractionBulk)
@limiter.limit("30/minute")
def get_movies_interactions(
    request: Request,
    movie_ids: List[int],
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """여러 영화에 대한 사용자의 평점/찜 상태 일괄 조회"""
    interactions = {}

    for mid in movie_ids:
        interactions[mid] = MovieInteraction(movie_id=mid)

    if not current_user:
        return MovieInteractionBulk(interactions=interactions)

    # 평점 일괄 조회
    ratings = db.query(Rating).filter(
        Rating.user_id == current_user.id,
        Rating.movie_id.in_(movie_ids)
    ).all()

    for r in ratings:
        interactions[r.movie_id].rating = r.score

    # 찜 여부 일괄 조회
    favorites = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.name == "찜한 영화"
    ).first()

    if favorites:
        favorited_movies = db.query(collection_movies.c.movie_id).filter(
            collection_movies.c.collection_id == favorites.id,
            collection_movies.c.movie_id.in_(movie_ids)
        ).all()

        for (mid,) in favorited_movies:
            interactions[mid].is_favorited = True

    return MovieInteractionBulk(interactions=interactions)


@router.post("/favorite/{movie_id}")
@limiter.limit("30/minute")
def toggle_favorite(
    request: Request,
    movie_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """찜하기 토글 (찜 컬렉션에 추가/제거)"""
    # 영화 존재 확인
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        return {"error": "Movie not found"}, 404

    # 찜 컬렉션 가져오기 (없으면 생성)
    favorites = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.name == "찜한 영화"
    ).first()

    if not favorites:
        favorites = Collection(
            user_id=current_user.id,
            name="찜한 영화",
            description="내가 찜한 영화 목록",
            is_public=False
        )
        db.add(favorites)
        db.commit()
        db.refresh(favorites)

    # 토글
    if movie in favorites.movies:
        favorites.movies.remove(movie)
        is_favorited = False
    else:
        favorites.movies.append(movie)
        is_favorited = True

    db.commit()

    return {
        "movie_id": movie_id,
        "is_favorited": is_favorited,
        "message": "찜 추가" if is_favorited else "찜 해제"
    }


@router.get("/favorites", response_model=List[MovieListItem])
@limiter.limit("30/minute")
def get_favorites(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """찜한 영화 목록 조회"""
    favorites = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.name == "찜한 영화"
    ).first()

    if not favorites:
        return []

    offset = (page - 1) * page_size
    movies = favorites.movies[offset:offset + page_size]

    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/favorites/genres")
@limiter.limit("30/minute")
def get_favorite_genres(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """찜한 영화들의 장르 분포 (추천용)"""
    favorites = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.name == "찜한 영화"
    ).first()

    if not favorites or not favorites.movies:
        return {"genres": {}, "top_genres": []}

    # 장르 집계
    genre_counts: dict[str, int] = {}
    for movie in favorites.movies:
        for genre in movie.genres:
            genre_name = genre.name if hasattr(genre, 'name') else str(genre)
            genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1

    # 상위 5개 장르
    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "genres": genre_counts,
        "top_genres": [g[0] for g in top_genres]
    }
