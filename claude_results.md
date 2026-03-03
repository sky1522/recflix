# 헤더 MBTI 비로그인 노출 + 프로필 드롭다운 + 설정 페이지 + 다크/라이트 모드

> 작업일: 2026-03-03

## 변경 파일 (43개)

### 신규 (3개)
- `frontend/stores/themeStore.ts` — Zustand 테마 스토어 (dark/light)
- `frontend/components/layout/ThemeProvider.tsx` — 테마 클래스 적용 래퍼
- `frontend/app/settings/page.tsx` — 설정 페이지 (닉네임, MBTI, 장르, 테마, 계정)

### 인프라 (3개)
- `frontend/tailwind.config.ts` — surface/fg/overlay/divider 시맨틱 컬러 토큰 추가
- `frontend/app/globals.css` — CSS 변수 (다크/라이트), 스크롤바/날씨/그라디언트/shimmer 라이트 대응
- `frontend/app/layout.tsx` — ThemeProvider, FOUC 방지 인라인 스크립트, bg-surface

### 기능 (3개)
- `frontend/components/layout/Header.tsx` — MBTI 비로그인 배지, 프로필 드롭다운, 시맨틱 토큰
- `frontend/components/layout/MBTIModal.tsx` — 비로그인 localStorage 저장, 시맨틱 토큰
- `frontend/components/layout/HeaderMobileDrawer.tsx` — 설정 링크 추가, 시맨틱 토큰

### 테마 적용 (34개)
- 레이아웃: MobileNav, ErrorBoundary
- 영화: MovieCard, MovieModal, MovieRow, HybridMovieRow, HybridMovieCard, FeaturedBanner, MovieGrid, MovieFilters, TrailerModal
- 검색: SearchAutocomplete, SearchResults
- 페이지: page.tsx(홈), movies/page, movies/[id]/page, login, signup, favorites, ratings, onboarding, profile
- 영화 상세: MovieHero, MovieSidebar, MovieTrailer, SimilarMovies, MovieDetailSkeleton, error, loading
- 기타: Skeleton, auth/kakao/callback, auth/google/callback, loading(루트), movies/loading

## 핵심 변경사항

1. **CSS 변수 기반 테마**: `--surface-main`, `--fg`, `--overlay`, `--divider` 등 6개 시맨틱 토큰
2. **FOUC 방지**: `<script>` 인라인으로 localStorage 즉시 읽어 `html.light` 클래스 적용
3. **MBTI 비로그인**: `localStorage("guest_mbti")` 저장, 헤더에 항상 배지 표시
4. **프로필 드롭다운**: 아바타 클릭 → 설정/찜/평점/로그아웃 메뉴
5. **설정 페이지**: 닉네임 인라인 편집, MBTI, 선호 장르(10종), 테마 토글, 계정 삭제
6. **다크/라이트 모드**: 모든 컴포넌트에 시맨틱 토큰 적용 (bg-dark-* 0건 잔존)

## 검증 결과
- `npx next build` ✅ 성공 (14 페이지, /settings 포함)
- `bg-dark-*` grep 결과: 0건 (완전 교체)
- ESLint/TypeScript: 빌드 시 에러 없음
