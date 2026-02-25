# Phase 52A: 이벤트 사각지대 해소 + 추천 컨텍스트 전파

**날짜**: 2026-02-25
**커밋**: `8c990af`

---

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `frontend/components/movie/MovieModal.tsx` | 찜/평점 trackEvent 추가, similar 카드에 section prop 전달 |
| `frontend/components/movie/FeaturedBanner.tsx` | 찜/상세보기/트레일러 trackEvent 추가 |
| `frontend/components/movie/MovieCard.tsx` | Link href에 `?from=&pos=` 쿼리 파라미터 추가 |
| `frontend/components/movie/HybridMovieCard.tsx` | Link href에 `?from=&pos=` 쿼리 파라미터 추가 |
| `frontend/app/movies/[id]/page.tsx` | useSearchParams로 source_section/source_position 읽어 이벤트에 포함 |
| `backend/app/api/v1/recommendation_engine.py` | preferred_genres 가중치 1→3 강화 |

---

## 추가된 이벤트 목록

| 파일 | 이벤트 타입 | 메타데이터 |
|------|-----------|-----------|
| `MovieModal.tsx` | `favorite_add` / `favorite_remove` | `{source: "movie_modal"}` |
| `MovieModal.tsx` | `rating` | `{rating, source: "movie_modal"}` |
| `FeaturedBanner.tsx` | `favorite_add` / `favorite_remove` | `{source: "featured_banner"}` |
| `FeaturedBanner.tsx` | `movie_click` | `{source: "featured_banner", section: "featured"}` |
| `FeaturedBanner.tsx` | `movie_click` (trailer) | `{source: "featured_banner", section: "featured", action: "trailer"}` |
| `MovieModal.tsx` | `movie_click` (similar) | section="similar_in_modal" prop → MovieCard 내부 이벤트 |

---

## 추천 컨텍스트 전파 흐름

```
1. 사용자가 추천 카드 클릭
   MovieCard/HybridMovieCard → href="/movies/123?from=hybrid_for_you&pos=3"

2. 상세 페이지 진입
   useSearchParams → sourceSection="hybrid_for_you", sourcePosition="3"
   trackEvent("movie_detail_view", {
     referrer, source_section: "hybrid_for_you", source_position: 3
   })

3. 상세 페이지에서 찜/평점
   trackEvent("favorite_add", {source: "detail_page", source_section: "hybrid_for_you"})
   trackEvent("rating", {rating: 4, source: "detail_page", source_section: "hybrid_for_you"})

4. 직접 접근 시
   source_section="direct", source_position 없음
```

---

## preferred_genres 가중치 변경

- **이전**: `genre_counts[eng_name] += 1` (찜=1, 고평점=2와 동등 이하)
- **변경**: `genre_counts[eng_name] += 3` (고평점보다 높음)
- **근거**: 콜드스타트 시 온보딩 장르가 추천에 유의미한 영향을 미치도록
- **영향 범위**: `total_interactions < 5`인 사용자만 (기존 사용자 무영향)

---

## 검증 결과

| 검증 항목 | 결과 |
|----------|------|
| `npx tsc --noEmit` | 0 errors |
| `npm run build` | 성공 |
| `npm run lint` | 0 warnings, 0 errors |
| `ruff check app/` | All checks passed |
| `grep trackEvent MovieModal.tsx` | 3건 (import + favorite + rating) |
| `grep trackEvent FeaturedBanner.tsx` | 4건 (import + favorite + 상세보기 + 트레일러) |
| `git push` | 성공 |
