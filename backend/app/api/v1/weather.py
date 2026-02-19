"""
Weather API endpoints
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.core.rate_limit import limiter

from app.services.weather import (
    get_weather_by_coords,
    get_weather_by_city,
    WeatherData,
)

router = APIRouter(prefix="/weather", tags=["Weather"])


class WeatherResponse(BaseModel):
    """날씨 응답 스키마"""
    condition: str  # sunny, rainy, cloudy, snowy
    temperature: float
    feels_like: float
    humidity: int
    description: str
    description_ko: str
    icon: str
    city: str
    country: str

    # 추천 관련 추가 정보
    recommendation_message: str
    theme_class: str

    class Config:
        from_attributes = True


def get_recommendation_message(condition: str) -> str:
    """날씨별 추천 메시지 생성"""
    messages = {
        "sunny": "화창한 날씨에는 신나는 모험 영화 어떠세요?",
        "rainy": "비 오는 날에는 감성적인 영화가 잘 어울려요",
        "cloudy": "흐린 날에는 편안한 힐링 영화를 추천드려요",
        "snowy": "눈 오는 날에는 따뜻한 로맨스 영화 어떠세요?",
    }
    return messages.get(condition, "오늘의 추천 영화를 확인해보세요!")


def get_theme_class(condition: str) -> str:
    """날씨별 테마 클래스"""
    themes = {
        "sunny": "theme-sunny",
        "rainy": "theme-rainy",
        "cloudy": "theme-cloudy",
        "snowy": "theme-snowy",
    }
    return themes.get(condition, "theme-default")


def weather_to_response(weather: WeatherData) -> WeatherResponse:
    """WeatherData를 API 응답으로 변환"""
    return WeatherResponse(
        condition=weather.condition,
        temperature=weather.temperature,
        feels_like=weather.feels_like,
        humidity=weather.humidity,
        description=weather.description,
        description_ko=weather.description_ko,
        icon=weather.icon,
        city=weather.city,
        country=weather.country,
        recommendation_message=get_recommendation_message(weather.condition),
        theme_class=get_theme_class(weather.condition),
    )


@router.get("", response_model=WeatherResponse)
@limiter.limit("60/minute")
async def get_weather(
    request: Request,
    lat: Optional[float] = Query(None, ge=-90, le=90, description="위도"),
    lon: Optional[float] = Query(None, ge=-180, le=180, description="경도"),
    city: Optional[str] = Query(None, description="도시명 (예: Seoul)"),
):
    """
    날씨 정보 조회

    좌표(lat, lon) 또는 도시명(city) 중 하나로 조회 가능
    둘 다 없으면 서울 기본값 사용
    """
    weather = None

    if lat is not None and lon is not None:
        # 좌표 기반 조회
        weather = await get_weather_by_coords(lat, lon)
    elif city:
        # 도시명 기반 조회
        weather = await get_weather_by_city(city)
    else:
        # 기본값: 서울
        weather = await get_weather_by_city("Seoul", "KR")

    if not weather:
        raise HTTPException(
            status_code=503,
            detail="날씨 정보를 가져올 수 없습니다"
        )

    return weather_to_response(weather)


@router.get("/conditions")
@limiter.limit("60/minute")
async def get_weather_conditions(request: Request):
    """
    지원하는 날씨 조건 목록
    """
    return {
        "conditions": [
            {
                "code": "sunny",
                "name_ko": "맑음",
                "icon": "01d",
                "description": "화창하고 맑은 날씨",
            },
            {
                "code": "rainy",
                "name_ko": "비",
                "icon": "10d",
                "description": "비가 오는 날씨",
            },
            {
                "code": "cloudy",
                "name_ko": "흐림",
                "icon": "03d",
                "description": "구름이 많은 날씨",
            },
            {
                "code": "snowy",
                "name_ko": "눈",
                "icon": "13d",
                "description": "눈이 오는 날씨",
            },
        ]
    }
