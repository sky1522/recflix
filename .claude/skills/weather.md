# 날씨 서비스

## 핵심 파일
→ `backend/app/services/weather.py` (420 LOC)
→ `backend/app/api/v1/weather.py` (141 LOC)
→ `frontend/hooks/useWeather.ts` (237 LOC)
→ `frontend/components/weather/WeatherBanner.tsx` (198 LOC)

## OpenWeatherMap 연동
→ weather.py의 API 호출 로직 참조
- 좌표 기반: `/api/v1/weather?lat=37.5&lon=127`
- 도시 기반: `/api/v1/weather?city=Seoul`
- 날씨 조건: sunny, rainy, cloudy, snowy (4종)

## 역지오코딩 + 한글 도시명
→ weather.py의 `reverse_geocode` + 70개 한글 도시명 매핑 참조

## 캐싱

### Backend (Redis)
→ weather.py의 Redis 캐싱 참조
- 키: `weather:v2:coords:{lat}:{lon}`, `weather:v2:city:{city}`
- TTL: 30분

### Frontend (localStorage)
→ useWeather.ts의 localStorage 캐싱 참조
- 키: `constants.ts`의 `WEATHER_CACHE_KEY` (`recflix_weather_v3`)
- TTL: 30분 (`WEATHER_CACHE_DURATION`)

## 날씨 테마
→ `frontend/app/page.tsx`의 `WEATHER_THEME_CLASSES` 참조 (constants.ts에서 import)
| 날씨 | 클래스 | 분위기 |
|------|--------|--------|
| sunny | theme-sunny | Warm gradient, 밝고 활기찬 |
| rainy | theme-rainy | Gray-blue, 잔잔하고 감성적 |
| cloudy | theme-cloudy | Soft gray, 편안하고 차분한 |
| snowy | theme-snowy | White-blue, 포근하고 로맨틱 |

## 날씨 관련 변경 시 체크리스트
1. 캐시 키 변경 시 → constants.ts 버전업 (v3 → v4 등)
2. 새 날씨 조건 추가 시 → weather_scores JSONB, 테마 CSS, WeatherBanner 모두 수정
3. 빌드 확인
