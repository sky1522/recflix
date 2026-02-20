"""
Movie API endpoints
"""
import hashlib
import json
import logging
import math
import random as random_mod
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import distinct, extract, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.recommendation_constants import (
    AGE_RATING_MAP,
    DIVERSITY_ENABLED,
    SEMANTIC_GENRE_MAX,
)
from app.api.v1.semantic_search import is_semantic_search_available, search_similar
from app.core.deps import get_db
from app.core.rate_limit import limiter
from app.models import Genre, Movie, Person
from app.models.movie import movie_cast
from app.schemas import GenreResponse, MovieDetail, MovieListItem, PaginatedMovies
from app.services.embedding import get_query_embedding
from app.services.llm import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/movies", tags=["Movies"])

AUTOCOMPLETE_CACHE_TTL = 3600  # 1시간


@router.get("/search/autocomplete")
@limiter.limit("30/minute")
async def search_autocomplete(
    request: Request,
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Search autocomplete for movies, cast, and directors.
    Returns quick suggestions for search dropdown.
    Redis cached (1 hour TTL).
    """
    cache_key = f"autocomplete:{query.lower().strip()}:{limit}"

    # Check Redis cache
    redis = await get_redis_client()
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

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
            "poster_path": m.poster_path,
            "weighted_score": round(m.weighted_score, 1) if m.weighted_score else None
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

    # Save to Redis cache
    if redis:
        try:
            await redis.setex(cache_key, AUTOCOMPLETE_CACHE_TTL, json.dumps(results, ensure_ascii=False))
        except Exception:
            pass

    return results


@router.get("", response_model=PaginatedMovies)
@limiter.limit("60/minute")
def get_movies(
    request: Request,
    query: Optional[str] = None,
    genres: Optional[str] = Query(None, description="Comma-separated genre names"),
    person: Optional[str] = Query(None, description="Actor or director name"),
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    age_rating: Optional[str] = Query(None, regex="^(all|family|teen|adult)$"),
    sort_by: str = Query("popularity", regex="^(popularity|weighted_score|release_date)$"),
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

    # Filter by age rating
    if age_rating and age_rating in AGE_RATING_MAP:
        allowed = AGE_RATING_MAP[age_rating]
        q = q.filter(
            or_(Movie.certification.in_(allowed), Movie.certification.is_(None))
        )

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
@limiter.limit("60/minute")
def get_genres(request: Request, db: Session = Depends(get_db)):
    """Get all genres"""
    genres = db.query(Genre).order_by(Genre.name).all()
    return genres


@router.get("/onboarding", response_model=List[MovieListItem])
@limiter.limit("10/minute")
def get_onboarding_movies(
    request: Request,
    db: Session = Depends(get_db),
) -> list[MovieListItem]:
    """
    Get movies for onboarding: 40 popular, high-quality movies
    distributed across genres for new users to rate.
    """
    genres = db.query(Genre).all()
    genre_names = [g.name for g in genres]

    all_movies: list[Movie] = []
    seen_ids: set[int] = set()
    per_genre = max(4, 40 // len(genre_names) + 1)

    for genre_name in genre_names:
        movies = (
            db.query(Movie)
            .join(Movie.genres)
            .filter(
                Genre.name == genre_name,
                Movie.weighted_score >= 7.0,
                Movie.vote_count >= 500,
                extract("year", Movie.release_date) >= 2000,
                Movie.poster_path.isnot(None),
            )
            .order_by(func.random())
            .limit(per_genre)
            .all()
        )
        for m in movies:
            if m.id not in seen_ids:
                seen_ids.add(m.id)
                all_movies.append(m)

    random_mod.shuffle(all_movies)
    selected = all_movies[:40]
    return [MovieListItem.from_orm_with_genres(m) for m in selected]


SEMANTIC_RESULT_CACHE_TTL = 1800  # 30분


def _calculate_relevance(semantic_score: float, movie: Movie) -> float:
    """시맨틱 유사도 + 인기도 + 품질을 결합한 복합 점수."""
    vote_count = movie.vote_count or 0
    popularity_score = min(math.log1p(vote_count) / math.log1p(50000), 1.0)

    weighted = movie.weighted_score or 0.0
    quality_score = min(max(weighted / 10.0, 0), 1.0)

    return semantic_score * 0.50 + popularity_score * 0.30 + quality_score * 0.20


def _get_match_reason(
    semantic_score: float, popularity_score: float, quality_score: float,
) -> str:
    """추천 이유 태그 생성."""
    reasons: list[str] = []
    if semantic_score >= 0.45:
        reasons.append("분위기 일치")
    if quality_score >= 0.75:
        reasons.append("높은 평점")
    if popularity_score >= 0.5:
        reasons.append("많은 관객")
    return " · ".join(reasons) if reasons else "AI 추천"


def _diversify_semantic(
    scored_items: list[tuple[Movie, float, float]],
    limit: int,
    max_same_genre: int,
) -> list[tuple[Movie, float, float]]:
    """시맨틱 검색 결과에 장르 다양성 적용."""
    result: list[tuple[Movie, float, float]] = []
    skipped: list[tuple[Movie, float, float]] = []
    genre_count: dict[str, int] = {}

    for item in scored_items:
        movie = item[0]
        genres = [g.name for g in movie.genres] if movie.genres else []
        primary = genres[0] if genres else "기타"

        if genre_count.get(primary, 0) >= max_same_genre:
            skipped.append(item)
            continue

        result.append(item)
        genre_count[primary] = genre_count.get(primary, 0) + 1

        if len(result) >= limit:
            break

    while len(result) < limit and skipped:
        result.append(skipped.pop(0))

    return result


@router.get("/semantic-search")
@limiter.limit("10/minute")
async def semantic_search(
    request: Request,
    q: str = Query(..., min_length=2, description="Natural language query"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    시맨틱 검색 — 자연어 쿼리로 영화 검색.
    벡터 유사도(Voyage AI) + 품질 필터로 결과 반환.
    임베딩 미생성 시 키워드 검색으로 폴백.
    """
    t_start = time.time()

    # 결과 캐시 키
    params_str = f"{q.strip().lower()}:{limit}"
    result_hash = hashlib.md5(params_str.encode()).hexdigest()[:12]
    result_cache_key = f"semantic_res:{result_hash}"

    # 1. Redis 결과 캐시 확인
    redis = await get_redis_client()
    if redis:
        try:
            cached = await redis.get(result_cache_key)
            if cached:
                result = json.loads(cached)
                result["search_time_ms"] = round((time.time() - t_start) * 1000, 1)
                return result
        except Exception:
            pass

    # 2. 시맨틱 검색 불가 → 키워드 폴백
    if not is_semantic_search_available():
        return _keyword_fallback(q, limit, t_start, db)

    # 3. 쿼리 임베딩
    t_emb = time.time()
    embedding = await get_query_embedding(q)
    t_emb_done = time.time()
    if embedding is None:
        return _keyword_fallback(q, limit, t_start, db)

    # 4. 벡터 유사도 검색 (Top 300 — 재랭킹용 넓은 후보)
    t_search = time.time()
    candidates = search_similar(embedding, top_k=300)
    t_search_done = time.time()
    if not candidates:
        return _keyword_fallback(q, limit, t_start, db)

    candidate_ids = [mid for mid, _ in candidates]
    score_map = {mid: score for mid, score in candidates}

    # 5. DB에서 후보 영화 조회
    t_db = time.time()
    movies = (
        db.query(Movie)
        .options(selectinload(Movie.genres))
        .filter(Movie.id.in_(candidate_ids))
        .all()
    )
    movie_map = {m.id: m for m in movies}

    # 6. 복합 점수 재랭킹 + 품질 필터
    scored_items = []
    for mid in candidate_ids:
        m = movie_map.get(mid)
        if not m:
            continue
        ws = m.weighted_score or 0.0
        if ws < 5.0:
            continue

        sem = score_map.get(mid, 0.0)
        relevance = _calculate_relevance(sem, m)
        scored_items.append((m, sem, relevance))

    # relevance 기준 내림차순 정렬
    scored_items.sort(key=lambda x: x[2], reverse=True)

    # 장르 다양성 후처리: 같은 장르 최대 SEMANTIC_GENRE_MAX편
    if DIVERSITY_ENABLED:
        scored_items = _diversify_semantic(scored_items, limit, SEMANTIC_GENRE_MAX)

    results = []
    for m, sem, relevance in scored_items[:limit]:
        ws = m.weighted_score or 0.0
        vote_count = m.vote_count or 0
        pop = min(math.log1p(vote_count) / math.log1p(50000), 1.0)
        qual = min(max(ws / 10.0, 0), 1.0)
        genres = [g.name for g in m.genres] if m.genres else []

        results.append({
            "id": m.id,
            "title": m.title,
            "title_ko": m.title_ko,
            "poster_path": m.poster_path,
            "release_date": str(m.release_date) if m.release_date else None,
            "weighted_score": round(ws, 1),
            "genres": genres,
            "semantic_score": round(sem, 4),
            "relevance_score": round(relevance, 4),
            "match_reason": _get_match_reason(sem, pop, qual),
        })

    t_db_done = time.time()
    logger.info(
        "Semantic search timing: embedding=%.0fms search=%.0fms db=%.0fms total=%.0fms",
        (t_emb_done - t_emb) * 1000,
        (t_search_done - t_search) * 1000,
        (t_db_done - t_db) * 1000,
        (t_db_done - t_start) * 1000,
    )

    elapsed_ms = round((time.time() - t_start) * 1000, 1)
    response = {
        "query": q,
        "results": results,
        "total": len(results),
        "search_time_ms": elapsed_ms,
        "fallback": False,
    }

    # 7. Redis 결과 캐시 저장
    if redis and results:
        try:
            await redis.setex(
                result_cache_key,
                SEMANTIC_RESULT_CACHE_TTL,
                json.dumps(response, ensure_ascii=False),
            )
        except Exception:
            pass

    return response


def _keyword_fallback(
    query: str, limit: int, t_start: float, db: Session,
) -> dict:
    """시맨틱 검색 불가 시 기존 키워드 검색으로 폴백."""
    movies = (
        db.query(Movie)
        .options(selectinload(Movie.genres))
        .filter(
            or_(
                Movie.title.ilike(f"%{query}%"),
                Movie.title_ko.ilike(f"%{query}%"),
            )
        )
        .order_by(Movie.popularity.desc())
        .limit(limit)
        .all()
    )

    results = []
    for m in movies:
        ws = m.weighted_score or 0.0
        genres = [g.name for g in m.genres] if m.genres else []
        results.append({
            "id": m.id,
            "title": m.title,
            "title_ko": m.title_ko,
            "poster_path": m.poster_path,
            "release_date": str(m.release_date) if m.release_date else None,
            "weighted_score": round(ws, 1),
            "genres": genres,
            "semantic_score": 0.0,
        })

    return {
        "query": query,
        "results": results,
        "total": len(results),
        "search_time_ms": round((time.time() - t_start) * 1000, 1),
        "fallback": True,
    }


@router.get("/{movie_id}", response_model=MovieDetail)
@limiter.limit("60/minute")
def get_movie(request: Request, movie_id: int, db: Session = Depends(get_db)):
    """Get movie detail by ID"""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )

    return MovieDetail.from_orm_with_relations(movie)


@router.get("/{movie_id}/similar", response_model=List[MovieListItem])
@limiter.limit("60/minute")
def get_similar_movies(
    request: Request,
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
