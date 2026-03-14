# RecFlix — 영화 등급 배지 한국어 툴팁 구현

## 목표
영화 포스터 좌측 상단에 표시되는 연령등급 배지(PG-13, R, 19 등)에 마우스 호버 시 한국어 툴팁을 표시한다. 기존 배지 디자인은 그대로 유지하되, 사용자가 등급의 의미를 쉽게 이해할 수 있도록 친절한 설명을 추가한다.

## 등급 매핑 테이블

아래 매핑을 상수 파일로 관리할 것:

```typescript
// frontend/lib/certificationTooltips.ts

export const CERTIFICATION_TOOLTIPS: Record<string, { label: string; description: string }> = {
  "G":     { label: "전체 관람가", description: "모든 연령층 관람 가능, 유해 요소 없음" },
  "PG":    { label: "12세 관람가", description: "부모 지도가 필요하거나 13세 미만 주의 콘텐츠" },
  "PG-13": { label: "12~15세 관람가", description: "부모 지도가 필요하거나 13세 미만 주의 콘텐츠" },
  "R":     { label: "15세~19세 관람가", description: "폭력성, 언어 수위 등으로 성인 보호자 동반 필요" },
  "NC-17": { label: "청소년 관람불가", description: "19세 미만 관람 절대 불가, 성인 전용 콘텐츠" },
  "NR":    { label: "19+ (미정)", description: "등급 미정 데이터는 보수적으로 성인물로 우선 분류" },
  "UR":    { label: "19+ (미정)", description: "등급 미정 데이터는 보수적으로 성인물로 우선 분류" },
  // 숫자형 등급 (한국/일본 등)
  "12":    { label: "12세 이상 관람가", description: "12세 미만은 보호자 동반 시 관람 가능" },
  "15":    { label: "15세 이상 관람가", description: "15세 미만 관람 불가" },
  "18":    { label: "청소년 관람불가", description: "18세 미만 관람 불가, 성인 전용" },
  "19":    { label: "청소년 관람불가", description: "19세 미만 관람 불가, 성인 전용" },
  "ALL":   { label: "전체 관람가", description: "모든 연령층 관람 가능" },
};

// fallback: 매핑에 없는 등급
export const DEFAULT_TOOLTIP = { label: "등급 정보", description: "상세 등급 정보를 확인해주세요" };
```

## 구현 사항

### 1. CertificationBadge 공통 컴포넌트 생성

`frontend/components/ui/CertificationBadge.tsx` 신규 생성:

- Props: `certification: string`, `size?: "sm" | "md"` (기본 sm)
- 기존 배지 스타일(색상, 크기, 위치) 그대로 유지
- 호버 시 툴팁 표시:
  - 배지 아래쪽에 말풍선 형태로 표시
  - 1줄: 한국 대응 등급 (Bold) — 예: "12~15세 관람가"
  - 2줄: 설명 — 예: "부모 지도가 필요하거나 13세 미만 주의 콘텐츠"
- 모바일: 탭 시 툴팁 표시, 외부 탭 시 닫힘
- 접근성: `aria-label`에 한국어 등급 설명 포함
- 다크/라이트 모드 모두 대응 (CSS 변수 사용)
- 애니메이션: `opacity 0→1`, `translateY -4px→0`, `150ms ease-out`

### 2. 툴팁 스타일

```
배경: var(--color-surface) 또는 반투명 다크 (rgba(0,0,0,0.85))
텍스트: var(--color-fg)
모서리: rounded-lg (8px)
패딩: px-3 py-2
그림자: shadow-lg
최대 너비: max-w-[200px]
폰트: 1줄 13px semibold, 2줄 12px regular
화살표: 상단 중앙에 삼각형 (CSS border trick)
z-index: 50 (다른 요소 위에 표시)
```

### 3. 적용 위치 — 모든 등급 배지 표시 지점

아래 파일에서 기존 등급 배지 렌더링 부분을 `<CertificationBadge>` 컴포넌트로 교체:

1. **MovieCard.tsx** — 포스터 좌측 상단 배지 (홈, 검색, 추천 등 모든 카드)
2. **HybridMovieCard.tsx** — 맞춤 추천 카드의 등급 배지
3. **MovieModal.tsx** — 영화 상세 모달의 등급 표시
4. **MovieHero.tsx** — 영화 상세 페이지 히어로 배너의 등급
5. **MovieSidebar.tsx** — 영화 상세 사이드바 정보
6. **SearchAutocomplete.tsx** — 검색 자동완성 드롭다운 (배지가 있는 경우)

### 4. 주의사항

- 기존 배지의 **색상 로직 그대로 유지** (G=초록, PG/PG-13=노랑, R=주황, NC-17/NR=빨강 등)
- 기존 **위치(absolute top-left)와 크기** 변경 없음
- 툴팁이 카드 영역을 벗어나는 경우 **overflow 클리핑 방지** — 필요 시 `overflow-visible` 설정 또는 포탈(portal) 사용
- MovieRow의 가로 스크롤 컨테이너에서 툴팁이 잘리지 않도록 처리
- `certification`이 null/undefined/빈 문자열인 경우 배지 자체를 표시하지 않음 (기존 동작 유지)

## 완료 후

1. 로컬에서 다음 시나리오 검증:
   - 홈 화면 MovieCard 호버 → 툴팁 표시 확인
   - 영화 상세 페이지 등급 호버 → 툴팁 확인
   - 모바일 뷰포트(360px)에서 탭 → 툴팁 표시/닫힘
   - 다크 모드 / 라이트 모드 양쪽 확인
   - 매핑에 없는 등급(예: "TV-MA") → fallback 툴팁 확인
2. git add -A && git commit -m "feat: 영화 등급 배지 한국어 툴팁 추가 (CertificationBadge 공통 컴포넌트)"
3. git push origin main
4. Vercel 자동 배포 확인
5. 프로덕션에서 등급 툴팁 동작 검증
6. 결과를 claude_results.md에 저장 (덮어 쓸 것, 위쪽에 추가x)