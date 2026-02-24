claude "모바일 UI/UX 점검 + 유도섹션 터치 영역 개선.

=== Research ===
다음 파일들을 읽을 것:
- frontend/app/page.tsx (홈 페이지 — 유도섹션 구조)
- frontend/app/movies/[id]/page.tsx (영화 상세)
- frontend/app/movies/[id]/components/ (상세 컴포넌트들)
- frontend/components/movie/FeaturedBanner.tsx (배너 버튼)
- frontend/components/movie/MovieCard.tsx (카드 터치)
- frontend/components/movie/HybridMovieCard.tsx (카드 터치)
- frontend/components/movie/MovieRow.tsx (가로 스크롤 Row)
- frontend/components/movie/MovieModal.tsx (모달 — 모바일 크기)
- frontend/components/movie/MovieFilters.tsx (필터 — 모바일 배치)
- frontend/components/movie/MovieGrid.tsx (그리드 — 모바일 컬럼)
- frontend/components/movie/TrailerModal.tsx (트레일러 모달)
- frontend/components/movie/MovieTrailer.tsx (트레일러 섹션)
- frontend/components/search/SearchAutocomplete.tsx (검색 — 모바일)
- frontend/components/search/SearchResults.tsx (검색 결과)
- frontend/components/layout/Header.tsx (헤더 — 모바일)
- frontend/components/layout/HeaderMobileDrawer.tsx (모바일 메뉴)
- frontend/components/ErrorBoundary.tsx
- frontend/app/login/page.tsx (로그인 폼)
- frontend/app/signup/page.tsx (회원가입 폼)
- frontend/app/onboarding/page.tsx (온보딩)
- frontend/app/favorites/page.tsx
- frontend/app/ratings/page.tsx
- frontend/app/profile/page.tsx

=== 모바일 점검 기준 (360px ~ 430px 뷰포트) ===

1. 터치 영역:
   - 모든 버튼/링크: 최소 44x44px (Apple HIG) 또는 48x48px (Material)
   - 버튼 간 간격: 최소 8px
   - 작은 아이콘 버튼: padding으로 터치 영역 확보

2. 유도섹션 (홈 페이지 CTA, 추천 섹션 헤더, '더보기' 등):
   - 버튼이 너무 작거나 밀집되어 있는지
   - 텍스트가 잘리거나 줄바꿈이 어색한지
   - CTA 버튼이 화면 하단에서 thumb zone에 있는지

3. 레이아웃:
   - 가로 스크롤 Row: 터치 스와이프 가능한지, 스크롤바 숨김
   - 그리드: 모바일에서 2컬럼인지 (1컬럼이면 너무 길어짐)
   - 모달: 모바일에서 전체 화면 또는 적절한 크기
   - 필터 바: 모바일에서 가로 스크롤 또는 접기
   - 검색: 모바일에서 전체 너비 활용

4. 텍스트/폰트:
   - 최소 14px (모바일 가독성)
   - 긴 텍스트 truncate 또는 line-clamp
   - 영화 제목이 2줄 이상일 때 레이아웃 깨짐

5. 인터랙션:
   - hover 의존 UI가 모바일에서 접근 불가하진 않은지
   - 카드 ▶ 아이콘 (hover 전용) → 모바일에서 안 보임 → 대안 필요?
   - 스와이프 제스처와 스크롤 충돌

6. 특정 이슈 — 유도섹션 버튼:
   - 홈 페이지에서 비로그인 사용자 유도 (회원가입, 온보딩 등) 섹션 확인
   - 추천 섹션 상단의 '전체보기', '더보기' 같은 작은 버튼
   - FeaturedBanner의 '자세히 보기', '트레일러' 버튼 — 모바일에서 크기/간격
   - 영화 상세의 '찜하기', '평점', '트레일러' 버튼 — 모바일 배치

=== 수정 방침 ===

발견된 이슈를 직접 수정:

- 버튼 최소 높이: min-h-[44px] 또는 py-3 확보
- 버튼 간 간격: gap-3 이상
- 모바일 전용 크기 조정: sm: 브레이크포인트 활용
- 텍스트 truncate: line-clamp-1, line-clamp-2
- 모달 모바일 대응: max-h-[90vh] overflow-y-auto, 또는 모바일에서 full-screen
- hover 전용 UI → 모바일에서는 항상 표시 또는 터치 대안
- 유도섹션 버튼: 모바일에서 full-width 또는 충분한 크기

⚠️ 데스크톱 레이아웃은 변경하지 않음 (sm:/md:/lg: 브레이크포인트로 분리)
⚠️ 기존 기능 동작 변경 금지

=== 검증 ===
1. cd frontend && npx tsc --noEmit → 0 errors
2. cd frontend && npm run build → 성공
3. cd frontend && npm run lint → 0 errors
4. Chrome DevTools 모바일 뷰 (375px iPhone SE, 390px iPhone 14) 기준 확인 목록:
   - 홈: 유도섹션 버튼 터치 가능
   - 홈: MovieRow 스와이프 정상
   - 홈: FeaturedBanner 버튼 크기 적절
   - 검색: 자동완성 드롭다운 전체 너비
   - 영화 상세: 버튼 그룹 모바일 배치
   - 모달: 모바일에서 닫기/스크롤 정상
5. git add -A && git commit -m 'fix: 모바일 UI/UX 개선 — 터치 영역 + 유도섹션 + 레이아웃' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- 발견된 이슈 목록 (파일 + 라인 + 문제)
- 수정 내용 (파일별)
- 모바일 터치 영역 개선 요약
- 유도섹션 변경 전/후"