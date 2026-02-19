# 프론트엔드 패턴

## 핵심 파일
→ `frontend/stores/` (Zustand 2개: authStore, interactionStore)
→ `frontend/hooks/` (useWeather, useInfiniteScroll, useDebounce)
→ `frontend/lib/api.ts` (24개 API 함수, fetchAPI 래퍼)
→ `frontend/lib/constants.ts` (캐시 키, 매직넘버)

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

## 새 페이지 추가 시 체크리스트
1. `app/경로/page.tsx` 생성
2. 필요 시 `layout.tsx` (OG 메타태그)
3. Header.tsx 네비게이션 링크 추가
4. 모바일 메뉴 링크 추가 (Header.tsx 내 모바일 패널)
5. `types/index.ts` 타입 추가
6. `lib/api.ts` API 함수 추가
7. 빌드 확인
