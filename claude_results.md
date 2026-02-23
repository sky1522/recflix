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
