"""
Recommendation API endpoints
Hybrid recommendation engine combining MBTI, Weather, and Personal preferences
"""
import random
from typing import Optional, List, Dict, Tuple
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
from datetime import datetime, timedelta

from app.core.deps import get_db, get_current_user_optional, get_current_user
from app.models import Movie, User, Collection, Genre, Rating
from app.models.movie import similar_movies
from app.schemas import MovieListItem, RecommendationRow, HomeRecommendations
from app.schemas.recommendation import (
    HybridMovieItem, HybridRecommendationRow, RecommendationTag
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Hybrid scoring weights
WEIGHT_MBTI = 0.35
WEIGHT_WEATHER = 0.25
WEIGHT_PERSONAL = 0.40

# Weather label mapping
WEATHER_LABELS = {
    "sunny": "#맑은날",
    "rainy": "#비오는날",
    "cloudy": "#흐린날",
    "snowy": "#눈오는날"
}

WEATHER_TITLES = {
    "sunny": "☀️ 맑은 날 추천",
    "rainy": "🌧️ 비 오는 날 추천",
    "cloudy": "☁️ 흐린 날 추천",
    "snowy": "❄️ 눈 오는 날 추천"
}


def get_movies_by_score(
    db: Session,
    score_type: str,
    score_key: str,
    limit: int = 10,
    pool_size: int = 40,
    min_votes: int = 10,
    shuffle: bool = True
) -> List[Movie]:
    """
    Get movies sorted by a specific score with optional shuffling.
    Fetches top `pool_size` movies, then randomly selects `limit` from them.
    """
    result = db.execute(text(f"""
        SELECT id FROM movies
        WHERE vote_count >= :min_votes
        AND {score_type} IS NOT NULL
        AND {score_type}->>:score_key IS NOT NULL
        ORDER BY ({score_type}->>:score_key)::float DESC
        LIMIT :pool_size
    """), {"score_key": score_key, "pool_size": pool_size, "min_votes": min_votes}).fetchall()

    movie_ids = [row[0] for row in result]
    if not movie_ids:
        return []

    movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
    # Preserve order
    movie_dict = {m.id: m for m in movies}
    ordered_movies = [movie_dict[mid] for mid in movie_ids if mid in movie_dict]

    # Shuffle and limit
    if shuffle and len(ordered_movies) > limit:
        selected = random.sample(ordered_movies, limit)
        # Optionally shuffle the order too
        random.shuffle(selected)
        return selected

    return ordered_movies[:limit]


def get_user_preferences(
    db: Session,
    user: User
) -> Tuple[set, Dict[str, int], set]:
    """
    Get user preferences from favorites and ratings
    Returns: (favorited_ids, genre_counts, highly_rated_movie_ids)
    """
    favorited_ids = set()
    genre_counts: Dict[str, int] = {}
    highly_rated_ids = set()

    # Get favorites
    favorites = db.query(Collection).filter(
        Collection.user_id == user.id,
        Collection.name == "찜한 영화"
    ).first()

    if favorites and favorites.movies:
        for movie in favorites.movies:
            favorited_ids.add(movie.id)
            for genre in movie.genres:
                genre_name = genre.name if hasattr(genre, 'name') else str(genre)
                genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1

    # Get highly rated movies (score >= 4.0) from last 90 days
    recent_date = datetime.utcnow() - timedelta(days=90)
    high_ratings = db.query(Rating).filter(
        Rating.user_id == user.id,
        Rating.score >= 4.0,
        Rating.created_at >= recent_date
    ).all()

    for rating in high_ratings:
        highly_rated_ids.add(rating.movie_id)
        # Also count genres from highly rated movies (weighted more)
        movie = db.query(Movie).filter(Movie.id == rating.movie_id).first()
        if movie:
            for genre in movie.genres:
                genre_name = genre.name if hasattr(genre, 'name') else str(genre)
                genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 2  # Double weight

    return favorited_ids, genre_counts, highly_rated_ids


def get_similar_movie_ids(db: Session, movie_ids: set, limit: int = 50) -> set:
    """Get IDs of movies similar to the given movie IDs"""
    if not movie_ids:
        return set()

    result = db.execute(
        text("""
            SELECT DISTINCT similar_movie_id
            FROM similar_movies
            WHERE movie_id = ANY(:movie_ids)
            LIMIT :limit
        """),
        {"movie_ids": list(movie_ids), "limit": limit}
    ).fetchall()

    return {row[0] for row in result}


def calculate_hybrid_scores(
    db: Session,
    movies: List[Movie],
    mbti: Optional[str],
    weather: Optional[str],
    genre_counts: Dict[str, int],
    favorited_ids: set,
    similar_ids: set
) -> List[Tuple[Movie, float, List[RecommendationTag]]]:
    """
    Calculate hybrid scores for movies
    Score = (0.35 × MBTI) + (0.25 × Weather) + (0.40 × Personal)
    """
    scored_movies = []
    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3] if genre_counts else []
    top_genre_names = {g[0] for g in top_genres}

    for movie in movies:
        tags = []
        mbti_score = 0.0
        weather_score = 0.0
        personal_score = 0.0

        # 1. MBTI Score (35%)
        if mbti and movie.mbti_scores:
            mbti_val = movie.mbti_scores.get(mbti, 0.0)
            mbti_score = float(mbti_val) if mbti_val else 0.0
            if mbti_score > 0.5:
                tags.append(RecommendationTag(
                    type="mbti",
                    label=f"#{mbti}추천",
                    score=mbti_score
                ))

        # 2. Weather Score (25%)
        if weather and movie.weather_scores:
            weather_val = movie.weather_scores.get(weather, 0.0)
            weather_score = float(weather_val) if weather_val else 0.0
            if weather_score > 0.5:
                tags.append(RecommendationTag(
                    type="weather",
                    label=WEATHER_LABELS.get(weather, f"#{weather}"),
                    score=weather_score
                ))

        # 3. Personal Score (40%)
        movie_genre_names = {g.name for g in movie.genres}

        # Genre match bonus
        matching_genres = movie_genre_names & top_genre_names
        if matching_genres:
            genre_bonus = len(matching_genres) * 0.3
            personal_score += min(genre_bonus, 0.9)  # Cap at 0.9
            if len(matching_genres) >= 2:
                tags.append(RecommendationTag(
                    type="personal",
                    label="#취향저격",
                    score=personal_score
                ))

        # Similar movie bonus
        if movie.id in similar_ids:
            personal_score += 0.4
            if not any(t.label == "#취향저격" for t in tags):
                tags.append(RecommendationTag(
                    type="personal",
                    label="#비슷한영화",
                    score=0.4
                ))

        # High rating bonus (movie quality)
        if movie.vote_average >= 8.0 and movie.vote_count >= 100:
            personal_score += 0.2
            tags.append(RecommendationTag(
                type="rating",
                label="#명작",
                score=0.2
            ))
        elif movie.vote_average >= 7.5 and movie.vote_count >= 50:
            personal_score += 0.1

        # Calculate hybrid score
        hybrid_score = (
            (WEIGHT_MBTI * mbti_score) +
            (WEIGHT_WEATHER * weather_score) +
            (WEIGHT_PERSONAL * personal_score)
        )

        # Popularity boost (small)
        if movie.popularity > 100:
            hybrid_score += 0.05

        # Normalize to 0-1 range
        hybrid_score = min(max(hybrid_score, 0.0), 1.0)

        scored_movies.append((movie, hybrid_score, tags))

    # Sort by hybrid score descending
    scored_movies.sort(key=lambda x: x[1], reverse=True)
    return scored_movies


@router.get("", response_model=HomeRecommendations)
def get_home_recommendations(
    weather: Optional[str] = Query(None, regex="^(sunny|rainy|cloudy|snowy)$"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get home page recommendations with hybrid scoring"""
    rows = []
    mbti = current_user.mbti if current_user else None
    hybrid_row = None

    # Get user preferences if logged in
    favorited_ids = set()
    genre_counts: Dict[str, int] = {}
    similar_ids = set()

    if current_user:
        favorited_ids, genre_counts, highly_rated_ids = get_user_preferences(db, current_user)
        # Get similar movies to favorites and highly rated
        user_movie_ids = favorited_ids | highly_rated_ids
        similar_ids = get_similar_movie_ids(db, user_movie_ids)

    # === HYBRID RECOMMENDATION ROW (Main personalized) ===
    if current_user and (mbti or weather or genre_counts):
        # Get candidate movies
        candidate_movies = db.query(Movie).filter(
            Movie.vote_count >= 30,
            ~Movie.id.in_(favorited_ids)  # Exclude already favorited
        ).order_by(desc(Movie.popularity)).limit(200).all()

        # Calculate hybrid scores
        scored = calculate_hybrid_scores(
            db, candidate_movies, mbti, weather,
            genre_counts, favorited_ids, similar_ids
        )

        # Shuffle from top 40, pick 10
        top_pool = scored[:40]
        if len(top_pool) > 10:
            top_recommendations = random.sample(top_pool, 10)
            random.shuffle(top_recommendations)
        else:
            top_recommendations = top_pool

        if top_recommendations:
            hybrid_movies = [
                HybridMovieItem.from_movie_with_tags(m, tags, score)
                for m, score, tags in top_recommendations
            ]

            # Build title
            title_parts = []
            if mbti:
                title_parts.append(f"{mbti}")
            if weather:
                weather_emoji = {"sunny": "☀️", "rainy": "🌧️", "cloudy": "☁️", "snowy": "❄️"}
                title_parts.append(weather_emoji.get(weather, ""))

            hybrid_title = "🎯 " + (" + ".join(title_parts) if title_parts else "당신을 위한") + " 맞춤 추천"

            hybrid_row = HybridRecommendationRow(
                title=hybrid_title,
                description="MBTI, 날씨, 취향을 모두 고려한 추천",
                movies=hybrid_movies
            )

    # === REGULAR RECOMMENDATION ROWS ===

    # 1. Popular movies (shuffle from top 40)
    popular_pool = db.query(Movie).filter(
        Movie.vote_count >= 50
    ).order_by(Movie.popularity.desc()).limit(40).all()
    popular = random.sample(popular_pool, min(10, len(popular_pool))) if popular_pool else []
    random.shuffle(popular)
    rows.append(RecommendationRow(
        title="🔥 인기 영화",
        description="지금 가장 핫한 영화들",
        movies=[MovieListItem.from_orm_with_genres(m) for m in popular]
    ))

    # 2. Weather-based recommendations
    if weather:
        weather_movies = get_movies_by_score(db, "weather_scores", weather, limit=10, pool_size=40)
        if weather_movies:
            rows.append(RecommendationRow(
                title=WEATHER_TITLES.get(weather, f"{weather} 날씨 추천"),
                description=f"{weather} 날씨에 어울리는 영화",
                movies=[MovieListItem.from_orm_with_genres(m) for m in weather_movies]
            ))

    # 3. MBTI-based recommendations
    if mbti:
        mbti_movies = get_movies_by_score(db, "mbti_scores", mbti, limit=10, pool_size=40)
        if mbti_movies:
            rows.append(RecommendationRow(
                title=f"💜 {mbti} 성향 추천",
                description=f"{mbti} 유형에게 어울리는 영화",
                movies=[MovieListItem.from_orm_with_genres(m) for m in mbti_movies]
            ))

    # 4. Top rated (shuffle from top 40)
    top_rated_pool = db.query(Movie).filter(
        Movie.vote_count >= 100
    ).order_by(Movie.vote_average.desc()).limit(40).all()
    top_rated = random.sample(top_rated_pool, min(10, len(top_rated_pool))) if top_rated_pool else []
    random.shuffle(top_rated)
    rows.append(RecommendationRow(
        title="⭐ 높은 평점 영화",
        description="평점이 높은 명작들",
        movies=[MovieListItem.from_orm_with_genres(m) for m in top_rated]
    ))

    # 5. Healing movies
    healing_movies = get_movies_by_score(db, "emotion_tags", "healing", limit=10, pool_size=40)
    if healing_movies:
        rows.append(RecommendationRow(
            title="😊 힐링이 필요할 때",
            description="마음이 따뜻해지는 영화",
            movies=[MovieListItem.from_orm_with_genres(m) for m in healing_movies]
        ))

    # 6. Tension movies
    tension_movies = get_movies_by_score(db, "emotion_tags", "tension", limit=10, pool_size=40)
    if tension_movies:
        rows.append(RecommendationRow(
            title="😰 긴장감 넘치는",
            description="손에 땀을 쥐게 하는 영화",
            movies=[MovieListItem.from_orm_with_genres(m) for m in tension_movies]
        ))

    # Featured movie (random from top 10 popular)
    featured = random.choice(popular_pool[:10]) if popular_pool else None

    return HomeRecommendations(
        featured=MovieListItem.from_orm_with_genres(featured) if featured else None,
        rows=rows,
        hybrid_row=hybrid_row
    )


@router.get("/hybrid", response_model=List[HybridMovieItem])
def get_hybrid_recommendations(
    weather: Optional[str] = Query(None, regex="^(sunny|rainy|cloudy|snowy)$"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get hybrid recommendations with full scoring
    Score = (0.35 × MBTI) + (0.25 × Weather) + (0.40 × Personal)
    """
    mbti = current_user.mbti

    # Get user preferences
    favorited_ids, genre_counts, highly_rated_ids = get_user_preferences(db, current_user)
    user_movie_ids = favorited_ids | highly_rated_ids
    similar_ids = get_similar_movie_ids(db, user_movie_ids)

    # Get candidate movies
    candidate_movies = db.query(Movie).filter(
        Movie.vote_count >= 20,
        ~Movie.id.in_(favorited_ids)
    ).order_by(desc(Movie.popularity)).limit(300).all()

    # Calculate hybrid scores
    scored = calculate_hybrid_scores(
        db, candidate_movies, mbti, weather,
        genre_counts, favorited_ids, similar_ids
    )

    # Return top results
    top_movies = scored[:limit]
    return [
        HybridMovieItem.from_movie_with_tags(m, tags, score)
        for m, score, tags in top_movies
    ]


@router.get("/weather", response_model=List[MovieListItem])
def get_weather_recommendations(
    weather: str = Query(..., regex="^(sunny|rainy|cloudy|snowy)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get weather-based recommendations"""
    movies = get_movies_by_score(db, "weather_scores", weather, limit=limit)
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/mbti", response_model=List[MovieListItem])
def get_mbti_recommendations(
    mbti: str = Query(..., regex="^[EI][NS][TF][JP]$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get MBTI-based recommendations"""
    movies = get_movies_by_score(db, "mbti_scores", mbti, limit=limit)
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/emotion", response_model=List[MovieListItem])
def get_emotion_recommendations(
    emotion: str = Query(..., regex="^(healing|tension|touching|fun|horror|excitement|sadness)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get emotion-based recommendations"""
    movies = get_movies_by_score(db, "emotion_tags", emotion, limit=limit)
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/popular", response_model=List[MovieListItem])
def get_popular_movies(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get popular movies"""
    movies = db.query(Movie).filter(
        Movie.vote_count >= 10
    ).order_by(Movie.popularity.desc()).limit(limit).all()
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/top-rated", response_model=List[MovieListItem])
def get_top_rated_movies(
    limit: int = Query(20, ge=1, le=100),
    min_votes: int = Query(100, ge=1),
    db: Session = Depends(get_db)
):
    """Get top rated movies"""
    movies = db.query(Movie).filter(
        Movie.vote_count >= min_votes
    ).order_by(Movie.vote_average.desc()).limit(limit).all()
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/for-you", response_model=List[MovieListItem])
def get_personalized_recommendations(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    찜한 영화 기반 개인화 추천
    - 찜한 영화들의 장르 분석
    - 해당 장르의 인기 영화 중 아직 안 본 영화 추천
    """
    # 찜 컬렉션 조회
    favorites = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.name == "찜한 영화"
    ).first()

    if not favorites or not favorites.movies:
        # 찜한 영화 없으면 인기 영화 반환
        movies = db.query(Movie).filter(
            Movie.vote_count >= 50
        ).order_by(Movie.popularity.desc()).limit(limit).all()
        return [MovieListItem.from_orm_with_genres(m) for m in movies]

    # 찜한 영화들의 장르 집계
    genre_counts: dict[str, int] = {}
    favorited_ids = set()

    for movie in favorites.movies:
        favorited_ids.add(movie.id)
        for genre in movie.genres:
            genre_name = genre.name if hasattr(genre, 'name') else str(genre)
            genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1

    if not genre_counts:
        movies = db.query(Movie).filter(
            Movie.vote_count >= 50
        ).order_by(Movie.popularity.desc()).limit(limit).all()
        return [MovieListItem.from_orm_with_genres(m) for m in movies]

    # 상위 3개 장르
    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_genre_names = [g[0] for g in top_genres]

    # 해당 장르의 영화 중 찜하지 않은 인기 영화 추천
    movies = db.query(Movie).join(Movie.genres).filter(
        Genre.name.in_(top_genre_names),
        Movie.vote_count >= 30,
        ~Movie.id.in_(favorited_ids)
    ).order_by(Movie.popularity.desc()).limit(limit * 2).all()

    # 중복 제거 및 limit 적용
    seen = set()
    result = []
    for m in movies:
        if m.id not in seen:
            seen.add(m.id)
            result.append(m)
            if len(result) >= limit:
                break

    return [MovieListItem.from_orm_with_genres(m) for m in result]
