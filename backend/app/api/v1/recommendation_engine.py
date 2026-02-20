"""
Recommendation engine: pure scoring and query helper functions.
No FastAPI route definitions — those live in recommendations.py.
"""
import random
from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.api.v1.diversity import apply_genre_cap, diversify_by_genre, ensure_freshness
from app.api.v1.recommendation_cf import is_cf_available, normalize_cf_score, predict_cf_score
from app.api.v1.recommendation_constants import (
    AGE_RATING_MAP,
    DIVERSITY_ENABLED,
    FRESHNESS_CLASSIC_RATIO,
    FRESHNESS_RECENT_RATIO,
    GENRE_MAX_CONSECUTIVE,
    GENRE_MAX_RATIO,
    MOOD_EMOTION_MAPPING,
    MOOD_LABELS,
    QUALITY_BOOST_MAX,
    QUALITY_BOOST_MIN,
    WEATHER_LABELS,
    WEIGHT_CF,
    WEIGHT_CF_NO_MOOD,
    WEIGHT_MBTI,
    WEIGHT_MBTI_CF,
    WEIGHT_MBTI_NO_MOOD,
    WEIGHT_MBTI_NO_MOOD_CF,
    WEIGHT_MOOD,
    WEIGHT_MOOD_CF,
    WEIGHT_PERSONAL,
    WEIGHT_PERSONAL_CF,
    WEIGHT_PERSONAL_NO_MOOD,
    WEIGHT_PERSONAL_NO_MOOD_CF,
    WEIGHT_WEATHER,
    WEIGHT_WEATHER_CF,
    WEIGHT_WEATHER_NO_MOOD,
    WEIGHT_WEATHER_NO_MOOD_CF,
    WEIGHTS_HYBRID_A,
    WEIGHTS_HYBRID_A_NO_MOOD,
    WEIGHTS_HYBRID_B,
    WEIGHTS_HYBRID_B_NO_MOOD,
)
from app.models import Collection, Movie, Rating, User
from app.schemas.recommendation import RecommendationTag


def get_weights_for_group(
    experiment_group: str, use_mood: bool,
) -> tuple[float, float, float, float, float]:
    """실험 그룹별 가중치 반환: (mbti, weather, mood, personal, cf)"""
    if experiment_group == "test_a":
        w = WEIGHTS_HYBRID_A if use_mood else WEIGHTS_HYBRID_A_NO_MOOD
    elif experiment_group == "test_b":
        w = WEIGHTS_HYBRID_B if use_mood else WEIGHTS_HYBRID_B_NO_MOOD
    else:
        return _get_control_weights(use_mood)
    return (w["mbti"], w["weather"], w.get("mood", 0.0), w["personal"], w["cf"])


def _get_control_weights(
    use_mood: bool,
) -> tuple[float, float, float, float, float]:
    """control 그룹 가중치 (기존 로직)"""
    cf_available = is_cf_available()
    if use_mood and cf_available:
        return (WEIGHT_MBTI_CF, WEIGHT_WEATHER_CF, WEIGHT_MOOD_CF, WEIGHT_PERSONAL_CF, WEIGHT_CF)
    if use_mood:
        return (WEIGHT_MBTI, WEIGHT_WEATHER, WEIGHT_MOOD, WEIGHT_PERSONAL, 0.0)
    if cf_available:
        return (WEIGHT_MBTI_NO_MOOD_CF, WEIGHT_WEATHER_NO_MOOD_CF, 0.0, WEIGHT_PERSONAL_NO_MOOD_CF, WEIGHT_CF_NO_MOOD)
    return (WEIGHT_MBTI_NO_MOOD, WEIGHT_WEATHER_NO_MOOD, 0.0, WEIGHT_PERSONAL_NO_MOOD, 0.0)


def apply_age_rating_filter(query, age_rating: str | None):
    """Apply certification-based age rating filter to a SQLAlchemy query"""
    if age_rating and age_rating in AGE_RATING_MAP:
        allowed = AGE_RATING_MAP[age_rating]
        from sqlalchemy import or_
        query = query.filter(
            or_(Movie.certification.in_(allowed), Movie.certification.is_(None))
        )
    return query


def get_llm_movie_ids(db: Session) -> set:
    """Get IDs of LLM-processed movies (top 1000 by popularity)"""
    result = db.execute(text("""
        SELECT id FROM movies
        WHERE vote_count >= 50
        ORDER BY popularity DESC
        LIMIT 1000
    """)).fetchall()
    return set(row[0] for row in result)


def get_movies_by_score(
    db: Session,
    score_type: str,
    score_key: str,
    limit: int = 10,
    pool_size: int = 40,
    min_weighted_score: float = 6.0,
    shuffle: bool = True,
    llm_min_ratio: float = 0.3,
    age_rating: str | None = None
) -> list[Movie]:
    """
    Get movies sorted by a specific score with optional shuffling.
    Ensures minimum ratio of LLM-analyzed movies for quality.
    Quality filter: weighted_score >= min_weighted_score
    """
    llm_ids = get_llm_movie_ids(db)
    extended_pool = pool_size * 2

    # Build age rating SQL clause
    age_rating_clause = ""
    params: dict = {"score_key": score_key, "pool_size": extended_pool, "min_weighted_score": min_weighted_score}
    if age_rating and age_rating in AGE_RATING_MAP:
        allowed = AGE_RATING_MAP[age_rating]
        placeholders = ", ".join(f":cert_{i}" for i in range(len(allowed)))
        age_rating_clause = f"AND (certification IN ({placeholders}) OR certification IS NULL)"
        for i, cert in enumerate(allowed):
            params[f"cert_{i}"] = cert

    result = db.execute(text(f"""
        SELECT id, ({score_type}->>:score_key)::float as score FROM movies
        WHERE COALESCE(weighted_score, 0) >= :min_weighted_score
        AND {score_type} IS NOT NULL
        AND {score_type}->>:score_key IS NOT NULL
        {age_rating_clause}
        ORDER BY ({score_type}->>:score_key)::float DESC, weighted_score DESC
        LIMIT :pool_size
    """), params).fetchall()

    if not result:
        return []

    # Separate LLM and keyword movies
    llm_movies = [(row[0], row[1]) for row in result if row[0] in llm_ids]
    kw_movies = [(row[0], row[1]) for row in result if row[0] not in llm_ids]

    # Calculate minimum LLM count needed
    min_llm_count = int(pool_size * llm_min_ratio)

    # Build final selection with LLM guarantee
    selected_ids: list[int] = []

    llm_to_take = min(min_llm_count, len(llm_movies))
    selected_ids.extend([m[0] for m in llm_movies[:llm_to_take]])

    remaining = pool_size - len(selected_ids)
    all_remaining = [(m[0], m[1]) for m in llm_movies[llm_to_take:]] + kw_movies
    all_remaining.sort(key=lambda x: x[1], reverse=True)
    selected_ids.extend([m[0] for m in all_remaining[:remaining]])

    if not selected_ids:
        return []

    movies = db.query(Movie).filter(Movie.id.in_(selected_ids)).all()
    movie_dict = {m.id: m for m in movies}

    def get_score(mid: int) -> float:
        m = movie_dict.get(mid)
        if m and m.emotion_tags:
            return m.emotion_tags.get(score_key, 0) if score_type == 'emotion_tags' else 0
        return 0

    selected_ids.sort(key=get_score, reverse=True)
    ordered_movies = [movie_dict[mid] for mid in selected_ids if mid in movie_dict]

    if shuffle and len(ordered_movies) > limit:
        selected = random.sample(ordered_movies, limit)
        random.shuffle(selected)
        return selected

    return ordered_movies[:limit]


def get_user_preferences(
    db: Session,
    user: User
) -> tuple[set, dict[str, int], set]:
    """
    Get user preferences from favorites and ratings.
    Returns: (favorited_ids, genre_counts, highly_rated_movie_ids)
    """
    favorited_ids: set = set()
    genre_counts: dict[str, int] = {}
    highly_rated_ids: set = set()

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

    highly_rated_movie_ids = [r.movie_id for r in high_ratings]
    highly_rated_ids = set(highly_rated_movie_ids)

    if highly_rated_movie_ids:
        rated_movies = db.query(Movie).options(selectinload(Movie.genres)).filter(
            Movie.id.in_(highly_rated_movie_ids)
        ).all()
        for movie in rated_movies:
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
    movies: list[Movie],
    mbti: str | None,
    weather: str | None,
    genre_counts: dict[str, int],
    favorited_ids: set,
    similar_ids: set,
    mood: str | None = None,
    experiment_group: str = "control",
) -> list[tuple[Movie, float, list[RecommendationTag]]]:
    """
    Calculate hybrid scores for movies.
    Weights are determined by experiment_group (control/test_a/test_b).
    Final score is multiplied by a quality factor based on weighted_score (0.85~1.0).
    """
    scored_movies: list[tuple[Movie, float, list[RecommendationTag]]] = []
    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3] if genre_counts else []
    top_genre_names = {g[0] for g in top_genres}

    use_mood = mood is not None and mood in MOOD_EMOTION_MAPPING
    w_mbti, w_weather, w_mood, w_personal, w_cf = get_weights_for_group(experiment_group, use_mood)

    for movie in movies:
        tags: list[RecommendationTag] = []
        mbti_score = 0.0
        weather_score = 0.0
        mood_score = 0.0
        personal_score = 0.0

        # 1. MBTI Score
        if mbti and movie.mbti_scores:
            mbti_val = movie.mbti_scores.get(mbti, 0.0)
            mbti_score = float(mbti_val) if mbti_val else 0.0
            if mbti_score > 0.5:
                tags.append(RecommendationTag(
                    type="mbti",
                    label=f"#{mbti}추천",
                    score=mbti_score
                ))

        # 2. Weather Score
        if weather and movie.weather_scores:
            weather_val = movie.weather_scores.get(weather, 0.0)
            weather_score = float(weather_val) if weather_val else 0.0
            if weather_score > 0.5:
                tags.append(RecommendationTag(
                    type="weather",
                    label=WEATHER_LABELS.get(weather, f"#{weather}"),
                    score=weather_score
                ))

        # 3. Mood Score (emotion_tags 기반)
        if use_mood and movie.emotion_tags:
            emotion_keys = MOOD_EMOTION_MAPPING.get(mood, [])
            if emotion_keys:
                emotion_values = []
                for key in emotion_keys:
                    val = movie.emotion_tags.get(key, 0.0)
                    if val:
                        emotion_values.append(float(val))
                if emotion_values:
                    mood_score = sum(emotion_values) / len(emotion_values)
                    if mood_score > 0.5:
                        tags.append(RecommendationTag(
                            type="personal",
                            label=MOOD_LABELS.get(mood, f"#{mood}"),
                            score=mood_score
                        ))

        # 4. Personal Score
        movie_genre_names = {g.name for g in movie.genres}

        matching_genres = movie_genre_names & top_genre_names
        if matching_genres:
            genre_bonus = len(matching_genres) * 0.3
            personal_score += min(genre_bonus, 0.9)
            if len(matching_genres) >= 2:
                tags.append(RecommendationTag(
                    type="personal",
                    label="#취향저격",
                    score=personal_score
                ))

        if movie.id in similar_ids:
            personal_score += 0.4
            if not any(t.label == "#취향저격" for t in tags):
                tags.append(RecommendationTag(
                    type="personal",
                    label="#비슷한영화",
                    score=0.4
                ))

        # High quality tag
        ws = movie.weighted_score or 0.0
        if ws >= 7.5:
            tags.append(RecommendationTag(
                type="rating",
                label="#명작",
                score=0.2
            ))

        # 5. CF Score
        cf_score = 0.0
        if w_cf > 0:
            raw_cf = predict_cf_score(movie.id)
            if raw_cf is not None:
                cf_score = normalize_cf_score(raw_cf)

        # Calculate hybrid score
        hybrid_score = (
            (w_mbti * mbti_score) +
            (w_weather * weather_score) +
            (w_mood * mood_score) +
            (w_personal * personal_score) +
            (w_cf * cf_score)
        )

        # Popularity boost (small)
        if movie.popularity > 100:
            hybrid_score += 0.05

        # Quality correction: continuous boost based on weighted_score (6.0~max → 0.85~1.0)
        max_ws = 9.0
        quality_ratio = min(max((ws - 6.0) / (max_ws - 6.0), 0.0), 1.0)
        quality_factor = QUALITY_BOOST_MIN + (QUALITY_BOOST_MAX - QUALITY_BOOST_MIN) * quality_ratio
        hybrid_score *= quality_factor

        # Normalize to 0-1 range
        hybrid_score = min(max(hybrid_score, 0.0), 1.0)

        scored_movies.append((movie, hybrid_score, tags))

    scored_movies.sort(key=lambda x: x[1], reverse=True)

    # Diversity post-processing (does not modify scores, only reorders)
    if DIVERSITY_ENABLED:
        pool = len(scored_movies)
        scored_movies = apply_genre_cap(scored_movies, pool, GENRE_MAX_RATIO)
        scored_movies = diversify_by_genre(
            scored_movies, pool, GENRE_MAX_CONSECUTIVE,
        )
        scored_movies = ensure_freshness(
            scored_movies, pool,
            recent_ratio=FRESHNESS_RECENT_RATIO,
            classic_ratio=FRESHNESS_CLASSIC_RATIO,
        )

    return scored_movies
