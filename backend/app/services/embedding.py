"""
Voyage AI Embedding Service — query text → 1024-dim vector.
Redis caching with binary storage (separate client, decode_responses=False).
"""
import hashlib
import logging

import httpx
import numpy as np
import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-multilingual-2"
EMBEDDING_DIM = 1024
EMBEDDING_CACHE_TTL = 86400  # 24시간

# Binary Redis client (decode_responses=False for raw bytes)
_redis_binary: aioredis.Redis | None = None


async def _get_binary_redis() -> aioredis.Redis | None:
    """임베딩 바이너리 저장용 Redis 클라이언트 (decode_responses=False)."""
    global _redis_binary

    if _redis_binary is not None:
        try:
            await _redis_binary.ping()
            return _redis_binary
        except Exception:
            _redis_binary = None

    try:
        if settings.REDIS_URL:
            _redis_binary = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=False,
                socket_connect_timeout=5,
            )
        else:
            _redis_binary = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=0,
                decode_responses=False,
                socket_connect_timeout=5,
            )
        await _redis_binary.ping()
        return _redis_binary
    except Exception as e:
        logger.warning("Binary Redis connection failed: %s", e)
        _redis_binary = None
        return None


def _cache_key(text: str) -> str:
    normalized = text.strip().lower()
    return f"semantic_emb:{hashlib.md5(normalized.encode()).hexdigest()[:12]}"


async def get_query_embedding(text: str) -> np.ndarray | None:
    """
    쿼리 텍스트를 Voyage AI로 임베딩 변환.
    Redis 캐싱 적용 (TTL 24시간).
    API 키 미설정 시 None 반환.
    """
    key = _cache_key(text)

    # Redis 캐시 확인
    redis = await _get_binary_redis()
    if redis:
        try:
            cached = await redis.get(key)
            if cached:
                logger.debug("Embedding cache HIT: %s", key)
                return np.frombuffer(cached, dtype=np.float32).copy()
        except Exception as e:
            logger.warning("Redis embedding get error: %s", e)

    # API 키 확인
    api_key = settings.VOYAGE_API_KEY
    if not api_key:
        logger.warning("VOYAGE_API_KEY not set — semantic search disabled")
        return None

    # Voyage AI API 호출
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                VOYAGE_API_URL,
                json={
                    "input": [text],
                    "model": VOYAGE_MODEL,
                    "input_type": "query",
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        embedding = np.array(
            data["data"][0]["embedding"], dtype=np.float32
        )
        logger.debug("Voyage AI embedding OK (%d dims)", len(embedding))
    except httpx.HTTPStatusError as e:
        logger.error("Voyage AI HTTP error %d: %s", e.response.status_code, e.response.text[:200])
        return None
    except Exception as e:
        logger.error("Voyage AI embedding error: %s", e)
        return None

    # Redis 캐시 저장
    if redis:
        try:
            await redis.setex(key, EMBEDDING_CACHE_TTL, embedding.tobytes())
        except Exception as e:
            logger.warning("Redis embedding set error: %s", e)

    return embedding
