"""
Movie API endpoints
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, extract, distinct, select

from app.core.deps import get_db
from app.models import Movie, Genre, Person
from app.models.movie import movie_cast
from app.schemas import (
    MovieListItem, MovieDetail, PaginatedMovies, GenreResponse
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/search/autocomplete")
def search_autocomplete(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Search autocomplete for movies, cast, and directors.
    Returns quick suggestions for search dropdown.
    """
    results = {
        "movies": [],
        "people": [],
        "query": query
    }

    # Search movies by title
    movies = db.query(Movie).filter(
        or_(
            Movie.title.ilike(f"%{query}%"),
            Movie.title_ko.ilike(f"%{query}%")
        )
    ).order_by(Movie.popularity.desc()).limit(limit).all()

    results["movies"] = [
        {
            "id": m.id,
            "title": m.title_ko or m.title,
            "title_en": m.title,
            "year": m.release_date.year if m.release_date else None,
            "poster_path": m.poster_path
        }
        for m in movies
    ]

    # Search people (cast/director)
    people = db.query(Person).filter(
        Person.name.ilike(f"%{query}%")
    ).limit(5).all()

    results["people"] = [
        {"id": p.id, "name": p.name}
        for p in people
    ]

    return results


@router.get("", response_model=PaginatedMovies)
def get_movies(
    query: Optional[str] = None,
    genres: Optional[str] = Query(None, description="Comma-separated genre names"),
    person: Optional[str] = Query(None, description="Actor or director name"),
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    sort_by: str = Query("popularity", regex="^(popularity|vote_average|release_date)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get movies with search, filter and pagination"""
    q = db.query(Movie)

    # Search by title, cast, or director
    if query:
        # Find person IDs matching query
        person_subq = db.query(Person.id).filter(
            Person.name.ilike(f"%{query}%")
        ).subquery()

        # Find movie IDs with matching cast/director
        movie_ids_by_person = db.query(distinct(movie_cast.c.movie_id)).filter(
            movie_cast.c.person_id.in_(select(person_subq))
        ).subquery()

        q = q.filter(
            or_(
                Movie.title.ilike(f"%{query}%"),
                Movie.title_ko.ilike(f"%{query}%"),
                Movie.id.in_(select(movie_ids_by_person))
            )
        )

    # Filter by person (direct filter)
    if person:
        person_ids = db.query(Person.id).filter(
            Person.name.ilike(f"%{person}%")
        ).subquery()
        movie_ids = db.query(movie_cast.c.movie_id).filter(
            movie_cast.c.person_id.in_(select(person_ids))
        ).subquery()
        q = q.filter(Movie.id.in_(select(movie_ids)))

    # Filter by genres
    if genres:
        genre_list = [g.strip() for g in genres.split(",")]
        q = q.join(Movie.genres).filter(Genre.name.in_(genre_list))

    # Filter by rating
    if min_rating is not None:
        q = q.filter(Movie.vote_average >= min_rating)
    if max_rating is not None:
        q = q.filter(Movie.vote_average <= max_rating)

    # Filter by year
    if year_from is not None:
        q = q.filter(extract('year', Movie.release_date) >= year_from)
    if year_to is not None:
        q = q.filter(extract('year', Movie.release_date) <= year_to)

    # Get total count
    total = q.count()

    # Sort
    sort_column = getattr(Movie, sort_by)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    q = q.order_by(sort_column.nulls_last())

    # Paginate
    offset = (page - 1) * page_size
    movies = q.offset(offset).limit(page_size).all()

    # Convert to response
    items = [MovieListItem.from_orm_with_genres(m) for m in movies]
    total_pages = (total + page_size - 1) // page_size

    return PaginatedMovies(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/genres", response_model=List[GenreResponse])
def get_genres(db: Session = Depends(get_db)):
    """Get all genres"""
    genres = db.query(Genre).order_by(Genre.name).all()
    return genres


@router.get("/{movie_id}", response_model=MovieDetail)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Get movie detail by ID"""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )

    return MovieDetail.from_orm_with_relations(movie)


@router.get("/{movie_id}/similar", response_model=List[MovieListItem])
def get_similar_movies(
    movie_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get similar movies"""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )

    similar = movie.similar[:limit]
    return [MovieListItem.from_orm_with_genres(m) for m in similar]
