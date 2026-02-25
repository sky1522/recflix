claude "Phase 52A: 이벤트 트래킹 사각지대 해소 + 추천 컨텍스트 전파.

=== Research ===
codex_results.md를 읽고 이벤트 누락 목록을 확인할 것.
그리고 다음 파일들을 읽을 것:
- frontend/components/movie/MovieModal.tsx (찜/평점 핸들러)
- frontend/components/movie/FeaturedBanner.tsx (찜/상세보기/트레일러 핸들러)
- frontend/lib/eventTracker.ts (trackEvent 함수)
- frontend/app/movies/[id]/page.tsx (상세 페이지 이벤트 — 참고 패턴)
- frontend/components/movie/MovieCard.tsx (클릭 이벤트 — 참고 패턴)
- frontend/components/search/SearchResults.tsx (검색 클릭 — 참고 패턴)

=== 1단계: MovieModal 이벤트 추가 ===
MovieModal.tsx에서 누락된 이벤트 추가:

1-1. 찜 토글 (handleFavoriteClick 또는 유사 함수):
  trackEvent('favorite_add' 또는 'favorite_remove', {
    movie_id: movie.id,
    source: 'movie_modal'
  })

1-2. 평점 등록 (handleRatingClick 또는 유사 함수):
  trackEvent('rating', {
    movie_id: movie.id,
    rating: selectedRating,
    source: 'movie_modal'
  })

1-3. 유사 영화 클릭: MovieModal 내에서 렌더링하는 유사 영화 카드에
  section='similar_in_modal' prop 전달 → MovieCard에서 movie_click 이벤트 발생

=== 2단계: FeaturedBanner 이벤트 추가 ===
FeaturedBanner.tsx에서 누락된 이벤트 추가:

2-1. 찜 추가 (handleAddToList 또는 유사 함수):
  trackEvent('favorite_add', {
    movie_id: movie.id,
    source: 'featured_banner'
  })

2-2. 상세보기 클릭:
  trackEvent('movie_click', {
    movie_id: movie.id,
    source: 'featured_banner',
    section: 'featured'
  })

2-3. 트레일러 클릭:
  trackEvent('movie_click', {
    movie_id: movie.id,
    source: 'featured_banner',
    section: 'featured',
    action: 'trailer'
  })

=== 3단계: 추천 컨텍스트 전파 ===

3-1. movie_detail_view에 source_section 추가:
  현재: trackEvent('movie_detail_view', { referrer })
  방법: URL에 query param 추가 (?from=hybrid_for_you&pos=3)
  
  MovieCard/HybridMovieCard에서 영화 링크에 from/pos 전달:
  href={`/movies/${movie.id}?from=${section}&pos=${index}`}
  
  상세 페이지에서 searchParams로 읽어서 이벤트에 포함:
  trackEvent('movie_detail_view', {
    referrer,
    source_section: searchParams.get('from') || 'direct',
    source_position: searchParams.get('pos') || null
  })

3-2. rating/favorite 이벤트에도 source_section 전파:
  상세 페이지 진입 시 source_section을 state로 저장
  찜/평점 이벤트에 포함:
  trackEvent('rating', {
    movie_id, rating, source: 'detail_page',
    source_section: sourceSection
  })

⚠️ 기존 이벤트 구조 깨뜨리지 않기 (새 필드는 optional 추가)
⚠️ 검색에서 온 경우: from=search, 직접 접근: from=direct

=== 4단계: preferred_genres 가중치 강화 ===

backend/app/api/v1/recommendation_engine.py:
  현재: preferred_genres에서 각 장르 += 1
  변경: preferred_genres에서 각 장르 += 3
  근거: 찜=1, 고평점=2인데 온보딩 장르가 1이면 영향력 부족
  3으로 올리면 고평점과 동등 이상 → 콜드스타트 초기에 의미있는 차이

=== 규칙 ===
- 기존 이벤트 스키마 변경 금지 (metadata에 필드 추가만)
- trackEvent 호출 패턴은 기존 코드와 동일하게
- URL param은 사용자에게 보이지만 UX에 영향 없음
- any 타입 금지

=== 검증 ===
1. cd frontend && npx tsc --noEmit → 0 errors
2. cd frontend && npm run build → 성공
3. cd frontend && npm run lint → 0 errors
4. cd backend && ruff check app/ → 0 issues
5. grep -rn 'trackEvent' frontend/components/movie/MovieModal.tsx → 2건 이상
6. grep -rn 'trackEvent' frontend/components/movie/FeaturedBanner.tsx → 2건 이상
7. git add -A && git commit -m 'feat: Phase 52A 이벤트 사각지대 해소 + 추천 컨텍스트 전파' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- 추가된 이벤트 목록 (파일 + 이벤트 타입 + 메타데이터)
- 추천 컨텍스트 전파 흐름
- preferred_genres 가중치 변경"