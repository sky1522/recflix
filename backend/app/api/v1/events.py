"""
User Event API endpoints - 사용자 행동 이벤트 로깅
"""
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_user_optional, get_db
from app.core.rate_limit import limiter
from app.models import User
from app.models.user_event import UserEvent
from app.schemas.user_event import EventBatch, EventCreate, EventResponse, EventStats

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
        db_event = UserEvent(
            user_id=current_user.id if current_user else None,
            session_id=event.session_id,
            event_type=event.event_type,
            movie_id=event.movie_id,
            metadata_=event.metadata,
        )
        db.add(db_event)
        db.commit()
    except Exception as e:
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
        db_events = [
            UserEvent(
                user_id=user_id,
                session_id=ev.session_id,
                event_type=ev.event_type,
                movie_id=ev.movie_id,
                metadata_=ev.metadata,
            )
            for ev in batch.events
        ]
        db.add_all(db_events)
        db.commit()
    except Exception as e:
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
