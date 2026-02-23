# Phase 44: SEO 메타데이터 + Loading Skeleton + 접근성 + 캐시 키 (2026-02-23)

## Step 1: 라우트별 SEO 메타데이터 레이아웃 (6개)

| 라우트 | 파일 | title |
|--------|------|-------|
| `/login` | `app/login/layout.tsx` | 로그인 \| RecFlix |
| `/signup` | `app/signup/layout.tsx` | 회원가입 \| RecFlix |
| `/profile` | `app/profile/layout.tsx` | 내 프로필 \| RecFlix |
| `/favorites` | `app/favorites/layout.tsx` | 찜한 영화 \| RecFlix |
| `/ratings` | `app/ratings/layout.tsx` | 내 평점 \| RecFlix |
| `/onboarding` | `app/onboarding/layout.tsx` | 취향 설정 \| RecFlix |

각 layout.tsx에 `metadata` export (title, description, openGraph, twitter) 포함.

## Step 2: Loading Skeleton (3개)

| 파일 | 설명 |
|------|------|
| `app/loading.tsx` | 홈: 배너 + 3개 Movie Row × 6카드 |
| `app/movies/loading.tsx` | 검색: 타이틀 + 검색바 + 필터 + 4×6 그리드 |
| `app/movies/[id]/loading.tsx` | 상세: 히어로 + 포스터 + 정보 |

## Step 3: 접근성 (Accessibility)

### 3-1: Viewport 설정
- `maximumScale`: 1 → 5
- `userScalable`: false → true

### 3-2: MovieModal
- `role="dialog"` `aria-modal="true"` `aria-labelledby="modal-movie-title"` 추가
- `tabIndex={-1}` + `ref={dialogRef}` + ESC 키 핸들러
- 닫기 버튼 `aria-label="닫기"` 추가
- h2에 `id="modal-movie-title"` 추가

### 3-3: HeaderMobileDrawer
- `role="dialog"` `aria-modal="true"` `aria-label="메뉴"` 추가
- ESC 키 핸들러 (useEffect + keydown)

### 3-4: SearchAutocomplete (Combobox ARIA)
- input: `role="combobox"` `aria-expanded` `aria-controls` `aria-activedescendant` `aria-autocomplete="list"`
- 결과 컨테이너: `id="search-results-listbox"` `role="listbox"`
- 각 결과 항목 (SearchResults.tsx): `role="option"` `aria-selected` `id="search-item-{n}"`
- 검색어 지우기 버튼: `aria-label="검색어 지우기"`

### 3-5: Icon 버튼 aria-label
- 로그인 닫기 버튼: `aria-label="닫기"`
- 비밀번호 토글: `aria-label="비밀번호 보기"` / `"비밀번호 숨기기"`

### 3-6: MovieFilters select aria-label
- 장르: `aria-label="장르 선택"`
- 연령등급: `aria-label="연령 등급 선택"`
- 정렬: `aria-label="정렬 방식"`

## Step 4: 홈 캐시 키 개선

```
Before: `${weather.condition}-${mood}-${isAuthenticated}`
After:  `${weather.condition}-${mood}-${user?.id || 'anon'}-${user?.mbti || 'none'}`
```

동일 인증 상태여도 사용자/MBTI가 다르면 캐시 무효화.
useEffect 의존성 배열에 `user?.id`, `user?.mbti` 추가.

## 변경 파일 목록 (15개)

### 신규 (9개)
- `app/login/layout.tsx`
- `app/signup/layout.tsx`
- `app/profile/layout.tsx`
- `app/favorites/layout.tsx`
- `app/ratings/layout.tsx`
- `app/onboarding/layout.tsx`
- `app/loading.tsx`
- `app/movies/loading.tsx`
- `app/movies/[id]/loading.tsx`

### 수정 (6개)
- `app/layout.tsx` — viewport 접근성
- `app/page.tsx` — 캐시 키 + deps
- `app/login/page.tsx` — aria-label
- `components/movie/MovieModal.tsx` — dialog ARIA
- `components/movie/MovieFilters.tsx` — select aria-label
- `components/layout/HeaderMobileDrawer.tsx` — dialog ARIA + ESC
- `components/search/SearchAutocomplete.tsx` — combobox ARIA
- `components/search/SearchResults.tsx` — option ARIA

## 검증 결과
- `tsc --noEmit`: 0 errors
- `npm run build`: 성공 (13/13 pages)
- `npm run lint`: 0 warnings/errors

---

# pg_trgm 검색 인덱스 프로덕션 적용 (2026-02-23)

Railway 프로덕션 DB에 pg_trgm GIN 인덱스 3개 적용 완료.

- `pg_trgm` 확장: 활성화 확인
- `idx_movies_title_ko_trgm`: title_ko ILIKE 검색 가속
- `idx_movies_title_trgm`: title ILIKE 검색 가속
- `idx_movies_cast_ko_trgm`: cast_ko ILIKE 검색 가속

모두 `CREATE INDEX CONCURRENTLY`로 무중단 생성.

---

# Phase 43B: Frontend 성능 — 파일 분할 + 애니메이션 경량화 결과

## 날짜
2026-02-23

## 분할 전/후 LOC 비교

| 파일 | Before | After | 감소 |
|------|--------|-------|------|
| `app/movies/page.tsx` | 531 | 271 | -260 (-49%) |
| `components/search/SearchAutocomplete.tsx` | 534 | 321 | -213 (-40%) |
| `components/layout/Header.tsx` | 373 | 230 | -143 (-38%) |

## 새로 생성된 파일 목록

| # | 파일 | 역할 | LOC |
|---|------|------|-----|
| 1 | `components/movie/MovieFilters.tsx` | 장르/정렬/연령등급 필터 UI | 108 |
| 2 | `components/movie/MovieGrid.tsx` | 영화 그리드 + 시맨틱 결과 + 페이지네이션 + 무한스크롤 | 289 |
| 3 | `components/search/SearchResults.tsx` | 자동완성 검색 결과 드롭다운 렌더링 | 255 |
| 4 | `components/layout/HeaderMobileDrawer.tsx` | 모바일 슬라이드 메뉴 패널 | 167 |

## 1단계: movies/page.tsx 분할

### 추출된 컴포넌트
- **MovieFilters**: 장르/연령등급/정렬 select + 무한스크롤 토글 + 필터 초기화 버튼
- **MovieGrid**: 검색 결과 그리드 렌더링 (시맨틱 검색 섹션 포함), 빈 결과 + 추천, 무한스크롤/페이지네이션

### page.tsx에 남은 역할
- URL 파라미터 해석 (searchParams)
- 데이터 fetch (getMovies, getGenres, semanticSearch)
- 상태 관리 (movies, genres, loading 등)
- 레이아웃 조합

## 2단계: SearchAutocomplete.tsx 분할

### 추출된 컴포넌트
- **SearchResults**: 시맨틱 AI 결과, 키워드 영화, 인물, 빈 결과, "전체 검색" 버튼 렌더링

### SearchAutocomplete에 남은 역할
- 입력 UI + debounce
- Promise.allSettled 병렬 fetch + AbortController
- 키보드 네비게이션 (ArrowUp/Down, Enter, Escape)
- flatItems 계산 (useMemo)

## 3단계: Header.tsx 경량화

### 변경 사항
- **5초 interval polling 제거**: `setInterval(loadWeather, 5000)` → `storage` 이벤트 리스너만 유지
- **HeaderMobileDrawer 추출**: 모바일 메뉴 패널 (날씨, 네비게이션, 사용자 섹션) 별도 컴포넌트
- **nav 상수 모듈 레벨**: `NAV_ITEMS`, `AUTH_NAV_ITEMS` → 렌더링마다 재생성 방지

### Weather polling 변경
```
Before: loadWeather() + storage event + setInterval(5000ms)
After:  loadWeather() + storage event only (no polling)
```
날씨 데이터는 useWeather 훅이 localStorage에 쓸 때 storage 이벤트로 동기화됩니다.

## 4단계: 카드 애니메이션 경량화

### MovieCard.tsx
```
Before: initial={{ opacity: 0, y: 20 }} transition={{ delay: index * 0.05 }}
After:  initial={{ opacity: 0 }} transition={{ duration: 0.3 }}
```

### HybridMovieCard.tsx
```
Before: initial={{ opacity: 0, y: 20 }} transition={{ delay: index * 0.05 }}
After:  initial={{ opacity: 0 }} transition={{ duration: 0.3 }}
```

- `y: 20` 이동 애니메이션 제거 → 단순 페이드인
- `delay: index * 0.05` 순차 지연 제거 → 모든 카드 동시 페이드인
- hover 효과 (scale, shadow) 유지
- 무한스크롤 추가분도 동일한 짧은 페이드만 적용

## 검증 결과
- `tsc --noEmit`: 0 errors
- `npm run build`: 성공 (13/13 pages)
- `npm run lint`: 0 ESLint errors
- 500줄 초과 파일: 0개 (최대 415줄 curationMessages.ts, 데이터 파일)
