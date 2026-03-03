# 프론트엔드 패턴

## 핵심 파일
→ `frontend/stores/` (Zustand 4개: authStore, interactionStore, themeStore, useMoodStore)
→ `frontend/hooks/` (useWeather, useInfiniteScroll, useDebounce, useImpressionTracker)
→ `frontend/lib/api.ts` (24개 API 함수, fetchAPI 래퍼)
→ `frontend/lib/constants.ts` (캐시 키, 매직넘버)
→ `frontend/lib/eventTracker.ts` (사용자 행동 이벤트 배치 전송, Beacon API)

## 데이터 흐름
→ `frontend/app/page.tsx` 참조
```
사용자 방문
  → useWeather(Geolocation)
  → buildUserContext (시간대/계절/기온)
  → getHomeRecommendations API
  → 큐레이션 문구 매칭
  → MovieRow 렌더링
```

## Zustand 패턴

### authStore
→ `frontend/stores/authStore.ts` 참조
- 로그인/로그아웃, JWT 토큰 관리
- persist middleware로 localStorage 영속화

### interactionStore
→ `frontend/stores/interactionStore.ts` 참조
- 찜/평점 상태 캐싱
- Optimistic UI: 요청 전 UI 즉시 반영, 실패 시 롤백

### themeStore
→ `frontend/stores/themeStore.ts` 참조
- `theme: "dark" | "light"`, `toggleTheme()`, `setTheme()`
- persist middleware로 localStorage 영속화 ("theme-storage")
- `onRehydrateStorage` 콜백으로 `html.light` 클래스 적용

### useMoodStore
→ `frontend/stores/useMoodStore.ts` 참조
- `mood: MoodType | null`, `setMood()`
- 기분 선택 상태 관리 (8종: relaxed, tense, excited, emotional, imaginative, light, gloomy, stifled)

## API 패턴
→ `frontend/lib/api.ts` 참조
- `fetchAPI<T>()`: 공통 래퍼 (base URL, 인증 헤더, 에러 처리)
- 각 API 함수는 fetchAPI를 감싸서 타입 안전하게 호출

## 컴포넌트 규칙
- 모듈 레벨 mutable 변수 금지 → `useRef` / `useState` 사용
- 상수는 `constants.ts`에 관리
- 캐시 키 변경 시 버전업 (v3 → v4)
- 서버/클라이언트 하이드레이션 불일치 방지: 동적 값은 `useEffect`에서만

## 에러 처리
→ `frontend/app/error.tsx` (전역), `frontend/app/not-found.tsx` (404), `frontend/app/movies/[id]/error.tsx`
→ ErrorBoundary: Phase 46에서 개선 (graceful degradation)

## 트레일러 (Phase 47)
→ `TrailerModal` 컴포넌트 — YouTube iframe 임베드
→ `MovieHero.tsx`, `MovieSidebar.tsx` — 트레일러 재생 버튼
→ `trailer_key` 필드: YouTube video ID (null이면 버튼 숨김)

## 모바일 UI/UX 패턴 (Phase 51)

### 터치 영역 (Apple HIG 44px 기준)
- 버튼/링크: `min-w-[44px] min-h-[44px]` + `flex items-center justify-center`
- 데스크톱 복원: `sm:min-w-0 sm:min-h-0` (데스크톱에선 원래 크기)
- 패딩 확대: 모바일 `p-2.5` → 데스크톱 `sm:p-1.5`

### hover-only → 모바일 대응
- 패턴: `opacity-100 sm:opacity-0 sm:group-hover:opacity-100`
- 적용: 트레일러 표시기, 찜 해제 버튼, 평점 삭제 버튼

### 반응형 위치 (thumb zone)
- 모바일: `fixed bottom-4 left-4 right-4` (하단 고정, 엄지 닿는 영역)
- 데스크톱: `sm:bottom-auto sm:left-auto sm:top-[72px] sm:right-4`
- 너비: `w-full sm:w-80`

### 가로 overflow 방지
- `flex flex-wrap gap-2 sm:gap-3` (줄바꿈 허용)
- `space-x-3` 대신 `gap-2` 사용 (wrap과 호환)

### 배경 가시성
- 모바일: `bg-black/60` (더 진하게, 야외 가독성)
- 데스크톱: `sm:bg-black/40`

## 이벤트 트래킹 패턴 (Phase 52)

### 추천 컨텍스트 전파
- MovieCard/HybridMovieCard: `href={/movies/${id}?from=${section}&pos=${index}}`
- 영화 상세 페이지: `useSearchParams()`로 `from`, `pos` 추출
- 이벤트 메타데이터에 `source_section`, `source_position` 포함

### 이벤트 삽입 포인트
| 컴포넌트 | 이벤트 | 메타데이터 |
|----------|--------|-----------|
| MovieCard | movie_click | section, source |
| HybridMovieCard | movie_click | section, source, from/pos params |
| MovieModal | favorite_add/remove, rating | source_section |
| FeaturedBanner | movie_click (상세보기/트레일러) | source: featured_banner, section: featured |
| movies/[id]/page | movie_detail_view, movie_detail_leave | source_section, source_position, duration_ms |

### trackEvent 패턴
```typescript
import { trackEvent } from "@/lib/eventTracker";

trackEvent({
  event_type: "movie_click",
  movie_id: movie.id,
  metadata: { source: "component_name", section: sectionKey },
});
```

## 테마 시스템 (Phase 54)

### CSS 변수 기반 시맨틱 토큰
→ `frontend/app/globals.css`, `frontend/tailwind.config.ts` 참조
- `:root`에 다크 모드 기본값, `html.light`에 라이트 모드 오버라이드
- 6개 시맨틱 토큰: `--surface-main`, `--surface-card`, `--surface-deep`, `--fg`, `--overlay`, `--divider`
- Tailwind 확장: `bg-surface`, `text-fg`, `bg-overlay/10`, `border-divider/10` 등
- `bg-dark-*` → `bg-surface-*`, `text-white` (중립 배경) → `text-fg`, `bg-white/*` → `bg-overlay/*`
- 유지: `text-white` on 컬러 배경 (`bg-primary-600`), `bg-black/*` 백드롭, 의도적 `bg-white`

### FOUC 방지
→ `frontend/app/layout.tsx` 참조
- `<html>` 태그에 `suppressHydrationWarning`
- 인라인 `<script>` → localStorage 즉시 읽어 `html.light` 클래스 적용 (paint 전)
- `ThemeProvider` 래퍼 → `useEffect`에서 theme store 동기화

## 헤더 드롭다운 패턴 (Phase 54)

### 4종 드롭다운 (weather/mood/mbti/profile)
→ `frontend/components/layout/Header.tsx` 참조
- `DropdownType = "weather" | "mood" | "mbti" | "profile" | null`
- `openDropdown` 단일 state로 상호 배타적 관리
- 각 드롭다운: `useRef` → `refs[]` 배열 → `mousedown` 외부 클릭 감지
- 공유 `dropdownAnimation` 객체 (scale 0.95 → 1, opacity)
- `AnimatePresence` + `motion.div` 패턴
- ESC 키 닫기: `keydown` 이벤트 리스너

### 게스트 MBTI 패턴
- `useGuestMBTI()` 훅: `localStorage("guest_mbti")` 읽기/쓰기
- `useEffect`에서 localStorage 읽기 (SSR 안전)
- `currentMBTI = isAuthenticated ? user?.mbti : guestMBTI`
- 인증 시 `updateMBTI()` API, 비인증 시 localStorage 저장

## 새 페이지 추가 시 체크리스트
1. `app/경로/page.tsx` 생성
2. 필요 시 `layout.tsx` (OG 메타태그)
3. Header.tsx 네비게이션 링크 추가
4. 모바일 메뉴 링크 추가 (Header.tsx 내 모바일 패널)
5. `types/index.ts` 타입 추가
6. `lib/api.ts` API 함수 추가
7. 빌드 확인
