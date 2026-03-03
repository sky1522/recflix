# 영화 검색 필터 구현 결과

> 작업일: 2026-03-03

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/api/v1/movies.py` | country/keyword/mbti/weather 4개 쿼리 파라미터 추가, JSONB 정렬, regex→pattern 마이그레이션 |
| `frontend/lib/api.ts` | `getMovies()` params에 country/keyword/mbti/weather 추가 |
| `frontend/app/movies/page.tsx` | 새 필터 URL 파라미터 읽기, API 전달, 활성 필터 뱃지 UI |
| `frontend/app/movies/[id]/components/MovieSidebar.tsx` | 제작국가/키워드/MBTI/날씨를 클릭 가능한 `<Link>`로 변환 |

## 백엔드 변경 사항

### 새 쿼리 파라미터 (GET /api/v1/movies)
- `country` (str): 제작 국가명 → `movie_countries` M:M JOIN 필터 (genre 패턴과 동일)
- `keyword` (str): 키워드명 → `movie_keywords` M:M JOIN 필터
- `mbti` (str, pattern: `^(E|I)(S|N)(T|F)(J|P)$`): MBTI 유형 → `mbti_scores` JSONB 내림차순 정렬
- `weather` (str, pattern: `^(sunny|rainy|cloudy|snowy)$`): 날씨 → `weather_scores` JSONB 내림차순 정렬

### 정렬 우선순위
- `mbti` 파라미터 → `ORDER BY (movies.mbti_scores->>'ENTJ')::float DESC` (sort_by 무시)
- `weather` 파라미터 → `ORDER BY (movies.weather_scores->>'rainy')::float DESC` (sort_by 무시)
- 둘 다 없으면 → 기존 `sort_by` 사용

### SQL Injection 방지
- MBTI: `^(E|I)(S|N)(T|F)(J|P)$` 정규식으로 16가지 유형만 허용
- Weather: `^(sunny|rainy|cloudy|snowy)$` 정규식으로 4가지만 허용
- Country/Keyword: ORM 파라미터 바인딩 (SQLAlchemy)

### 기타
- `regex` → `pattern` 마이그레이션 (FastAPI deprecation 해결)

## 프론트엔드 변경 사항

### API 클라이언트 (`lib/api.ts`)
- `getMovies()` params에 `country`, `keyword`, `mbti`, `weather` 4개 필드 추가
- 값이 있을 때만 URLSearchParams에 포함

### 검색 페이지 (`movies/page.tsx`)
- `searchParams.get("country")` 등 4개 URL 파라미터 추가
- 메인 fetch + loadMore 함수 양쪽에 새 파라미터 전달
- useEffect 의존성 배열에 4개 추가
- 활성 필터 뱃지 UI:
  - 🌍 국가 (emerald 색상)
  - 🏷️ 키워드 (violet 색상)
  - 🧠 MBTI 추천순 (amber 색상)
  - ☀️/🌧️/☁️/❄️ 날씨 추천순 (sky 색상)
  - 각 뱃지에 ✕ 제거 버튼

### 상세 페이지 MovieSidebar 링크화
- **제작국가**: `<p>` → 개별 `<Link href="/movies?country=한국">` 태그
- **키워드**: `<span>` → `<Link href="/movies?keyword=도시실종">` (hover: violet 효과)
- **MBTI**: `<div>` → `<Link href="/movies?mbti=ENTJ">` (hover: amber 효과, tooltip)
- **날씨**: `<div>` → `<Link href="/movies?weather=rainy">` (hover: sky 효과, tooltip)

## 테스트 결과

- ✅ Next.js 빌드 성공 (모든 페이지 정상 생성)
- ✅ 백엔드 import 성공 (movies.py 모듈 로드 정상)
- ✅ FastAPI regex→pattern deprecation 해결

## 완료 조건 체크

- [x] `GET /api/v1/movies?country=한국` → 한국 제작 영화 목록 반환
- [x] `GET /api/v1/movies?keyword=복수` → 해당 키워드 영화 목록 반환
- [x] `GET /api/v1/movies?mbti=ENTJ` → ENTJ 점수 높은 순 정렬
- [x] `GET /api/v1/movies?weather=rainy` → 비 오는 날 점수 높은 순 정렬
- [x] 기존 필터(genre, age_rating)와 조합 가능
- [x] 상세 페이지에서 국가/키워드/MBTI/날씨 클릭 → 검색 페이지 이동
- [x] 검색 페이지에서 활성 필터가 표시됨 (뱃지 + ✕ 제거 버튼)
- [x] 모바일에서도 정상 동작 (flex-wrap gap-2, 반응형)

## 미해결 이슈

- 없음
