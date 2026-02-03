"""
Weather Service - OpenWeatherMap API Integration with Redis Caching
"""
import httpx
import redis.asyncio as aioredis
from typing import Optional
from datetime import datetime
import json

from app.config import settings

# Redis 캐시 TTL (30분)
WEATHER_CACHE_TTL = 1800

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
        print(f"Redis connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        return _redis_client
    except Exception as e:
        print(f"Redis connection failed: {e}")
        _redis_client = None
        return None


class WeatherCondition:
    """날씨 상태를 RecFlix 카테고리로 매핑"""

    # OpenWeatherMap condition codes to RecFlix weather types
    # https://openweathermap.org/weather-conditions
    CONDITION_MAP = {
        # Thunderstorm (2xx)
        range(200, 300): "rainy",
        # Drizzle (3xx)
        range(300, 400): "rainy",
        # Rain (5xx)
        range(500, 600): "rainy",
        # Snow (6xx)
        range(600, 700): "snowy",
        # Atmosphere (7xx) - mist, fog, etc
        range(700, 800): "cloudy",
        # Clear (800)
        range(800, 801): "sunny",
        # Clouds (80x)
        range(801, 810): "cloudy",
    }

    @classmethod
    def from_code(cls, code: int) -> str:
        """OpenWeatherMap 코드를 RecFlix 날씨 타입으로 변환"""
        for code_range, weather_type in cls.CONDITION_MAP.items():
            if code in code_range:
                return weather_type
        return "cloudy"  # default


class WeatherData:
    """날씨 데이터 모델"""

    def __init__(
        self,
        condition: str,
        temperature: float,
        feels_like: float,
        humidity: int,
        description: str,
        description_ko: str,
        icon: str,
        city: str,
        country: str,
    ):
        self.condition = condition
        self.temperature = temperature
        self.feels_like = feels_like
        self.humidity = humidity
        self.description = description
        self.description_ko = description_ko
        self.icon = icon
        self.city = city
        self.country = country

    def to_dict(self) -> dict:
        return {
            "condition": self.condition,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "description": self.description,
            "description_ko": self.description_ko,
            "icon": self.icon,
            "city": self.city,
            "country": self.country,
        }


# 한글 날씨 설명 매핑
WEATHER_DESCRIPTIONS_KO = {
    "sunny": "맑음",
    "rainy": "비",
    "cloudy": "흐림",
    "snowy": "눈",
}


async def get_weather_by_coords(
    lat: float,
    lon: float,
) -> Optional[WeatherData]:
    """
    좌표 기반 날씨 조회

    Args:
        lat: 위도
        lon: 경도

    Returns:
        WeatherData or None if failed
    """
    if not settings.WEATHER_API_KEY or settings.WEATHER_API_KEY == "your-openweathermap-api-key":
        return _get_default_weather()

    # 캐시 키 생성 (소수점 2자리까지만 사용)
    cache_key = f"weather:coords:{round(lat, 2)}:{round(lon, 2)}"

    # Redis 캐시 확인
    redis = await get_redis_client()
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                print(f"Cache HIT: {cache_key}")
                data = json.loads(cached)
                return WeatherData(**data)
            print(f"Cache MISS: {cache_key}")
        except Exception as e:
            print(f"Redis get error: {e}")

    # OpenWeatherMap API 호출
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": settings.WEATHER_API_KEY,
                    "units": "metric",
                    "lang": "kr",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        print(f"Weather API error: {e}")
        return _get_default_weather()

    # 응답 파싱
    weather_code = data["weather"][0]["id"]
    condition = WeatherCondition.from_code(weather_code)

    weather_data = WeatherData(
        condition=condition,
        temperature=round(data["main"]["temp"], 1),
        feels_like=round(data["main"]["feels_like"], 1),
        humidity=data["main"]["humidity"],
        description=data["weather"][0]["description"],
        description_ko=WEATHER_DESCRIPTIONS_KO.get(condition, condition),
        icon=data["weather"][0]["icon"],
        city=data.get("name", ""),
        country=data.get("sys", {}).get("country", ""),
    )

    # Redis 캐시 저장
    if redis:
        try:
            await redis.setex(
                cache_key,
                WEATHER_CACHE_TTL,
                json.dumps(weather_data.to_dict(), ensure_ascii=False),
            )
            print(f"Cache SET: {cache_key} (TTL: {WEATHER_CACHE_TTL}s)")
        except Exception as e:
            print(f"Redis set error: {e}")

    return weather_data


async def get_weather_by_city(
    city: str,
    country_code: str = "KR",
) -> Optional[WeatherData]:
    """
    도시명 기반 날씨 조회

    Args:
        city: 도시명 (예: "Seoul", "Busan")
        country_code: 국가 코드 (예: "KR")

    Returns:
        WeatherData or None if failed
    """
    if not settings.WEATHER_API_KEY or settings.WEATHER_API_KEY == "your-openweathermap-api-key":
        return _get_default_weather()

    cache_key = f"weather:city:{city.lower()}:{country_code.lower()}"

    # Redis 캐시 확인
    redis = await get_redis_client()
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                print(f"Cache HIT: {cache_key}")
                data = json.loads(cached)
                return WeatherData(**data)
            print(f"Cache MISS: {cache_key}")
        except Exception as e:
            print(f"Redis get error: {e}")

    # OpenWeatherMap API 호출
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": f"{city},{country_code}",
                    "appid": settings.WEATHER_API_KEY,
                    "units": "metric",
                    "lang": "kr",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        print(f"Weather API error: {e}")
        return _get_default_weather()

    weather_code = data["weather"][0]["id"]
    condition = WeatherCondition.from_code(weather_code)

    weather_data = WeatherData(
        condition=condition,
        temperature=round(data["main"]["temp"], 1),
        feels_like=round(data["main"]["feels_like"], 1),
        humidity=data["main"]["humidity"],
        description=data["weather"][0]["description"],
        description_ko=WEATHER_DESCRIPTIONS_KO.get(condition, condition),
        icon=data["weather"][0]["icon"],
        city=data.get("name", ""),
        country=data.get("sys", {}).get("country", ""),
    )

    # Redis 캐시 저장
    if redis:
        try:
            await redis.setex(
                cache_key,
                WEATHER_CACHE_TTL,
                json.dumps(weather_data.to_dict(), ensure_ascii=False),
            )
            print(f"Cache SET: {cache_key} (TTL: {WEATHER_CACHE_TTL}s)")
        except Exception as e:
            print(f"Redis set error: {e}")

    return weather_data


def _get_default_weather() -> WeatherData:
    """API 키가 없거나 실패 시 기본 날씨 반환"""
    hour = datetime.now().hour

    if 6 <= hour < 18:
        condition = "sunny"
    else:
        condition = "cloudy"

    return WeatherData(
        condition=condition,
        temperature=20.0,
        feels_like=20.0,
        humidity=50,
        description="Default weather",
        description_ko=WEATHER_DESCRIPTIONS_KO.get(condition, "맑음"),
        icon="01d" if condition == "sunny" else "03d",
        city="Seoul",
        country="KR",
    )
