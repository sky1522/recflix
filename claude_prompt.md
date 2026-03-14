# RecFlix — 헤더 로고에 클래퍼보드 아이콘 추가

## 목표
헤더의 RecFlix 로고 좌측에 영화 클래퍼보드 아이콘을 추가하여 시각적 완성도를 높인다.

## 수정 파일
`frontend/components/layout/Header.tsx` — 로고 영역

## 구현
- lucide-react의 `Clapperboard` 아이콘 사용 (`import { Clapperboard } from "lucide-react"`)
- 아이콘 위치: 빨간 R 박스 왼쪽
- 아이콘 크기: 20~22px (헤더 로고와 시각적 균형)
- 아이콘 색상: 흰색 또는 RecFlix 레드(#C0392B) — 다크 헤더 배경에서 잘 보이는 쪽으로
- 아이콘과 R 박스 사이 간격: gap 6~8px
- 레이아웃: `flex items-center gap-1.5` 또는 `gap-2`로 아이콘 + 기존 로고(R박스 + ecflix) 배치
- 모바일에서도 동일하게 표시 (아이콘 숨김 처리 불필요)

## R 박스 글꼴 수정
- 현재 빨간 R 박스의 "R" 글자에서 둥근 부분(bowl)이 글꼴 특성상 위로 많이 튀어나와 보이는 문제
- 이것은 CSS 정렬 문제가 아니라 **폰트 디자인** 문제
- 수정: R 글자에 사용하는 폰트를 변경하여 균형 잡힌 R로 교체
  - 후보 1: `font-family: 'Arial Black', sans-serif` — R의 bowl이 컴팩트
  - 후보 2: `font-family: 'Helvetica Neue', 'Helvetica', sans-serif` — 깔끔한 산세리프
  - 후보 3: `font-family: 'Inter', sans-serif` — 모던하고 균형 잡힌 R
  - 후보 4: `font-family: 'Montserrat', sans-serif` — Netflix 스타일 굵은 산세리프 (Google Fonts)
- R 박스에만 적용, "ecflix" 텍스트의 폰트는 변경하지 않음 (또는 함께 변경해도 무방, 어울리는 쪽으로)
- 변경 후 R의 둥근 부분이 박스 안에 균형 있게 들어가는지 시각적으로 확인할 것

## 주의
- "ecflix" 텍스트도 같은 폰트로 통일하는 것이 자연스러울 수 있음 — 적용 후 판단
- 모바일 드로어(HeaderMobileDrawer.tsx)에도 로고가 있으면 동일하게 적용
- MobileNav.tsx 하단 바에는 적용 불필요

## 검증
1. 데스크톱: 헤더에서 클래퍼보드 아이콘 + R + ecflix 조합 확인
2. R 글자의 둥근 부분(bowl)이 박스 안에 균형 있게 들어가는지 확인
3. 모바일: 아이콘이 헤더 영역을 넘치지 않는지 확인
4. 다크/라이트 모드 양쪽에서 아이콘 + R 가시성 확인
5. npx next build 성공

## 완료 후
1. git add -A && git commit -m "style: 헤더 로고 클래퍼보드 아이콘 추가 + R 글꼴 변경"
2. git push origin main
3. 결과를 claude_results.md에 저장