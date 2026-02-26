"""추천 노출(impression) 로깅 서비스.

추천 API가 응답을 반환할 때 호출되어,
어떤 알고리즘이 어떤 영화를 어떤 순서로 노출했는지를 기록합니다.
실패해도 추천 응답에 영향을 주지 않습니다.
"""
from __future__ import annotations

import structlog
from sqlalchemy import insert

from app.database import SessionLocal
from app.models.reco_impression import RecoImpression

logger = structlog.get_logger()


def log_impressions(
    *,
    request_id: str,
    user_id: int | None,
    session_id: str | None,
    experiment_group: str,
    algorithm_version: str,
    context: dict | None,
    sections: dict[str, list[tuple[int, int, float | None]]],
) -> None:
    """벌크 INSERT로 impression 기록.

    BackgroundTasks에서 호출되며, 별도 DB 세션을 생성하여 독립 실행합니다.

    Args:
        request_id: 추천 1회 요청 식별자 (UUID 문자열)
        user_id: 로그인 사용자 ID (비로그인 시 None)
        session_id: X-Session-ID 헤더 값
        experiment_group: A/B 테스트 그룹
        algorithm_version: 알고리즘 버전 문자열
        context: {weather, mood, mbti} 스냅샷
        sections: {"hybrid_row": [(movie_id, rank, score), ...], ...}
    """
    rows = []
    for section_name, items in sections.items():
        for movie_id, rank, score in items:
            rows.append({
                "request_id": request_id,
                "user_id": user_id,
                "session_id": session_id,
                "experiment_group": experiment_group,
                "algorithm_version": algorithm_version,
                "section": section_name,
                "movie_id": movie_id,
                "rank": rank,
                "score": score,
                "context": context,
            })

    if not rows:
        return

    db = SessionLocal()
    try:
        db.execute(insert(RecoImpression), rows)
        db.commit()
        logger.info(
            "impressions_logged",
            request_id=request_id,
            count=len(rows),
            sections=list(sections.keys()),
        )
    except Exception:
        db.rollback()
        logger.error(
            "impression_log_failed",
            request_id=request_id,
            count=len(rows),
            exc_info=True,
        )
    finally:
        db.close()
