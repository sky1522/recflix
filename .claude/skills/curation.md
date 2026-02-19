# 큐레이션 시스템

## 핵심 파일
→ `frontend/lib/curationMessages.ts` (258개 문구)
→ `frontend/lib/contextCuration.ts` (컨텍스트 감지)
→ `frontend/app/page.tsx`의 `getRowSubtitle()`, `getHybridSubtitle()`

## 문구 구조 (258개)
→ curationMessages.ts 참조
- WEATHER: 4종 x 6 = 24 (sunny, rainy, cloudy, snowy)
- MOOD: 8종 x 6 = 48 (relaxed, tense, excited, emotional, imaginative, light, gloomy, stifled)
- MBTI: 16종 x 6 = 96
- FIXED: 3종 x 6 = 18 (popular, top_rated, for_you)
- TIME: 4종 x 6 = 24 (morning, afternoon, evening, night)
- SEASON: 4종 x 6 = 24 (spring, summer, autumn, winter)
- TEMP: 6종 x 4 = 24 (freezing, cold, cool, mild, warm, hot)

## 컨텍스트 감지
→ contextCuration.ts 참조
- 시간대: morning/afternoon/evening/night (`new Date().getHours()`)
- 계절: spring/summer/autumn/winter (`new Date().getMonth()`)
- 기온: freezing/cold/cool/mild/warm/hot (`weather.temperature`)

## 적용 위치
- 맞춤 추천 (Hybrid) → TIME_SUBTITLES
- 날씨 추천 → 짝수 idx = SEASON_SUBTITLES, 홀수 idx = TEMP_SUBTITLES

## 문구 추가 시 체크리스트
1. curationMessages.ts에 문구 추가 (기존 구조 유지)
2. 시간/계절/기온 종속 표현 사용 금지 (중립적 표현만)
3. 하이드레이션 안전: useEffect에서만 컨텍스트 설정
4. 빌드 확인
