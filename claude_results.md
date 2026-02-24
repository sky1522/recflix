# 모바일 UI/UX 점검 + 유도섹션 터치 영역 개선

**날짜**: 2026-02-24

## 발견된 이슈 목록

| 파일 | 라인 | 문제 |
|------|------|------|
| `FeaturedBanner.tsx` | 290 | 우측 고정 사이드바 `w-80`(320px) — 360px 뷰포트에서 화면 대부분 차지 |
| `FeaturedBanner.tsx` | 235 | 배너 버튼 4개 `flex space-x-3` — 360px에서 가로 overflow |
| `FeaturedBanner.tsx` | 353-365 | 날씨 토글 버튼 `p-1.5` — ~28px, 44px 미달 |
| `FeaturedBanner.tsx` | 394-408 | 기분 버튼 `px-1.5 py-1` — ~24px, 44px 미달 |
| `Header.tsx` | 142 | 모바일 검색 버튼 `p-2` — ~36px, 44px 미달 |
| `Header.tsx` | 186 | 햄버거 메뉴 버튼 `p-2` — ~36px, 44px 미달 |
| `MovieCard.tsx` | 93 | 트레일러 표시기 hover-only — 모바일에서 보이지 않음 |
| `HybridMovieCard.tsx` | 123 | 트레일러 표시기 hover-only — 모바일에서 보이지 않음 |
| `MovieRow.tsx` | 96-108 | 새로고침 버튼 `p-1.5` — ~28px, 44px 미달 |
| `MovieModal.tsx` | 277-291 | 별점 버튼 `p-1` + `w-7 h-7` — ~36px, 44px 미달 |
| `movies/[id]/page.tsx` | 185-202 | 영화 상세 별점 버튼 `p-0.5` — ~32px, 44px 미달 |
| `TrailerModal.tsx` | 86 | 닫기 버튼 `w-10 h-10` — 모바일에서 터치 어려움 |
| `login/page.tsx` | 62 | 닫기 버튼 `p-1.5` — ~28px, 44px 미달 |
| `signup/page.tsx` | 77 | 닫기 버튼 `p-1.5` — ~28px, 44px 미달 |
| `signup/page.tsx` | 99,114,129,144,158 | 입력 필드 `py-2.5` — 모바일 터치 경계 |
| `onboarding/page.tsx` | 337-354 | 별점 버튼 `p-0` — 터치 영역 전혀 없음 |
| `favorites/page.tsx` | 209-220 | 찜 해제 버튼 hover-only — 모바일 접근 불가 |
| `ratings/page.tsx` | 131-143 | 평점 삭제 버튼 hover-only — 모바일 접근 불가 |
| `profile/page.tsx` | 116 | 로그아웃 버튼 `py-2.5` — 경계값 |
| `ErrorBoundary.tsx` | 49,54 | 버튼 `py-2.5` — 경계값 |

## 수정 내용 (파일별)

### FeaturedBanner.tsx — 유도섹션 + 날씨/기분 터치 영역
- **유도섹션 위치**: 모바일에서 `fixed bottom-4 left-4 right-4` (하단 고정, thumb zone), 데스크톱은 기존 우측 상단 유지
- **섹션 너비**: 모바일 `w-full`, 데스크톱 `sm:w-80`
- **배경 가시성**: 모바일 `bg-black/60` (더 진하게), 데스크톱 `sm:bg-black/40`
- **MBTI 유도 링크**: `min-h-[44px]`, `py-3` (모바일) / `sm:py-2.5` (데스크톱)
- **날씨 버튼**: `p-2.5` (모바일, ~40px) / `sm:p-1.5` (데스크톱), gap 확대
- **기분 버튼**: `px-2 py-2 min-h-[36px]` (모바일) / `sm:px-1.5 sm:py-1` (데스크톱)
- **배너 버튼**: `flex-wrap gap-2 sm:gap-3` (줄바꿈 허용)

### Header.tsx — 터치 영역 확대
- 검색 버튼: `p-2` → `p-2.5 min-w-[44px] min-h-[44px]`
- 햄버거 버튼: `p-2` → `p-2.5 min-w-[44px] min-h-[44px]`

### MovieCard.tsx + HybridMovieCard.tsx — 모바일 트레일러 표시
- 트레일러 아이콘: `opacity-0 group-hover:opacity-100` → `opacity-100 sm:opacity-0 sm:group-hover:opacity-100`

### MovieRow.tsx — 새로고침 버튼 확대
- 새로고침 버튼: `p-1.5` → `p-2.5 sm:p-1.5 min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0`

### MovieModal.tsx — 별점 터치 영역
- 별점 버튼: `p-1` → `p-1.5 sm:p-1 min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0`

### movies/[id]/page.tsx — 상세 별점 터치 영역
- 별점 버튼: `p-0.5` → `p-1.5 sm:p-0.5 min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0`

### TrailerModal.tsx — 닫기 버튼 확대
- 닫기 버튼: `w-10 h-10` → `w-11 h-11 sm:w-10 sm:h-10`, 배경 더 진하게

### login/page.tsx + signup/page.tsx — 닫기 버튼 확대
- 닫기 버튼: `p-1.5` → `p-2.5 min-w-[44px] min-h-[44px]`
- signup 입력 필드: `py-2.5` → `py-3 text-base` (5개 필드)

### onboarding/page.tsx — 별점 터치 영역
- 별점 버튼: `p-0` → `p-1 min-w-[28px] min-h-[28px]` (카드 크기 제약으로 28px)

### favorites/page.tsx — 모바일 삭제 버튼 표시
- 찜 해제 버튼: `opacity-0 group-hover:opacity-100` → `opacity-100 sm:opacity-0 sm:group-hover:opacity-100`

### ratings/page.tsx — 모바일 삭제 버튼 표시
- 평점 삭제 버튼: `opacity-0 group-hover:opacity-100` → `opacity-100 sm:opacity-0 sm:group-hover:opacity-100`
- 터치 영역: `min-w-[44px] min-h-[44px]`

### profile/page.tsx — 로그아웃 버튼
- `py-2.5` → `py-3 min-h-[44px]`

### ErrorBoundary.tsx — 버튼 높이
- `py-2.5` → `py-3 min-h-[44px]` (새로고침, 홈으로)

## 모바일 터치 영역 개선 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 헤더 버튼 (검색/메뉴) | ~36px | 44px (min-w/min-h) |
| 날씨 토글 | ~28px | ~40px (p-2.5) |
| 기분 버튼 | ~24px | ~36px (py-2 min-h-[36px]) |
| 별점 (모달) | ~36px | 44px (min-w/min-h) |
| 별점 (상세) | ~32px | 44px (min-w/min-h) |
| 새로고침 | ~28px | 44px (min-w/min-h) |
| 닫기 (로그인/가입) | ~28px | 44px (min-w/min-h) |
| 온보딩 별점 | ~14px | ~28px (카드 크기 제약) |

## 유도섹션 변경 전/후

### 변경 전
- 우측 상단 고정 (`fixed top-[72px] right-4`) — 모바일에서 `w-80`(320px)가 360px 화면의 89% 차지
- 엄지 닿지 않는 위치 (상단)
- 작은 터치 영역

### 변경 후
- **모바일**: 하단 고정 (`fixed bottom-4 left-4 right-4`) — thumb zone, 전체 너비
- **데스크톱**: 기존 우측 상단 유지 (`sm:top-[72px] sm:right-4`)
- 배경 가시성 향상 (모바일에서 `bg-black/60`)
- 충분한 터치 영역 확보 (44px 기준)

## 검증 결과

- `npx tsc --noEmit`: 0 errors
- `npm run build`: 성공 (13/13 pages)
- `npm run lint`: 0 errors/warnings
- 커밋: `e44878b fix: 모바일 UI/UX 개선 — 터치 영역 + 유도섹션 + 레이아웃`
- 푸시: `origin/main` 완료
