"""
User Event Schemas
"""
from pydantic import BaseModel, field_validator

ALLOWED_EVENT_TYPES = {
    "movie_click",
    "movie_detail_view",
    "movie_detail_leave",
    "recommendation_impression",
    "search",
    "search_click",
    "rating",
    "favorite_add",
    "favorite_remove",
    "not_interested",
}


class EventCreate(BaseModel):
    """단일 이벤트 생성"""
    event_type: str
    movie_id: int | None = None
    session_id: str | None = None
    metadata: dict | None = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: {v}")
        return v


class EventBatch(BaseModel):
    """배치 이벤트 전송 (최대 50개)"""
    events: list[EventCreate]

    @field_validator("events")
    @classmethod
    def validate_batch_size(cls, v: list[EventCreate]) -> list[EventCreate]:
        if len(v) > 50:
            raise ValueError("Batch size must be <= 50")
        return v


class EventResponse(BaseModel):
    """이벤트 응답"""
    status: str


class EventStats(BaseModel):
    """이벤트 통계 응답"""
    period: str
    total_events: int
    by_type: dict[str, int]
    recommendation_ctr: dict
    unique_users: int
    unique_movies_clicked: int


class ABGroupStats(BaseModel):
    """A/B 그룹별 통계"""
    users: int
    total_clicks: int
    total_impressions: int
    ctr: float
    avg_detail_duration_ms: float | None
    rating_conversion: float
    favorite_conversion: float
    by_section: dict[str, dict[str, float | int]]


class ABReport(BaseModel):
    """A/B 테스트 리포트"""
    period: str
    groups: dict[str, ABGroupStats]
    winner: str | None
    confidence_note: str
