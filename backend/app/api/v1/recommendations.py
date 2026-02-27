"""
Recommendation API endpoints.
Scoring logic lives in recommendation_engine.py, constants in recommendation_constants.py.
"""
import hashlib
import random
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy import desc
from sqlalchemy.orm import Session, selectinload

from app.api.v1.diversity import deduplicate_section, inject_serendipity
from app.api.v1.recommendation_constants import (
    DIVERSITY_ENABLED,
    MOOD_EMOTION_MAPPING,
    MOOD_SECTION_CONFIG,
    SERENDIPITY_MIN_QUALITY,
    SERENDIPITY_RATIO,
    WEATHER_TITLES,
    get_algorithm_version,
    get_experiment_weights,
)
from app.api.v1.recommendation_engine import (
    apply_age_rating_filter,
    calculate_hybrid_scores,
    get_movies_by_score,
    get_similar_movie_ids,
    get_user_preferences,
)
from app.api.v1.recommendation_reason import generate_reason
from app.core.deps import get_current_user, get_current_user_optional, get_db
from app.core.rate_limit import limiter
from app.models import Collection, Genre, Movie, User
from app.schemas import HomeRecommendations, MovieListItem, RecommendationRow
from app.schemas.recommendation import HybridMovieItem, HybridRecommendationRow
from app.services.reco_logger import log_impressions
from app.services.reranker import get_reranker
from app.services.two_tower_retriever import get_retriever

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def get_deterministic_group(
    user_id: int | None,
    session_id: str | None,
    weights: dict[str, int],
) -> str:
    """동일 사용자/세션은 항상 같은 그룹을 반환.

    로직:
    1. seed = str(user_id) if user_id else (session_id or "anonymous")
    2. bucket = md5(seed) % 100
    3. weights 순서대로 누적하여 bucket이 속하는 그룹 반환
    """
    seed = str(user_id) if user_id else (session_id or "anonymous")
    hash_val = int(hashlib.md5(seed.encode()).hexdigest(), 16)  # noqa: S324
    bucket = hash_val % 100

    cumulative = 0
    for group, weight in weights.items():
        cumulative += weight
        if bucket < cumulative:
            return group
    return list(weights.keys())[-1]  # fallback


def _prepare_reranker_input(
    movies: list,
    tt_score_map: dict[int, float],
    tt_candidates: list[tuple[int, float]],
    mbti: str | None,
    weather: str | None,
    mood: str | None,
) -> list[dict]:
    """Movie ORM 객체 → 재랭커 입력 딕셔너리 리스트."""
    rank_map = {mid: rank for rank, (mid, _) in enumerate(tt_candidates)}
    result = []
    for m in movies:
        genres = [g.name for g in m.genres] if m.genres else []
        emotion_tags = m.emotion_tags if isinstance(m.emotion_tags, dict) else {}
        mbti_scores = m.mbti_scores if isinstance(m.mbti_scores, dict) else {}
        weather_scores = m.weather_scores if isinstance(m.weather_scores, dict) else {}

        result.append({
            "movie_id": m.id,
            "genres": genres,
            "weighted_score": m.weighted_score or 0,
            "emotion_tags": emotion_tags,
            "mbti_score": mbti_scores.get(mbti, 0.0) if mbti else 0.0,
            "weather_score": weather_scores.get(weather, 0.0) if weather else 0.0,
            "tt_score": tt_score_map.get(m.id, 0.0),
            "rank": rank_map.get(m.id, 0),
        })
    return result


@router.get("", response_model=HomeRecommendations)
@limiter.limit("15/minute")
def get_home_recommendations(
    request: Request,
    background_tasks: BackgroundTasks,
    weather: str | None = Query(None, regex="^(sunny|rainy|cloudy|snowy)$"),
    mood: str | None = Query(None, regex="^(relaxed|tense|excited|emotional|imaginative|light|gloomy|stifled)$"),
    age_rating: str | None = Query(None, regex="^(all|family|teen|adult)$"),
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get home page recommendations with hybrid scoring"""
    request_id = str(uuid.uuid4())
    session_id = request.headers.get("X-Session-ID")
    experiment_group = get_deterministic_group(
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        weights=get_experiment_weights(),
    )
    algorithm_version = get_algorithm_version(experiment_group)

    rows = []
    mbti = current_user.mbti if current_user else None
    hybrid_row = None
    impression_sections: dict[str, list[tuple[int, int, float | None]]] = {}

    # Get user preferences if logged in
    favorited_ids: set = set()
    genre_counts: dict[str, int] = {}
    similar_ids: set = set()

    if current_user:
        favorited_ids, genre_counts, highly_rated_ids = get_user_preferences(db, current_user)
        user_movie_ids = favorited_ids | highly_rated_ids
        similar_ids = get_similar_movie_ids(db, user_movie_ids)

    # === HYBRID RECOMMENDATION ROW (Main personalized) ===
    if current_user and (mbti or weather or mood or genre_counts):
        retriever = get_retriever()

        if algorithm_version.startswith("twotower") and retriever is not None:
            # Two-Tower 경로: 후보 200개 → (LGBM 재랭킹 50개) → 하이브리드 재랭킹
            preferred_genres_list = sorted(genre_counts, key=genre_counts.get, reverse=True)[:5] if genre_counts else []
            tt_candidates = retriever.retrieve(
                mbti=mbti or "INTJ",
                preferred_genres=preferred_genres_list,
                top_k=200,
                exclude_ids=favorited_ids,
            )
            candidate_ids = [mid for mid, _ in tt_candidates]
            tt_score_map = {mid: score for mid, score in tt_candidates}

            if len(candidate_ids) >= 20:
                candidate_movies = (
                    db.query(Movie).options(selectinload(Movie.genres))
                    .filter(Movie.id.in_(candidate_ids))
                    .all()
                )

                # LGBM 재랭킹: Two-Tower 200 → GBDT Top 50
                reranker = get_reranker()
                if "lgbm" in algorithm_version and reranker is not None:
                    reranker_input = _prepare_reranker_input(
                        candidate_movies, tt_score_map, tt_candidates, mbti, weather, mood,
                    )
                    reranked = reranker.rerank(
                        reranker_input,
                        context={"mbti": mbti or "", "weather": weather or "", "mood": mood or ""},
                        top_k=50,
                    )
                    reranked_ids = [c["movie_id"] for c in reranked]
                    movie_map = {m.id: m for m in candidate_movies}
                    candidate_movies = [movie_map[mid] for mid in reranked_ids if mid in movie_map]
            else:
                # 후보 부족 → 기존 방식 보충
                algorithm_version = "twotower_v1_supplemented"
                candidate_q = db.query(Movie).options(selectinload(Movie.genres)).filter(
                    Movie.weighted_score >= 6.0,
                    ~Movie.id.in_(favorited_ids)
                )
                candidate_q = apply_age_rating_filter(candidate_q, age_rating)
                candidate_movies = candidate_q.order_by(desc(Movie.popularity), desc(Movie.weighted_score)).limit(200).all()
        elif algorithm_version.startswith("twotower"):
            # retriever 미로드 → fallback
            algorithm_version = "hybrid_v1_fallback"
            candidate_q = db.query(Movie).options(selectinload(Movie.genres)).filter(
                Movie.weighted_score >= 6.0,
                ~Movie.id.in_(favorited_ids)
            )
            candidate_q = apply_age_rating_filter(candidate_q, age_rating)
            candidate_movies = candidate_q.order_by(desc(Movie.popularity), desc(Movie.weighted_score)).limit(200).all()
        else:
            # 기존 경로: 전체 DB 스캔
            candidate_q = db.query(Movie).options(selectinload(Movie.genres)).filter(
                Movie.weighted_score >= 6.0,
                ~Movie.id.in_(favorited_ids)
            )
            candidate_q = apply_age_rating_filter(candidate_q, age_rating)
            candidate_movies = candidate_q.order_by(desc(Movie.popularity), desc(Movie.weighted_score)).limit(200).all()

        scored = calculate_hybrid_scores(
            db, candidate_movies, mbti, weather,
            genre_counts, favorited_ids, similar_ids, mood,
            experiment_group=experiment_group,
        )

        top_pool = scored[:60]
        top_recommendations = top_pool[:40]

        if top_recommendations:
            hybrid_movies = [
                HybridMovieItem.from_movie_with_tags(
                    m, tags, score,
                    reason=generate_reason(tags, m, mbti, weather, mood),
                )
                for m, score, tags in top_recommendations
            ]

            # Build title
            title_parts = []
            if mbti:
                title_parts.append(f"{mbti}")
            if weather:
                weather_emoji = {"sunny": "☀️", "rainy": "🌧️", "cloudy": "☁️", "snowy": "❄️"}
                title_parts.append(weather_emoji.get(weather, ""))
            if mood:
                mood_emoji = {"relaxed": "😌", "tense": "😰", "excited": "😆", "emotional": "💕", "imaginative": "🔮", "light": "😄", "gloomy": "😢", "stifled": "😤"}
                title_parts.append(mood_emoji.get(mood, ""))

            hybrid_title = "🎯 " + (" + ".join(title_parts) if title_parts else "당신을 위한") + " 맞춤 추천"

            desc_parts = []
            if mbti:
                desc_parts.append("MBTI")
            if weather:
                desc_parts.append("날씨")
            if mood:
                desc_parts.append("기분")
            desc_parts.append("취향")
            hybrid_desc = ", ".join(desc_parts) + "을 모두 고려한 추천"

            hybrid_row = HybridRecommendationRow(
                title=hybrid_title,
                description=hybrid_desc,
                movies=hybrid_movies
            )
            impression_sections["hybrid_row"] = [
                (m.id, rank, score)
                for rank, (m, score, _) in enumerate(top_recommendations)
            ]

    # === SECTION DEDUP: track seen movie IDs ===
    seen_ids: set[int] = set()

    if DIVERSITY_ENABLED and hybrid_row:
        for hm in hybrid_row.movies:
            seen_ids.add(hm.id)

    # === REGULAR RECOMMENDATION ROWS ===

    # MBTI-based recommendations
    mbti_row = None
    if mbti:
        mbti_movies = get_movies_by_score(db, "mbti_scores", mbti, limit=50, pool_size=120, age_rating=age_rating)
        if DIVERSITY_ENABLED:
            mbti_movies = deduplicate_section(mbti_movies, seen_ids)
        if mbti_movies:
            for m in mbti_movies:
                seen_ids.add(m.id)
            mbti_row = RecommendationRow(
                title=f"💜 {mbti} 성향 추천",
                description=f"{mbti} 유형에게 어울리는 영화",
                movies=[MovieListItem.from_orm_with_genres(m) for m in mbti_movies]
            )
            impression_sections["mbti_picks"] = [
                (m.id, rank, None) for rank, m in enumerate(mbti_movies)
            ]

    # Weather-based recommendations
    weather_row = None
    if weather:
        weather_movies = get_movies_by_score(db, "weather_scores", weather, limit=50, pool_size=120, age_rating=age_rating)
        if DIVERSITY_ENABLED:
            weather_movies = deduplicate_section(weather_movies, seen_ids)
        if weather_movies:
            for m in weather_movies:
                seen_ids.add(m.id)
            weather_row = RecommendationRow(
                title=WEATHER_TITLES.get(weather, f"{weather} 날씨 추천"),
                description=f"{weather} 날씨에 어울리는 영화",
                movies=[MovieListItem.from_orm_with_genres(m) for m in weather_movies]
            )
            impression_sections["weather_picks"] = [
                (m.id, rank, None) for rank, m in enumerate(weather_movies)
            ]

    # 기분별 추천 (동적) - 미선택 시 기본값 relaxed
    current_mood = mood if mood else "relaxed"
    mood_emotion_keys = MOOD_EMOTION_MAPPING.get(current_mood, ["healing"])
    primary_emotion = mood_emotion_keys[0]
    mood_movies = get_movies_by_score(db, "emotion_tags", primary_emotion, limit=50, pool_size=120, age_rating=age_rating)
    if DIVERSITY_ENABLED:
        mood_movies = deduplicate_section(mood_movies, seen_ids)
    mood_row = None
    if mood_movies:
        for m in mood_movies:
            seen_ids.add(m.id)
        mood_config = MOOD_SECTION_CONFIG.get(current_mood, {"title": "😌 편안한 기분일 때", "desc": "마음이 따뜻해지는 영화"})
        mood_row = RecommendationRow(
            title=mood_config["title"],
            description=mood_config["desc"],
            movies=[MovieListItem.from_orm_with_genres(m) for m in mood_movies]
        )
        impression_sections["mood_picks"] = [
            (m.id, rank, None) for rank, m in enumerate(mood_movies)
        ]

    # Popular movies (shuffle from top 100)
    popular_q = db.query(Movie).options(selectinload(Movie.genres)).filter(Movie.weighted_score >= 6.0)
    popular_q = apply_age_rating_filter(popular_q, age_rating)
    popular_pool = popular_q.order_by(Movie.popularity.desc(), Movie.weighted_score.desc()).limit(100).all()
    if DIVERSITY_ENABLED:
        popular_pool = deduplicate_section(popular_pool, seen_ids)
    popular = random.sample(popular_pool, min(50, len(popular_pool))) if popular_pool else []
    random.shuffle(popular)
    for m in popular:
        seen_ids.add(m.id)
    popular_row = RecommendationRow(
        title="🔥 인기 영화",
        description="지금 가장 핫한 영화들",
        movies=[MovieListItem.from_orm_with_genres(m) for m in popular]
    )
    impression_sections["popular"] = [
        (m.id, rank, None) for rank, m in enumerate(popular)
    ]

    # Top rated (shuffle from top 100)
    top_rated_q = db.query(Movie).options(selectinload(Movie.genres)).filter(Movie.weighted_score >= 6.0, Movie.vote_count >= 100)
    top_rated_q = apply_age_rating_filter(top_rated_q, age_rating)
    top_rated_pool = top_rated_q.order_by(Movie.weighted_score.desc(), Movie.vote_average.desc()).limit(100).all()
    if DIVERSITY_ENABLED:
        top_rated_pool = deduplicate_section(top_rated_pool, seen_ids)
    top_rated = random.sample(top_rated_pool, min(50, len(top_rated_pool))) if top_rated_pool else []
    random.shuffle(top_rated)
    top_rated_row = RecommendationRow(
        title="⭐ 높은 평점 영화",
        description="평점이 높은 명작들",
        movies=[MovieListItem.from_orm_with_genres(m) for m in top_rated]
    )
    impression_sections["top_rated"] = [
        (m.id, rank, None) for rank, m in enumerate(top_rated)
    ]

    # --- 섹션 순서 결정 ---
    if current_user:
        if mbti_row:
            rows.append(mbti_row)
        if weather_row:
            rows.append(weather_row)
        if mood_row:
            rows.append(mood_row)
        rows.append(popular_row)
        rows.append(top_rated_row)
    else:
        rows.append(popular_row)
        rows.append(top_rated_row)
        if weather_row:
            rows.append(weather_row)
        if mood_row:
            rows.append(mood_row)

    featured = popular[0] if popular else None

    if featured:
        impression_sections["featured"] = [(featured.id, 0, None)]

    # Background task: impression 로깅 (응답 지연 방지)
    background_tasks.add_task(
        log_impressions,
        request_id=request_id,
        user_id=current_user.id if current_user else None,
        session_id=session_id,
        experiment_group=experiment_group,
        algorithm_version=algorithm_version,
        context={"weather": weather, "mood": mood, "mbti": mbti},
        sections=impression_sections,
    )

    return HomeRecommendations(
        request_id=request_id,
        algorithm_version=algorithm_version,
        featured=MovieListItem.from_orm_with_genres(featured) if featured else None,
        rows=rows,
        hybrid_row=hybrid_row
    )


@router.get("/hybrid", response_model=list[HybridMovieItem])
@limiter.limit("15/minute")
def get_hybrid_recommendations(
    request: Request,
    weather: str | None = Query(None, regex="^(sunny|rainy|cloudy|snowy)$"),
    age_rating: str | None = Query(None, regex="^(all|family|teen|adult)$"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get hybrid recommendations with full scoring"""
    mbti = current_user.mbti
    session_id = request.headers.get("X-Session-ID")
    experiment_group = get_deterministic_group(
        user_id=current_user.id,
        session_id=session_id,
        weights=get_experiment_weights(),
    )

    favorited_ids, genre_counts, highly_rated_ids = get_user_preferences(db, current_user)
    user_movie_ids = favorited_ids | highly_rated_ids
    similar_ids = get_similar_movie_ids(db, user_movie_ids)

    candidate_q = db.query(Movie).options(selectinload(Movie.genres)).filter(
        Movie.weighted_score >= 6.0,
        ~Movie.id.in_(favorited_ids)
    )
    candidate_q = apply_age_rating_filter(candidate_q, age_rating)
    candidate_movies = candidate_q.order_by(desc(Movie.popularity), desc(Movie.weighted_score)).limit(300).all()

    scored = calculate_hybrid_scores(
        db, candidate_movies, mbti, weather,
        genre_counts, favorited_ids, similar_ids,
        experiment_group=experiment_group,
    )

    top_movies = scored[:limit]
    return [
        HybridMovieItem.from_movie_with_tags(
            m, tags, score,
            reason=generate_reason(tags, m, current_user.mbti, weather),
        )
        for m, score, tags in top_movies
    ]


@router.get("/weather", response_model=list[MovieListItem])
@limiter.limit("15/minute")
def get_weather_recommendations(
    request: Request,
    weather: str = Query(..., regex="^(sunny|rainy|cloudy|snowy)$"),
    age_rating: str | None = Query(None, regex="^(all|family|teen|adult)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get weather-based recommendations"""
    movies = get_movies_by_score(db, "weather_scores", weather, limit=limit, age_rating=age_rating)
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/mbti", response_model=list[MovieListItem])
@limiter.limit("15/minute")
def get_mbti_recommendations(
    request: Request,
    mbti: str = Query(..., regex="^[EI][NS][TF][JP]$"),
    age_rating: str | None = Query(None, regex="^(all|family|teen|adult)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get MBTI-based recommendations"""
    movies = get_movies_by_score(db, "mbti_scores", mbti, limit=limit, age_rating=age_rating)
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/emotion", response_model=list[MovieListItem])
@limiter.limit("15/minute")
def get_emotion_recommendations(
    request: Request,
    emotion: str = Query(..., regex="^(healing|tension|energy|romance|deep|fantasy|light)$"),
    age_rating: str | None = Query(None, regex="^(all|family|teen|adult)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get emotion-based recommendations (7 clusters)"""
    movies = get_movies_by_score(db, "emotion_tags", emotion, limit=limit, age_rating=age_rating)
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/popular", response_model=list[MovieListItem])
@limiter.limit("15/minute")
def get_popular_movies(
    request: Request,
    age_rating: str | None = Query(None, regex="^(all|family|teen|adult)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get popular movies (quality filter: weighted_score >= 6.0)"""
    q = db.query(Movie).options(selectinload(Movie.genres)).filter(Movie.weighted_score >= 6.0)
    q = apply_age_rating_filter(q, age_rating)
    movies = q.order_by(Movie.popularity.desc(), Movie.weighted_score.desc()).limit(limit).all()
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/top-rated", response_model=list[MovieListItem])
@limiter.limit("15/minute")
def get_top_rated_movies(
    request: Request,
    age_rating: str | None = Query(None, regex="^(all|family|teen|adult)$"),
    limit: int = Query(20, ge=1, le=100),
    min_votes: int = Query(100, ge=1),
    db: Session = Depends(get_db)
):
    """Get top rated movies (quality filter: weighted_score >= 6.0)"""
    q = db.query(Movie).options(selectinload(Movie.genres)).filter(Movie.weighted_score >= 6.0, Movie.vote_count >= min_votes)
    q = apply_age_rating_filter(q, age_rating)
    movies = q.order_by(Movie.weighted_score.desc(), Movie.vote_average.desc()).limit(limit).all()
    return [MovieListItem.from_orm_with_genres(m) for m in movies]


@router.get("/for-you", response_model=list[MovieListItem])
@limiter.limit("15/minute")
def get_personalized_recommendations(
    request: Request,
    age_rating: str | None = Query(None, regex="^(all|family|teen|adult)$"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """찜한 영화 기반 개인화 추천"""
    favorites = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.name == "찜한 영화"
    ).first()

    if not favorites or not favorites.movies:
        q = db.query(Movie).options(selectinload(Movie.genres)).filter(Movie.weighted_score >= 6.0)
        q = apply_age_rating_filter(q, age_rating)
        movies = q.order_by(Movie.popularity.desc(), Movie.weighted_score.desc()).limit(limit).all()
        return [MovieListItem.from_orm_with_genres(m) for m in movies]

    # 찜한 영화들의 장르 집계
    genre_counts: dict[str, int] = {}
    favorited_ids: set = set()

    for movie in favorites.movies:
        favorited_ids.add(movie.id)
        for genre in movie.genres:
            genre_name = genre.name if hasattr(genre, 'name') else str(genre)
            genre_counts[genre_name] = genre_counts.get(genre_name, 0) + 1

    if not genre_counts:
        q = db.query(Movie).options(selectinload(Movie.genres)).filter(Movie.weighted_score >= 6.0)
        q = apply_age_rating_filter(q, age_rating)
        movies = q.order_by(Movie.popularity.desc(), Movie.weighted_score.desc()).limit(limit).all()
        return [MovieListItem.from_orm_with_genres(m) for m in movies]

    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_genre_names = [g[0] for g in top_genres]

    q = db.query(Movie).options(selectinload(Movie.genres)).join(Movie.genres).filter(
        Genre.name.in_(top_genre_names),
        Movie.weighted_score >= 6.0,
        ~Movie.id.in_(favorited_ids)
    )
    q = apply_age_rating_filter(q, age_rating)
    movies = q.order_by(Movie.popularity.desc(), Movie.weighted_score.desc()).limit(limit * 3).all()

    seen: set = set()
    result = []
    for m in movies:
        if m.id not in seen:
            seen.add(m.id)
            result.append(m)

    # Serendipity injection
    if DIVERSITY_ENABLED and result:
        scored = [(m, 0.0, []) for m in result]
        scored = inject_serendipity(
            scored, limit, set(top_genre_names), db,
            serendipity_ratio=SERENDIPITY_RATIO,
            min_quality=SERENDIPITY_MIN_QUALITY,
        )
        result = [item[0] for item in scored[:limit]]
    else:
        result = result[:limit]

    return [MovieListItem.from_orm_with_genres(m) for m in result]
