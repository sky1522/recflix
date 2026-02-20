"""
Recommendation diversity post-processing functions.
Applied after scoring to improve genre variety, freshness, and serendipity.
"""
import logging
import random
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models import Genre, Movie
from app.schemas.recommendation import RecommendationTag

logger = logging.getLogger(__name__)

# Type alias for scored movie tuples
ScoredMovie = tuple[Movie, float, list[RecommendationTag]]


def _get_primary_genre(movie: Movie) -> str:
    """영화의 primary genre(첫 번째 장르) 반환."""
    if movie.genres:
        return movie.genres[0].name
    return "기타"


def diversify_by_genre(
    scored_movies: list[ScoredMovie],
    limit: int,
    max_consecutive: int = 3,
) -> list[ScoredMovie]:
    """같은 primary genre가 max_consecutive개 연속되지 않도록 재배치.

    상위 pool 내에서만 재배치하므로 스코어 손실이 최소화됨.
    조건을 만족하는 영화가 없으면 제약을 완화하고 최고점 영화를 선택.
    """
    if not scored_movies or len(scored_movies) <= max_consecutive:
        return scored_movies

    result: list[ScoredMovie] = []
    remaining = list(scored_movies)
    genre_window: list[str] = []

    while len(result) < limit and remaining:
        selected = False
        for i, item in enumerate(remaining):
            movie = item[0]
            primary_genre = _get_primary_genre(movie)

            recent = genre_window[-(max_consecutive - 1):]
            if (
                len(recent) >= max_consecutive - 1
                and all(g == primary_genre for g in recent)
            ):
                continue

            result.append(item)
            genre_window.append(primary_genre)
            remaining.pop(i)
            selected = True
            break

        if not selected:
            # 모든 남은 영화가 연속 제한에 걸림 → 최고점 선택 (제약 완화)
            item = remaining.pop(0)
            result.append(item)
            genre_window.append(_get_primary_genre(item[0]))

    return result


def apply_genre_cap(
    scored_movies: list[ScoredMovie],
    limit: int,
    max_genre_ratio: float = 0.35,
) -> list[ScoredMovie]:
    """단일 장르가 전체의 max_genre_ratio를 초과하지 않도록 필터링.

    5편 이하일 때는 제한 없음. 부족하면 스킵된 영화로 채움.
    """
    if not scored_movies or limit <= 5:
        return scored_movies[:limit] if scored_movies else []

    result: list[ScoredMovie] = []
    skipped: list[ScoredMovie] = []
    genre_count: dict[str, int] = {}

    for item in scored_movies:
        if len(result) >= limit:
            break

        primary_genre = _get_primary_genre(item[0])
        count = genre_count.get(primary_genre, 0)
        max_allowed = max(int(limit * max_genre_ratio), 2)

        if count >= max_allowed:
            skipped.append(item)
            continue

        result.append(item)
        genre_count[primary_genre] = count + 1

    # 부족하면 skipped에서 채움
    while len(result) < limit and skipped:
        result.append(skipped.pop(0))

    return result


def ensure_freshness(
    scored_movies: list[ScoredMovie],
    limit: int,
    recent_years: int = 3,
    classic_years: int = 10,
    recent_ratio: float = 0.20,
    classic_ratio: float = 0.10,
) -> list[ScoredMovie]:
    """최신작/클래식 최소 비율을 보장하여 연도 다양성 확보.

    - 최신작(recent_years 이내): 최소 recent_ratio
    - 클래식(classic_years 이전): 최소 classic_ratio
    - 나머지: 스코어 순 채움
    """
    if not scored_movies or limit <= 3:
        return scored_movies[:limit] if scored_movies else []

    now_year = datetime.now().year
    recent_cutoff = now_year - recent_years
    classic_cutoff = now_year - classic_years

    recent: list[ScoredMovie] = []
    classic: list[ScoredMovie] = []
    middle: list[ScoredMovie] = []

    for item in scored_movies:
        movie = item[0]
        if movie.release_date:
            year = movie.release_date.year
            if year >= recent_cutoff:
                recent.append(item)
            elif year < classic_cutoff:
                classic.append(item)
            else:
                middle.append(item)
        else:
            middle.append(item)

    min_recent = max(int(limit * recent_ratio), 1)
    min_classic = max(int(limit * classic_ratio), 1)

    result: list[ScoredMovie] = []
    used_ids: set[int] = set()

    # 최신작 슬롯 채우기
    for item in recent[:min_recent]:
        result.append(item)
        used_ids.add(item[0].id)

    # 클래식 슬롯 채우기
    for item in classic[:min_classic]:
        result.append(item)
        used_ids.add(item[0].id)

    # 나머지는 원래 스코어 순으로 채움
    for item in scored_movies:
        if len(result) >= limit:
            break
        if item[0].id not in used_ids:
            result.append(item)
            used_ids.add(item[0].id)

    return result[:limit]


def inject_serendipity(
    scored_movies: list[ScoredMovie],
    limit: int,
    user_top_genres: set[str],
    db: Session,
    serendipity_ratio: float = 0.10,
    min_quality: float = 7.0,
) -> list[ScoredMovie]:
    """추천 리스트의 일부를 사용자 선호 장르 외의 고품질 영화로 대체.

    user_top_genres가 비어있으면 스킵.
    리스트의 70% 지점에 삽입하여 상위 관련성 높은 영화 유지.
    """
    if not scored_movies or not user_top_genres:
        return scored_movies

    serendipity_count = max(int(limit * serendipity_ratio), 1)
    main_count = limit - serendipity_count

    main_movies = scored_movies[:main_count]
    used_ids = {item[0].id for item in main_movies}

    # 사용자 선호 장르 외의 고품질 영화 조회
    serendipity_pool = (
        db.query(Movie)
        .options(selectinload(Movie.genres))
        .join(Movie.genres)
        .filter(
            Movie.weighted_score >= min_quality,
            ~Movie.id.in_(used_ids),
            ~Genre.name.in_(user_top_genres),
        )
        .order_by(func.random())
        .limit(serendipity_count * 5)
        .all()
    )

    # 중복 제거
    seen: set[int] = set()
    unique_pool: list[Movie] = []
    for m in serendipity_pool:
        if m.id not in seen and m.id not in used_ids:
            seen.add(m.id)
            unique_pool.append(m)

    count = min(serendipity_count, len(unique_pool))
    if count == 0:
        return scored_movies[:limit]

    selected = random.sample(unique_pool, count)

    # 메인 리스트 70% 지점에 삽입
    result = list(main_movies)
    insert_pos = int(main_count * 0.7)
    for i, movie in enumerate(selected):
        tag = RecommendationTag(
            type="serendipity", label="#의외의발견", score=0.0,
        )
        result.insert(insert_pos + i, (movie, 0.0, [tag]))

    return result[:limit]


def deduplicate_section(
    movies: list[Movie],
    seen_ids: set[int],
) -> list[Movie]:
    """이미 노출된 영화(seen_ids)를 제외한 영화 목록 반환."""
    return [m for m in movies if m.id not in seen_ids]
