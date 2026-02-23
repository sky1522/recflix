# Phase 46A: 추천 콜드스타트 해소 + 피드백 루프 + Error Boundary

**날짜**: 2026-02-23

## 1단계: preferred_genres → 추천 반영 (콜드스타트 해소)

### 변경 파일
- `backend/app/api/v1/recommendation_engine.py`

### 로직 상세
- `get_user_preferences()` 함수 수정
- **조건**: 총 상호작용 (찜 + 높은 평점) < 5건 AND `user.preferred_genres`가 존재
- **동작**:
  1. `preferred_genres` (Text 컬럼, JSON 문자열 `'["액션","SF"]'`) → `json.loads()`로 파싱
  2. Genre 테이블에서 `name_ko IN (파싱된 리스트)` 쿼리 → 한글→영어 매핑
  3. 각 영어 장르명을 `genre_counts`에 가중치 1로 추가 (`setdefault` + `+= 1`)
- **가산 공식**: 기존 `calculate_hybrid_scores()`의 personal_score 계산에서 `matching_genres * 0.3` (최대 0.9)으로 자동 반영
- **안전 처리**: `json.JSONDecodeError`, `TypeError` 예외 처리, NULL/빈 값 시 스킵
- **기존 로직 영향**: 상호작용 5건 이상이면 preferred_genres 무시 (기존 로직 그대로)

## 2단계: 피드백 루프 실시간화

### 변경 파일
- `frontend/stores/interactionStore.ts` — `bumpInteractionVersion()` 헬퍼 추가
- `frontend/app/page.tsx` — 캐시 키에 `interaction_version` 포함

### 무효화 지점
| 지점 | 함수 | 동작 |
|------|------|------|
| 찜 토글 성공 | `toggleFavorite()` | `bumpInteractionVersion()` 호출 |
| 평점 등록 성공 | `setRating()` | `bumpInteractionVersion()` 호출 |

### 구현 방식
- `localStorage`에 `interaction_version` (숫자) 저장
- 찜/평점 변경 성공 시 +1 증가
- `page.tsx`에서:
  - `interactionVersion` state 변수로 관리
  - `focus` 이벤트로 탭 복귀/뒤로가기 시 버전 재읽기
  - 캐시 키: `${weather}-${mood}-${userId}-${mbti}-iv${version}`
  - `useEffect` 의존성 배열에 `interactionVersion` 추가
- 기존 weather/mood 캐시 키 구조 유지하면서 확장

## 3단계: React Error Boundary

### 변경 파일
- `frontend/components/ErrorBoundary.tsx` (신규)
- `frontend/app/layout.tsx`

### 구조
- React 클래스 컴포넌트 (`'use client'`)
- `getDerivedStateFromError()` → `{ hasError: true }`
- `componentDidCatch()` → `console.error` (Sentry 연동 가능 지점)
- 폴백 UI:
  - "문제가 발생했습니다" 메시지 (h2, 흰색)
  - 안내 텍스트 (zinc-400)
  - "새로고침" 버튼 (`window.location.reload()`, primary-600)
  - "홈으로" 링크 (`/`, zinc-700)
  - 다크 테마 (bg-dark-200), 중앙 정렬
- `layout.tsx`에서 `<main>` 태그를 `<ErrorBoundary>`로 래핑

## 검증 결과
| 검증 항목 | 결과 |
|-----------|------|
| `ruff check app/` | All checks passed! |
| `python -c "from app.main import app"` | OK (RecFlix) |
| `npx tsc --noEmit` | 0 errors |
| `npm run build` | 13/13 pages |
| `npm run lint` | 0 warnings/errors |
