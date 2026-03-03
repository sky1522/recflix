# 영화 상세 페이지 → 검색 연결: country/keyword/mbti/weather 필터 구현

## 목적
영화 상세 페이지(MovieSidebar)에서 제작국가, 키워드, MBTI, 날씨를 클릭하면 `/movies` 검색 페이지로 이동하여 해당 조건으로 필터/정렬된 영화 목록을 보여주는 기능 구현.

## 구현 범위

### Part 1: 백엔드 — `backend/app/api/v1/movies.py`

기존 `GET /api/v1/movies` 엔드포인트에 4개 쿼리 파라미터 추가:

**1. `country` (제작 국가)**
- 파라미터: `country: Optional[str] = Query(None)`
- 쿼리: `movie_countries` M:M JOIN 또는 `production_countries_ko LIKE '%{country}%'`
- 기존 `genres` 필터의 M:M JOIN 패턴 참고해서 동일하게 구현
- 예: `GET /api/v1/movies?country=한국`

**2. `keyword` (키워드)**
- 파라미터: `keyword: Optional[str] = Query(None)`
- 쿼리: `movie_keywords` M:M JOIN → `Keyword.name == keyword`
- 기존 `genres` 필터와 동일 패턴
- 예: `GET /api/v1/movies?keyword=도시실종`

**3. `mbti` (MBTI 유형별 정렬)**
- 파라미터: `mbti: Optional[str] = Query(None, regex="^(E|I)(S|N)(T|F)(J|P)$")`
- 쿼리: `ORDER BY (movies.mbti_scores->>:mbti)::float DESC`
- mbti 파라미터가 있으면 자동으로 해당 MBTI 점수 내림차순 정렬
- 추천 엔진(`recommendation_engine.py`)에서 이미 사용 중인 JSONB 쿼리 패턴 참고
- 예: `GET /api/v1/movies?mbti=ENTJ`

**4. `weather` (날씨별 정렬)**
- 파라미터: `weather: Optional[str] = Query(None, regex="^(sunny|rainy|cloudy|snowy)$")`
- 쿼리: `ORDER BY (movies.weather_scores->>:weather)::float DESC`
- mbti와 동일 패턴
- 예: `GET /api/v1/movies?weather=rainy`

**주의사항:**
- mbti/weather 파라미터가 있으면 sort_by 파라미터를 무시하고 해당 점수로 정렬 (또는 sort_by에 `mbti_score`, `weather_score` 옵션 추가)
- 기존 필터(genre, age_rating, person 등)와 조합 가능해야 함
- 품질 필터(weighted_score >= 6.0)는 유지
- SQL Injection 방지: JSONB 키는 화이트리스트 검증 (MBTI 16유형, 날씨 4종만 허용)

---

### Part 2: 프론트엔드 — API 클라이언트

**`frontend/lib/api.ts`** (또는 API 호출 파일):
- `getMovies()` 함수의 params에 `country`, `keyword`, `mbti`, `weather` 추가
- 값이 있을 때만 쿼리스트링에 포함

---

### Part 3: 프론트엔드 — 검색 페이지

**`frontend/app/movies/page.tsx`**:
- `searchParams`에서 `country`, `keyword`, `mbti`, `weather` 읽기
- API 호출 시 해당 파라미터 전달
- 활성 필터 표시 (선택적): 페이지 상단에 "🌍 한국" 또는 "MBTI: ENTJ 추천순" 같은 필터 뱃지 표시
- 필터 제거 버튼 (X) → 해당 파라미터 제거하고 재검색

---

### Part 4: 프론트엔드 — 상세 페이지 링크화

**`frontend/app/movies/[id]/page.tsx` (MovieSidebar 영역)**:

**제작 국가** (현재 40-45줄):
- `<p>` 텍스트 → 각 국가를 `<Link href="/movies?country=브라질">브라질</Link>`로 변환
- 쉼표 구분 텍스트를 split → 개별 링크로

**키워드** (현재 48-62줄):
- `<span>` 태그 → `<Link href="/movies?keyword=도시실종">도시실종</Link>`로 변환
- 기존 태그 스타일 유지하면서 클릭 가능하게

**MBTI 점수** (현재 76-96줄):
- 각 MBTI 유형명을 클릭하면 → `<Link href="/movies?mbti=ENTJ">ENTJ</Link>`
- 퍼센트와 바 그래프는 그대로, 유형명만 링크화
- hover 시 "ENTJ 추천 영화 보기" 같은 tooltip 또는 커서 포인터

**날씨 점수** (현재 99-120줄):
- 각 날씨를 클릭하면 → `<Link href="/movies?weather=cloudy">☁️ 흐린 날</Link>`
- 날씨 한글 라벨 → API 영문 키 매핑: 흐린 날→cloudy, 비 오는 날→rainy, 맑은 날→sunny, 눈 오는 날→snowy

**스타일 가이드:**
- 링크는 기존 텍스트 색상 유지, hover 시 underline 또는 색상 변화
- 커서를 pointer로 변경
- 태그 형태의 요소(키워드)는 hover 시 배경색 변화로 클릭 가능함을 표시
- 지나치게 링크처럼 보이지 않되, 인터랙티브함이 느껴지도록

---

## 완료 조건

- [ ] `GET /api/v1/movies?country=한국` → 한국 제작 영화 목록 반환
- [ ] `GET /api/v1/movies?keyword=복수` → 해당 키워드 영화 목록 반환
- [ ] `GET /api/v1/movies?mbti=ENTJ` → ENTJ 점수 높은 순 정렬
- [ ] `GET /api/v1/movies?weather=rainy` → 비 오는 날 점수 높은 순 정렬
- [ ] 기존 필터(genre, age_rating)와 조합 가능
- [ ] 상세 페이지에서 국가/키워드/MBTI/날씨 클릭 → 검색 페이지 이동
- [ ] 검색 페이지에서 활성 필터가 표시됨
- [ ] 모바일에서도 정상 동작

---

## 결과 저장

작업 완료 후 결과를 `claude_results.md`에 저장해줘. 아래 형식으로:

```markdown
# 영화 검색 필터 구현 결과

> 작업일: YYYY-MM-DD

## 변경 파일 목록
| 파일 | 변경 내용 |
|------|-----------|
| ... | ... |

## 백엔드 변경 사항
- 추가된 파라미터, 쿼리 방식, 주의점

## 프론트엔드 변경 사항
- API 클라이언트, 검색 페이지, 상세 페이지 각각 정리

## 테스트 결과
- 각 필터별 동작 확인 결과

## 완료 조건 체크
- [x] 또는 [ ] 로 표시

## 미해결 이슈 (있다면)
- ...
```