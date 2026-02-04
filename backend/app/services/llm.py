"""
LLM Service - Anthropic Claude API Integration with Redis Caching
"""
import anthropic
import redis.asyncio as aioredis
from typing import Optional

from app.config import settings

# Redis 캐시 TTL (24시간)
CATCHPHRASE_CACHE_TTL = 86400

# Redis 클라이언트 (싱글톤)
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> Optional[aioredis.Redis]:
    """Redis 클라이언트 가져오기 (싱글톤)"""
    global _redis_client

    if _redis_client is not None:
        try:
            await _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_client = None

    try:
        _redis_client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        await _redis_client.ping()
        return _redis_client
    except Exception as e:
        print(f"Redis connection failed: {e}")
        _redis_client = None
        return None


CATCHPHRASE_PROMPT = """당신은 영화 추천 전문가입니다. 다음 영화에 대해 한국어로 짧고 매력적인 캐치프레이즈를 작성해주세요.

영화 제목: {title}
장르: {genres}
줄거리: {overview}

규칙:
- 15자 이내로 작성
- 영화의 핵심 매력을 담아야 함
- 감탄사나 이모지 사용 금지
- 예시: "당신의 마음을 훔칠 로맨틱 판타지"

캐치프레이즈만 출력하세요:"""


async def generate_catchphrase(
    movie_id: int,
    title: str,
    overview: str,
    genres: list[str],
    fallback_tagline: Optional[str] = None,
) -> tuple[str, bool]:
    """
    영화에 대한 캐치프레이즈 생성 (Anthropic Claude API 사용)

    Args:
        movie_id: 영화 ID
        title: 영화 제목
        overview: 영화 줄거리
        genres: 영화 장르 목록
        fallback_tagline: API 실패 시 사용할 기본 태그라인

    Returns:
        tuple[str, bool]: (캐치프레이즈, 캐시 여부)
    """
    cache_key = f"catchphrase:{movie_id}"

    # Redis 캐시 확인
    redis = await get_redis_client()
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                print(f"Cache HIT: {cache_key}")
                return cached, True
            print(f"Cache MISS: {cache_key}")
        except Exception as e:
            print(f"Redis get error: {e}")

    # API 키 확인
    if not settings.ANTHROPIC_API_KEY:
        print("Anthropic API key not configured")
        return fallback_tagline or "매력적인 영화", False

    # Anthropic Claude API 호출
    try:
        prompt = CATCHPHRASE_PROMPT.format(
            title=title,
            genres=", ".join(genres) if genres else "알 수 없음",
            overview=overview[:500] if overview else "줄거리 정보 없음",
        )

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        catchphrase = message.content[0].text.strip()
        # 따옴표 제거
        catchphrase = catchphrase.strip('"\'')

    except Exception as e:
        print(f"Anthropic API error: {e}")
        return fallback_tagline or "매력적인 영화", False

    # Redis 캐시 저장
    if redis:
        try:
            await redis.setex(
                cache_key,
                CATCHPHRASE_CACHE_TTL,
                catchphrase,
            )
            print(f"Cache SET: {cache_key} (TTL: {CATCHPHRASE_CACHE_TTL}s)")
        except Exception as e:
            print(f"Redis set error: {e}")

    return catchphrase, False
