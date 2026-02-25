"""
User Event API endpoints - 사용자 행동 이벤트 로깅
"""
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_user_optional, get_db
from app.core.rate_limit import limiter
from app.models import User
from app.models.user_event import UserEvent
from app.schemas.user_event import (
    ABComparison,
    ABGroupStats,
    ABReport,
    EventBatch,
    EventCreate,
    EventResponse,
    EventStats,
)

from .ab_stats import (
    proportion_ci,
    query_avg_session_events,
    query_daily_active_users,
    query_rec_avg_rating,
    query_return_rate,
    z_test_proportions,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventResponse, status_code=201)
@limiter.limit("60/minute")
def create_event(
    request: Request,
    event: EventCreate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> EventResponse:
    """단일 이벤트 기록. 실패해도 200 반환."""
    try:
        metadata = event.metadata or {}
        if current_user:
            metadata["experiment_group"] = current_user.experiment_group
        db_event = UserEvent(
            user_id=current_user.id if current_user else None,
            session_id=event.session_id,
            event_type=event.event_type,
            movie_id=event.movie_id,
            metadata_=metadata,
        )
        db.add(db_event)
        db.commit()
    except SQLAlchemyError as e:
        logger.warning("Event logging failed: %s", e)
        db.rollback()
    return EventResponse(status="ok")


@router.post("/batch", response_model=EventResponse, status_code=201)
@limiter.limit("30/minute")
def create_events_batch(
    request: Request,
    batch: EventBatch,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
) -> EventResponse:
    """배치 이벤트 기록 (최대 50개). 실패해도 200 반환."""
    try:
        user_id = current_user.id if current_user else None
        exp_group = current_user.experiment_group if current_user else None
        db_events = []
        for ev in batch.events:
            metadata = ev.metadata or {}
            if exp_group:
                metadata["experiment_group"] = exp_group
            db_events.append(UserEvent(
                user_id=user_id,
                session_id=ev.session_id,
                event_type=ev.event_type,
                movie_id=ev.movie_id,
                metadata_=metadata,
            ))
        db.add_all(db_events)
        db.commit()
    except SQLAlchemyError as e:
        logger.warning("Batch event logging failed: %s", e)
        db.rollback()
    return EventResponse(status="ok")


@router.get("/stats", response_model=EventStats)
@limiter.limit("30/minute")
def get_event_stats(
    request: Request,
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventStats:
    """최근 N일 이벤트 통계 (인증 필수)."""
    since = datetime.now(UTC) - timedelta(days=days)

    # 전체 이벤트 수
    total = db.query(func.count(UserEvent.id)).filter(
        UserEvent.created_at >= since
    ).scalar() or 0

    # 타입별 집계
    type_rows = db.query(
        UserEvent.event_type, func.count(UserEvent.id)
    ).filter(
        UserEvent.created_at >= since
    ).group_by(UserEvent.event_type).all()
    by_type = {row[0]: row[1] for row in type_rows}

    # 고유 사용자 수
    unique_users = db.query(
        func.count(func.distinct(UserEvent.user_id))
    ).filter(
        UserEvent.created_at >= since,
        UserEvent.user_id.isnot(None),
    ).scalar() or 0

    # 클릭된 고유 영화 수
    unique_movies = db.query(
        func.count(func.distinct(UserEvent.movie_id))
    ).filter(
        UserEvent.created_at >= since,
        UserEvent.event_type == "movie_click",
        UserEvent.movie_id.isnot(None),
    ).scalar() or 0

    # 추천 CTR 계산 (impression 대비 click)
    impressions = by_type.get("recommendation_impression", 0)
    clicks = by_type.get("movie_click", 0)
    overall_ctr = round(clicks / impressions, 4) if impressions > 0 else 0.0

    # 섹션별 CTR (metadata의 section 필드 기반)
    section_rows = db.execute(text("""
        SELECT
            metadata->>'section' AS section,
            event_type,
            COUNT(*) AS cnt
        FROM user_events
        WHERE created_at >= :since
          AND event_type IN ('recommendation_impression', 'movie_click')
          AND metadata->>'section' IS NOT NULL
        GROUP BY metadata->>'section', event_type
    """), {"since": since}).fetchall()

    section_imp: dict[str, int] = {}
    section_clk: dict[str, int] = {}
    for section, event_type, cnt in section_rows:
        if event_type == "recommendation_impression":
            section_imp[section] = cnt
        elif event_type == "movie_click":
            section_clk[section] = cnt

    by_section = {}
    for section in set(section_imp) | set(section_clk):
        imp = section_imp.get(section, 0)
        clk = section_clk.get(section, 0)
        by_section[section] = round(clk / imp, 4) if imp > 0 else 0.0

    recommendation_ctr = {
        "overall": overall_ctr,
        "impressions": impressions,
        "clicks": clicks,
        "by_section": by_section,
    }

    return EventStats(
        period=f"{days}d",
        total_events=total,
        by_type=by_type,
        recommendation_ctr=recommendation_ctr,
        unique_users=unique_users,
        unique_movies_clicked=unique_movies,
    )


@router.get("/ab-report", response_model=ABReport)
@limiter.limit("30/minute")
def get_ab_report(
    request: Request,
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ABReport:
    """A/B 테스트 그룹별 추천 품질 리포트 (인증 필수)."""
    since = datetime.now(UTC) - timedelta(days=days)

    group_events = _gather_group_events(db, since)
    duration_map = _gather_duration_map(db, since)
    section_data = _gather_section_data(db, since)

    # Additional metrics
    rec_rating_map = query_rec_avg_rating(db, since)
    return_rate_map = query_return_rate(db, since)
    session_events_map = query_avg_session_events(db, since)
    daily_active = query_daily_active_users(db, since)

    # Build per-group stats
    groups, raw_data = _build_group_stats(
        db, since, group_events, duration_map, section_data,
        rec_rating_map, return_rate_map, session_events_map,
    )

    # Winner by CTR
    winner = max(groups, key=lambda g: groups[g].ctr) if groups else None

    # Statistical comparisons
    comparisons = _compute_comparisons(groups, raw_data)

    min_n = min((r["impressions"] for r in raw_data.values()), default=0)
    sample_note = (
        f"각 그룹 최소 노출 수: {min_n}. "
        "CTR Z-test는 그룹당 최소 30건 필요, 안정적 결과는 1000건 이상 권장."
    )

    return ABReport(
        period=f"{days}d",
        groups=groups,
        winner=winner,
        confidence_note="통계적 유의성은 comparisons 필드의 p_value/significant 참조",
        comparisons=comparisons,
        minimum_sample_note=sample_note,
        daily_active_users=daily_active if daily_active else None,
    )


# ---------------------------------------------------------------------------
# Helper functions for ab-report
# ---------------------------------------------------------------------------

def _gather_group_events(
    db: Session, since: datetime,
) -> dict[str, dict]:
    """Gather event counts and unique users per experiment group."""
    rows = db.execute(text("""
        SELECT
            COALESCE(metadata->>'experiment_group', 'unknown') AS exp_group,
            event_type,
            COUNT(*) AS cnt,
            COUNT(DISTINCT user_id) AS unique_users
        FROM user_events
        WHERE created_at >= :since
        GROUP BY exp_group, event_type
        ORDER BY exp_group, event_type
    """), {"since": since}).fetchall()

    group_data: dict[str, dict] = {}
    for exp_group, event_type, cnt, unique_users in rows:
        if exp_group not in group_data:
            group_data[exp_group] = {"events": {}, "users": set()}
        group_data[exp_group]["events"][event_type] = cnt
        if unique_users:
            group_data[exp_group]["users"].add(unique_users)
    return group_data


def _gather_duration_map(db: Session, since: datetime) -> dict[str, float]:
    """Average detail page duration per group."""
    rows = db.execute(text("""
        SELECT
            COALESCE(metadata->>'experiment_group', 'unknown') AS exp_group,
            AVG((metadata->>'duration_ms')::float) AS avg_duration
        FROM user_events
        WHERE created_at >= :since
          AND event_type = 'movie_detail_leave'
          AND metadata->>'duration_ms' IS NOT NULL
        GROUP BY exp_group
    """), {"since": since}).fetchall()
    return {r[0]: r[1] for r in rows}


def _gather_section_data(
    db: Session, since: datetime,
) -> dict[str, dict[str, dict[str, int]]]:
    """Per-group per-section click/impression counts."""
    rows = db.execute(text("""
        SELECT
            COALESCE(metadata->>'experiment_group', 'unknown') AS exp_group,
            metadata->>'section' AS section,
            event_type,
            COUNT(*) AS cnt
        FROM user_events
        WHERE created_at >= :since
          AND event_type IN ('recommendation_impression', 'movie_click')
          AND metadata->>'section' IS NOT NULL
        GROUP BY exp_group, section, event_type
    """), {"since": since}).fetchall()

    data: dict[str, dict[str, dict[str, int]]] = {}
    for exp_group, section, event_type, cnt in rows:
        if exp_group not in data:
            data[exp_group] = {}
        if section not in data[exp_group]:
            data[exp_group][section] = {"clicks": 0, "impressions": 0}
        if event_type == "movie_click":
            data[exp_group][section]["clicks"] = cnt
        elif event_type == "recommendation_impression":
            data[exp_group][section]["impressions"] = cnt
    return data


def _build_group_stats(
    db: Session,
    since: datetime,
    group_events: dict[str, dict],
    duration_map: dict[str, float],
    section_data: dict[str, dict[str, dict[str, int]]],
    rec_rating_map: dict[str, float],
    return_rate_map: dict[str, float],
    session_events_map: dict[str, float],
) -> tuple[dict[str, ABGroupStats], dict[str, dict[str, int]]]:
    """Build ABGroupStats for each group. Returns (groups, raw_data)."""
    groups: dict[str, ABGroupStats] = {}
    raw_data: dict[str, dict[str, int]] = {}

    for exp_group, data in group_events.items():
        events = data["events"]
        clicks = events.get("movie_click", 0)
        impressions = events.get("recommendation_impression", 0)
        detail_views = events.get("movie_detail_view", 0)
        ratings = events.get("rating", 0)
        favorites = events.get("favorite_add", 0)

        ctr = round(clicks / impressions, 4) if impressions > 0 else 0.0
        ci_lower, ci_upper = proportion_ci(clicks, impressions)
        rating_conv = round(ratings / detail_views, 4) if detail_views > 0 else 0.0
        fav_conv = round(favorites / detail_views, 4) if detail_views > 0 else 0.0

        # Section CTR
        by_section: dict[str, dict[str, float | int]] = {}
        for section, sec_data in section_data.get(exp_group, {}).items():
            sec_imp = sec_data["impressions"]
            sec_clk = sec_data["clicks"]
            by_section[section] = {
                "clicks": sec_clk,
                "impressions": sec_imp,
                "ctr": round(sec_clk / sec_imp, 4) if sec_imp > 0 else 0.0,
            }

        # Unique users
        user_count = db.execute(text("""
            SELECT COUNT(DISTINCT user_id) FROM user_events
            WHERE created_at >= :since
              AND COALESCE(metadata->>'experiment_group', 'unknown') = :group
              AND user_id IS NOT NULL
        """), {"since": since, "group": exp_group}).scalar() or 0

        # Funnel
        funnel = _build_funnel(clicks, impressions, detail_views, ratings, favorites)

        raw_data[exp_group] = {
            "clicks": clicks, "impressions": impressions,
            "detail_views": detail_views, "ratings": ratings, "favorites": favorites,
        }

        groups[exp_group] = ABGroupStats(
            users=user_count,
            total_clicks=clicks,
            total_impressions=impressions,
            ctr=ctr,
            ctr_ci_lower=ci_lower,
            ctr_ci_upper=ci_upper,
            avg_detail_duration_ms=duration_map.get(exp_group),
            rating_conversion=rating_conv,
            favorite_conversion=fav_conv,
            by_section=by_section,
            avg_rating_from_recs=rec_rating_map.get(exp_group),
            return_rate=return_rate_map.get(exp_group),
            avg_session_events=session_events_map.get(exp_group),
            funnel=funnel,
        )

    return groups, raw_data


def _build_funnel(
    clicks: int, impressions: int, detail_views: int, ratings: int, favorites: int,
) -> dict[str, float | int]:
    """Build conversion funnel: impression → click → detail → rating/favorite."""
    return {
        "impressions": impressions,
        "clicks": clicks,
        "click_rate": round(clicks / impressions, 4) if impressions > 0 else 0.0,
        "detail_views": detail_views,
        "detail_rate": round(detail_views / clicks, 4) if clicks > 0 else 0.0,
        "ratings": ratings,
        "rating_rate": round(ratings / detail_views, 4) if detail_views > 0 else 0.0,
        "favorites": favorites,
        "favorite_rate": round(favorites / detail_views, 4) if detail_views > 0 else 0.0,
    }


def _compute_comparisons(
    groups: dict[str, ABGroupStats],
    raw_data: dict[str, dict[str, int]],
) -> list[ABComparison]:
    """Compute Z-test comparisons for CTR and conversion rates between all pairs."""
    comparisons: list[ABComparison] = []
    names = sorted(groups.keys())

    for i, ga in enumerate(names):
        for gb in names[i + 1:]:
            da, db_ = raw_data[ga], raw_data[gb]

            # CTR comparison
            comparisons.append(_make_comparison(
                ga, gb, "ctr", groups[ga].ctr, groups[gb].ctr,
                da["clicks"], da["impressions"], db_["clicks"], db_["impressions"],
            ))

            # Rating conversion
            comparisons.append(_make_comparison(
                ga, gb, "rating_conversion",
                groups[ga].rating_conversion, groups[gb].rating_conversion,
                da["ratings"], da["detail_views"], db_["ratings"], db_["detail_views"],
            ))

            # Favorite conversion
            comparisons.append(_make_comparison(
                ga, gb, "favorite_conversion",
                groups[ga].favorite_conversion, groups[gb].favorite_conversion,
                da["favorites"], da["detail_views"], db_["favorites"], db_["detail_views"],
            ))

    return comparisons


def _make_comparison(
    ga: str, gb: str, metric: str,
    val_a: float, val_b: float,
    succ_a: int, n_a: int, succ_b: int, n_b: int,
) -> ABComparison:
    """Create a single ABComparison with Z-test result."""
    z, p = z_test_proportions(succ_a, n_a, succ_b, n_b)
    return ABComparison(
        group_a=ga, group_b=gb, metric=metric,
        value_a=val_a, value_b=val_b,
        difference=round(val_a - val_b, 6),
        z_statistic=z, p_value=p,
        significant=p is not None and p < 0.05,
        note="insufficient_data" if p is None else None,
    )
