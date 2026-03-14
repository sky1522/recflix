# 2026-03-14: 라이트 모드 가독성 개선

---

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `frontend/components/movie/FeaturedBanner.tsx:82-85` | 그래디언트 오버레이를 다크 기반으로 변경 (`from-surface` → `from-black/80`) |
| `frontend/app/movies/[id]/components/MovieHero.tsx:59-61` | 동일하게 다크 오버레이 강화 |

## 핵심 변경사항

- **FeaturedBanner 히어로**: 좌→우 `from-black/80 via-black/50`, 하→상 `from-surface via-black/40` (하단은 페이지 배경과 자연스럽게 전환)
- **MovieHero 상세 페이지**: 하→상 `from-surface via-black/50`, 좌→우 `from-black/80`
- 상단/측면은 항상 다크 오버레이로 텍스트(text-white) 가독성 보장
- 하단은 `from-surface`를 유지하여 다크/라이트 모두 페이지 배경과 자연스러운 전환

## 수정 불필요 영역

- **MovieCard**: 호버 오버레이 `bg-black/60` — 이미 라이트 모드에서도 충분한 대비
- **HybridMovieCard**: 호버 `from-black/90` — 이미 정상
- **HybridMovieRow**: `text-fg` 시맨틱 토큰 사용 — 라이트 모드에서 정상 전환
- **헤더**: 스크롤 시 `bg-surface/95` — 라이트/다크 모두 정상

## 검증 결과

- [x] `npx next build` — 빌드 성공
- [x] `git push origin HEAD:main` — 푸시 완료
- [ ] 프로덕션 라이트/다크 모드 시각 확인

## 커밋

- `059ace0` fix: 라이트 모드 가독성 개선 (히어로/카드 오버레이 텍스트 대비)

---
---

# 2026-03-14: 헤더 로고 클래퍼보드 아이콘 추가 + R 글꼴 변경

---

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `frontend/components/layout/Header.tsx:196-203` | 로고에 Clapperboard 아이콘 추가, R 박스 SVG→텍스트 변환, Arial Black 폰트 적용 |

## 핵심 변경사항

- **Clapperboard 아이콘**: lucide-react에서 import, 흰색 20-22px, R 박스 좌측에 배치
- **R 박스 글꼴 변경**: SVG path → `<span>` + `font-family: 'Arial Black'`로 교체, bowl 균형 개선
- **ecflix 텍스트**: 동일하게 Arial Black 폰트 통일
- **레이아웃**: `gap-1.5`로 아이콘-로고 간격 설정
- **모바일 드로어**: 로고 없음 — 수정 불필요

## 검증 결과

- [x] `npx next build` — 빌드 성공
- [x] `git push origin HEAD:main` — 푸시 완료
- [ ] 프로덕션 시각 확인

## 커밋

- `2e4757f` style: 헤더 로고 클래퍼보드 아이콘 추가 + R 글꼴 변경

---
---

# 2026-03-14: 기분 드롭다운 너비 확장

---

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `frontend/components/layout/Header.tsx:323` | 기분 드롭다운 너비 `w-64`(256px) → `w-72`(288px) |

## 핵심 변경사항

- 데스크톱 헤더 기분 드롭다운 컨테이너 너비를 `w-72`로 확장
- "몽글몽글한", "상상에 빠진" 등 5글자 라벨이 한 줄에 표시됨
- 모바일 드로어(`HeaderMobileDrawer.tsx`)는 `grid-cols-4` + `text-[10px]`로 이미 정상 — 수정 불필요

## 검증 결과

- [x] `npx next build` — 빌드 성공
- [x] `git push origin HEAD:main` — 푸시 완료
- [ ] 프로덕션 확인

## 커밋

- `d47710b` fix: 기분 드롭다운 너비 확장 (5글자 라벨 줄바꿈 해소)

---
---

# 2026-03-14: 영화 등급 배지 한국어 툴팁 구현

---

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `frontend/lib/certificationTooltips.ts` | **신규** — 12개 등급 한국어 매핑 상수 + fallback |
| `frontend/components/ui/CertificationBadge.tsx` | **신규** — 공통 배지 컴포넌트 (3 variant, 포탈 툴팁) |
| `frontend/app/globals.css` | 툴팁 페이드인 애니메이션 추가 (`animate-tooltip-fade`) |
| `frontend/components/movie/MovieCard.tsx` | 인라인 배지 → `CertificationBadge` 교체 |
| `frontend/components/movie/MovieModal.tsx` | 인라인 배지 → `CertificationBadge variant="outlined"` 교체 |
| `frontend/app/movies/[id]/components/MovieHero.tsx` | 인라인 배지 → `CertificationBadge variant="outlined-white"` 교체 |
| `frontend/components/movie/FeaturedBanner.tsx` | 인라인 조건부 색상 배지 → `CertificationBadge variant="outlined"` 교체 |

## 핵심 변경사항

1. **CertificationBadge 공통 컴포넌트** — 4개 파일의 인라인 배지를 하나의 컴포넌트로 통합
2. **한국어 툴팁** — 호버/탭 시 한국 등급명(bold) + 설명 표시
3. **등급 매핑** — G, PG, PG-13, R, NC-17, NR, UR, 12, 15, 18, 19, ALL (12종 + fallback)
4. **포탈(Portal) 기반 툴팁** — `overflow-hidden` 컨테이너에서도 클리핑 없이 표시
5. **뷰포트 경계 감지** — 하단 공간 부족 시 상단에 툴팁 표시, 좌우 클램핑
6. **모바일 대응** — 탭 토글 + 외부 터치 시 닫힘
7. **접근성** — `aria-label`에 한국어 등급 설명 포함
8. **애니메이션** — opacity 0→1, translateY -4px→0, 150ms ease-out

## 미적용 항목 (프롬프트에 언급되었으나 해당 코드 없음)

- **HybridMovieCard.tsx** — 등급 배지 렌더링이 원래 없음 (추천 점수/태그만 표시)
- **SearchAutocomplete.tsx** — 등급 배지 렌더링이 원래 없음
- **MovieSidebar.tsx** — 해당 컴포넌트 파일 미존재

## 검증 결과

- [x] `npx next build` — 빌드 성공 (ESLint + TypeScript 통과)
- [x] `git push origin HEAD:main` — 푸시 완료
- [ ] Vercel 자동 배포 확인
- [ ] 프로덕션 등급 툴팁 동작 검증

## 커밋

- `8df5ad7` feat: 영화 등급 배지 한국어 툴팁 추가 (CertificationBadge 공통 컴포넌트)
