"""
Health Check Endpoint
"""
import logging
import os

from fastapi import APIRouter
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


def _check_database() -> str:
    """Check database connectivity."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return "connected"
    except SQLAlchemyError:
        return "disconnected"


def _check_redis() -> str:
    """Check Redis connectivity."""
    if not settings.REDIS_URL:
        return "disabled"
    try:
        import redis

        client = redis.from_url(settings.redis_connection_url, socket_timeout=2)
        client.ping()
        client.close()
        return "connected"
    except (RedisError, ConnectionError):
        return "disconnected"


@router.get("")
async def health_check() -> dict:
    """Detailed health check with component status."""
    from app.api.v1.recommendation_cf import is_cf_available
    from app.api.v1.semantic_search import is_semantic_search_available
    from app.services.reranker import get_reranker
    from app.services.two_tower_retriever import get_retriever

    return {
        "status": "ok",
        "environment": settings.APP_ENV,
        "database": _check_database(),
        "redis": _check_redis(),
        "semantic_search": "enabled" if is_semantic_search_available() else "disabled",
        "cf_model": "loaded" if is_cf_available() else "not_loaded",
        "two_tower": "loaded" if get_retriever() is not None else "not_loaded",
        "reranker": "loaded" if get_reranker() is not None else "not_loaded",
        "version": os.environ.get("GIT_SHA", os.environ.get("APP_VERSION", "v2.0.0")),
    }
