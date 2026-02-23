# Phase 47B: 트레일러 YouTube 임베드 UI

**날짜**: 2026-02-23

## 변경/생성 파일

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/types/index.ts` | `Movie` 타입에 `trailer_key?: string \| null` 추가 |
| `frontend/app/movies/[id]/components/MovieTrailer.tsx` | 상세 페이지 트레일러 섹션 (신규) |
| `frontend/components/movie/TrailerModal.tsx` | 트레일러 모달 (신규) |
| `frontend/app/movies/[id]/page.tsx` | MovieTrailer 배치 (출연진↔유사영화 사이) |
| `frontend/components/movie/FeaturedBanner.tsx` | 트레일러 버튼 + TrailerModal 연동 |
| `frontend/components/movie/MovieModal.tsx` | 트레일러 버튼 + TrailerModal 연동 |
| `frontend/components/movie/MovieCard.tsx` | hover 시 ▶ 아이콘 오버레이 |
| `frontend/components/movie/HybridMovieCard.tsx` | hover 시 ▶ 아이콘 오버레이 |

## 컴포넌트 역할

### MovieTrailer (신규)
- 영화 상세 페이지 내 인라인 트레일러 섹션
- YouTube iframe 임베드, `loading="lazy"`, `aspect-video` 반응형
- `trailerKey` 없으면 null 반환 (섹션 숨김)

### TrailerModal (신규)
- 전체 화면 오버레이 (`bg-black/80`) + 중앙 YouTube iframe
- `autoplay=1` 자동 재생
- 닫기: X 버튼 + ESC 키 + 배경 클릭
- `role="dialog"` `aria-modal="true"` 접근성
- focus trap (MovieModal과 동일 패턴)

## 트레일러 표시 위치 요약

| 위치 | 동작 |
|------|------|
| **영화 상세 페이지** | 출연진 아래, 유사 영화 위에 인라인 iframe |
| **FeaturedBanner** | '미리보기' 옆 '트레일러' 버튼 → TrailerModal |
| **MovieModal** | 찜하기 옆 '트레일러' 버튼 → TrailerModal |
| **MovieCard** | hover 시 포스터 좌하단 ▶ 아이콘 (클릭은 기존 동작 유지) |
| **HybridMovieCard** | hover 시 포스터 좌하단 ▶ 아이콘 (클릭은 기존 동작 유지) |

## 접근성 처리

- TrailerModal: `role="dialog"`, `aria-modal="true"`, `aria-label="트레일러"`
- ESC 키로 닫기
- focus trap (Tab/Shift+Tab 순환)
- 닫을 때 트리거 요소로 포커스 복귀
- 닫기 버튼: `aria-label="닫기"`

## 검증 결과

| 항목 | 결과 |
|------|------|
| `npx tsc --noEmit` | 0 errors |
| `npm run build` | 13/13 pages 성공 |
| Lint (build 내장) | 0 errors |
