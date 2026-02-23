claude "Phase 47B: 트레일러 YouTube 임베드 UI.

=== Research ===
다음 파일들을 읽을 것:
- frontend/app/movies/[id]/page.tsx (영화 상세 페이지)
- frontend/app/movies/[id]/components/ (상세 페이지 컴포넌트들)
- frontend/components/movie/FeaturedBanner.tsx (배너 구조)
- frontend/components/movie/MovieCard.tsx (카드 구조)
- frontend/components/movie/HybridMovieCard.tsx (카드 구조)
- frontend/components/movie/MovieModal.tsx (모달 구조)
- frontend/types/index.ts (Movie 타입 — trailer_key 필드 추가 필요)
- frontend/lib/api.ts (API 함수)

=== 1단계: 타입 업데이트 ===
frontend/types/index.ts:
- Movie 타입에 trailer_key?: string 추가
- MovieDetail 타입에도 동일 추가

=== 2단계: 영화 상세 페이지 트레일러 섹션 ===
frontend/app/movies/[id]/components/MovieTrailer.tsx 생성:

2-1. 컴포넌트 구조:
  - props: { trailerKey: string | null | undefined }
  - trailerKey 없으면 null 반환 (섹션 숨김)
  - 섹션 제목: '트레일러' (h2)
  - YouTube iframe 임베드:
    src: https://www.youtube.com/embed/{trailerKey}
    allow: accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture
    allowFullScreen
  - 반응형: aspect-video (16:9), rounded-xl, overflow-hidden
  - loading="lazy" (viewport 진입 시 로드)

2-2. 상세 페이지에 배치:
  - 영화 정보 섹션 아래, 유사 영화 섹션 위에 배치
  - 기존 레이아웃 깨지지 않도록

=== 3단계: FeaturedBanner 트레일러 버튼 ===
frontend/components/movie/FeaturedBanner.tsx 수정:

3-1. '트레일러 보기' 버튼 추가:
  - trailer_key가 있는 영화만 표시
  - 기존 '자세히 보기' 버튼 옆에 배치
  - 아이콘: ▶ (Play) + '트레일러' 텍스트
  - 스타일: 반투명 배경, 기존 버튼과 조화

3-2. 클릭 시 트레일러 모달:
  - frontend/components/movie/TrailerModal.tsx 생성
  - 전체 화면 오버레이 (bg-black/80)
  - 중앙에 YouTube iframe (max-w-4xl, aspect-video)
  - 닫기: X 버튼 + ESC 키 + 배경 클릭
  - role='dialog' aria-modal='true' (접근성)
  - focus trap (MovieModal과 동일 패턴)

=== 4단계: MovieCard/MovieModal 트레일러 표시 ===

4-1. MovieCard.tsx + HybridMovieCard.tsx:
  - trailer_key 있는 영화: hover 시 작은 ▶ 아이콘 오버레이 (포스터 좌하단)
  - 아이콘만 표시, 클릭은 기존 동작 유지 (상세 페이지 이동)

4-2. MovieModal.tsx:
  - trailer_key 있으면 모달 내에 '트레일러 보기' 버튼 추가
  - 클릭 시 TrailerModal 열기

=== 규칙 ===
- YouTube iframe은 lazy loading 필수
- trailer_key 없는 영화는 트레일러 관련 UI 일절 표시하지 않음
- iframe sandbox 속성은 넣지 않음 (YouTube 재생에 필요한 기능 차단될 수 있음)
- 새 컴포넌트는 300줄 이내
- 기존 다크 테마 (zinc, dark 계열) 일관성 유지
- any 타입 금지

=== 검증 ===
1. cd frontend && npx tsc --noEmit → 0 errors
2. cd frontend && npm run build → 성공
3. cd frontend && npm run lint → 0 errors
4. trailer_key 포함된 영화 상세 페이지: 트레일러 섹션 표시
5. trailer_key 없는 영화: 트레일러 관련 UI 숨김
6. FeaturedBanner: 트레일러 버튼 + 모달 동작
7. git add -A && git commit -m 'feat: Phase 47B 트레일러 YouTube 임베드 UI' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- 새로 생성된 컴포넌트 목록 + 역할
- 타입 변경 내용
- 트레일러 표시 위치 요약 (상세/배너/카드/모달)
- 접근성 처리 요약"