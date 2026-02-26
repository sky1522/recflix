# Step 01C: 프론트엔드 이벤트에 request_id, rank, algorithm_version 전파

> 작업일: 2026-02-26
> 목적: 노출→클릭/찜/평점 연결 완성. 프론트 이벤트에 request_id 전파 + 백엔드에서 reco 테이블 라우팅

## 수정된 파일

### 프론트엔드 (10개)

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/types/index.ts` | HomeRecommendations에 `request_id`, `algorithm_version` 필드 추가 |
| `frontend/lib/eventTracker.ts` | EventType에 `"judgment"` 추가 |
| `frontend/app/page.tsx` | requestId를 MovieRow, HybridMovieRow에 전달 |
| `frontend/components/movie/MovieRow.tsx` | `requestId` prop 추가, MovieCard + useImpressionTracker에 전달 |
| `frontend/components/movie/HybridMovieRow.tsx` | `requestId` prop 추가, HybridMovieCard + useImpressionTracker에 전달 |
| `frontend/components/movie/MovieCard.tsx` | `requestId` prop 추가, 클릭 이벤트에 request_id 포함, URL에 `rid` 파라미터, MovieModal에 전달 |
| `frontend/components/movie/HybridMovieCard.tsx` | 동일 (requestId prop, 클릭 이벤트, URL, MovieModal) |
| `frontend/components/movie/MovieModal.tsx` | `requestId` prop, 찜/평점 이벤트에 request_id 포함, judgment 이벤트 추가 |
| `frontend/app/movies/[id]/page.tsx` | URL에서 `rid` 추출, detail_view/leave/favorite/rating에 request_id 포함, judgment 이벤트 추가 |
| `frontend/hooks/useImpressionTracker.ts` | `requestId` 파라미터, 노출 이벤트에 request_id 포함, movie_ids 상한 10→20 |

### 백엔드 (2개)

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/schemas/user_event.py` | ALLOWED_EVENT_TYPES에 `"judgment"` 추가 |
| `backend/app/api/v1/events.py` | 배치 핸들러에서 reco_interactions/reco_judgments 라우팅 추가 |

## 이벤트 흐름 요약

### 클릭 (movie_click)
```
홈 → MovieCard 클릭
  → trackEvent({ event_type: "movie_click", metadata: { request_id, section, position } })
  → 백엔드 events/batch
    → user_events INSERT (기존)
    → reco_interactions INSERT (request_id, position, section)
```

### 찜 (favorite_add/remove)
```
MovieModal 또는 상세 페이지 → 찜 토글
  → trackEvent({ event_type: "favorite_add", metadata: { request_id } })
  → 백엔드 events/batch
    → user_events INSERT (기존)
    → reco_interactions INSERT (request_id, event_type=favorite_add)
```

### 평점 (rating + judgment)
```
MovieModal 또는 상세 페이지 → 별점 클릭
  → trackEvent({ event_type: "rating", metadata: { rating, request_id } })
  → trackEvent({ event_type: "judgment", metadata: { label_type: "rating", label_value, request_id } })
  → 백엔드 events/batch
    → user_events INSERT x2 (기존)
    → reco_interactions INSERT (event_type=rating 이벤트는 _INTERACTION_TYPES에 없으므로 안 감)
    → reco_judgments INSERT (label_type=rating, label_value=score)
```

## 검증 결과

| 항목 | 결과 |
|------|------|
| 프론트엔드 빌드 (`next build`) | OK (tsc 에러 없음) |
| 백엔드 Ruff 린트 | OK |
| 백엔드 pytest (10 passed) | OK |

## 기존 동작 호환성

- user_events 테이블 구조 변경 없음
- 기존 eventTracker 인터페이스 breaking change 없음 (EventType에 judgment 추가만)
- MovieCard의 기존 필수 props 변경 없음 (requestId는 optional)
- 추천 외 페이지(검색 결과 등)에서 requestId=undefined → 이벤트 metadata에서 생략 → 에러 없음
- request_id가 없는 이벤트(검색 클릭 등)는 reco_interactions에 request_id=NULL로 저장
