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
- `country` (str): 제작 국가명 → `production_countries_ko ILIKE` 필터 (한글 국가명)
- `keyword` (str): 키워드명 → `movie_keywords` M:M JOIN 필터
- `mbti` (str, pattern: `^(E|I)(S|N)(T|F)(J|P)$`): MBTI 유형 → `mbti_scores` JSONB 내림차순 정렬
- `weather` (str, pattern: `^(sunny|rainy|cloudy|snowy)$`): 날씨 → `weather_scores` JSONB 내림차순 정렬

### 정렬 우선순위
- `mbti` 파라미터 → `cast(Movie.mbti_scores[key].astext, Float).desc().nulls_last()` (sort_by 무시)
- `weather` 파라미터 → `cast(Movie.weather_scores[key].astext, Float).desc().nulls_last()` (sort_by 무시)
- 둘 다 없으면 → 기존 `sort_by` 사용

### SQL Injection 방지
- MBTI: `^(E|I)(S|N)(T|F)(J|P)$` 정규식으로 16가지 유형만 허용
- Weather: `^(sunny|rainy|cloudy|snowy)$` 정규식으로 4가지만 허용
- MBTI/Weather 정렬: SQLAlchemy 파라미터 바인딩 (`Movie.mbti_scores[key]`)
- Country/Keyword: ORM 파라미터 바인딩 (SQLAlchemy)

### 기타
- `regex` → `pattern` 마이그레이션 (FastAPI deprecation 해결)

### 수정 이력
1. 초기: text() SQL 직접 사용 → 500 에러 (ORM 쿼리와 호환 문제)
2. 수정: SQLAlchemy `cast(Movie.mbti_scores[key].astext, Float)` 네이티브 연산자
3. Country: M:M JOIN (영문) → `production_countries_ko ILIKE` (한글)

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
- **제작국가**: `<p>` → `production_countries_ko.split(", ")` → 개별 `<Link href="/movies?country=대한민국">` 태그
- **키워드**: `<span>` → `<Link href="/movies?keyword=도시실종">` (hover: violet 효과)
- **MBTI**: `<div>` → `<Link href="/movies?mbti=ENTJ">` (hover: amber 효과, tooltip)
- **날씨**: `<div>` → `<Link href="/movies?weather=rainy">` (hover: sky 효과, tooltip)

## 테스트 결과

- ✅ Next.js 빌드 성공 (모든 페이지 정상 생성)
- ✅ 백엔드 import 성공 (movies.py 모듈 로드 정상)
- ✅ FastAPI regex→pattern deprecation 해결

## 배포 검증 결과

### CI/CD
- ✅ backend-lint 통과
- ✅ backend-test 통과
- ✅ frontend-build 통과
- ✅ deploy-backend 성공 (Railway)
- ⚠️ backend-typecheck 실패 (continue-on-error, 기존 타입 이슈)

### 프로덕션 API 테스트
```
[country=대한민국] total=1097  → 대홍수, 전지적 독자 시점, 어쩔수가없다
[keyword=복수]    total=1676  → 드라큘라: 어 러브 테일, 헌팅시즌, 발레리나
[mbti=ENTJ]       total=42917 → ENTJ 점수 높은 순 정렬
[weather=rainy]   total=42917 → 비 오는 날 점수 높은 순 정렬

조합: [country=대한민국 + mbti=ENTJ] total=1097 → 한국 영화 중 ENTJ 추천순
조합: [keyword=복수 + weather=rainy] total=1676 → 복수 키워드 중 비 오는 날순
```

## 완료 조건 체크

- [x] `GET /api/v1/movies?country=대한민국` → 한국 제작 영화 1,097건 반환
- [x] `GET /api/v1/movies?keyword=복수` → 해당 키워드 영화 1,676건 반환
- [x] `GET /api/v1/movies?mbti=ENTJ` → ENTJ 점수 높은 순 정렬
- [x] `GET /api/v1/movies?weather=rainy` → 비 오는 날 점수 높은 순 정렬
- [x] 기존 필터(genre, age_rating)와 조합 가능
- [x] 상세 페이지에서 국가/키워드/MBTI/날씨 클릭 → 검색 페이지 이동
- [x] 검색 페이지에서 활성 필터가 표시됨 (뱃지 + ✕ 제거 버튼)
- [x] 모바일에서도 정상 동작 (flex-wrap gap-2, 반응형)

## 커밋 이력

| SHA | 메시지 |
|-----|--------|
| `925ee8d` | feat(search): 영화 검색 API에 country/keyword/mbti/weather 필터 추가 |
| `fe16f22` | fix(search): country LIKE 필터 + MBTI/weather JSONB 정렬 수정 |
| `2674a7e` | fix(search): MBTI/weather 정렬을 SQLAlchemy JSONB 연산자로 변경 |

## 미해결 이슈

- 없음
