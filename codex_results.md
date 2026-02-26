# Step 01C Review — 프론트엔드 이벤트 request_id + rank 전파

## Findings (Severity Order)

### CRITICAL
1. `create_events_batch`가 `user_events`와 `reco_interactions/reco_judgments`를 동일 트랜잭션으로 커밋합니다. `reco_*` 삽입 중 하나라도 실패하면 `db.rollback()`으로 `user_events`까지 함께 롤백되어 배치 이벤트가 통째로 유실될 수 있습니다.
- 근거: `backend/app/api/v1/events.py:91`, `backend/app/api/v1/events.py:100`, `backend/app/api/v1/events.py:113`, `backend/app/api/v1/events.py:122`, `backend/app/api/v1/events.py:124`, `backend/app/api/v1/events.py:125`, `backend/app/api/v1/events.py:126`, `backend/app/api/v1/events.py:128`
- 체크리스트 영향: `reco_interactions/judgments INSERT 실패가 전체 배치를 중단하지 않는지` 항목 미충족

### WARNING
- 없음

### INFO
- 없음

## 체크리스트 검증

### 프론트엔드 — request_id 전파 체인
- [x] page.tsx에서 추천 응답의 request_id를 상태로 보관하고 MovieRow/HybridMovieRow에 전달
  - 근거: `frontend/app/page.tsx:43`, `frontend/app/page.tsx:133`, `frontend/app/page.tsx:285`, `frontend/app/page.tsx:306`
- [x] MovieRow → MovieCard로 requestId + rank(index) 전달
  - 근거: `frontend/components/movie/MovieRow.tsx:16`, `frontend/components/movie/MovieRow.tsx:146`
- [x] HybridMovieRow → HybridMovieCard로 requestId + rank(index) 전달
  - 근거: `frontend/components/movie/HybridMovieRow.tsx:17`, `frontend/components/movie/HybridMovieRow.tsx:155`
- [x] requestId가 모든 경로에서 optional(undefined 허용)
  - 근거: `frontend/components/movie/MovieRow.tsx:16`, `frontend/components/movie/HybridMovieRow.tsx:17`, `frontend/components/movie/MovieCard.tsx:33`, `frontend/components/movie/HybridMovieCard.tsx:18`, `frontend/components/movie/MovieModal.tsx:19`, `frontend/hooks/useImpressionTracker.ts:14`, `frontend/app/movies/[id]/page.tsx:26`

### 프론트엔드 — 이벤트 payload
- [x] MovieCard 클릭 metadata에 request_id, rank/position, section 포함
  - 근거: `frontend/components/movie/MovieCard.tsx:61`, `frontend/components/movie/MovieCard.tsx:65`, `frontend/components/movie/MovieCard.tsx:66`, `frontend/components/movie/MovieCard.tsx:67`, `frontend/components/movie/HybridMovieCard.tsx:73`, `frontend/components/movie/HybridMovieCard.tsx:77`, `frontend/components/movie/HybridMovieCard.tsx:78`, `frontend/components/movie/HybridMovieCard.tsx:79`
- [x] 찜 토글 metadata에 request_id 포함
  - 근거: `frontend/app/movies/[id]/page.tsx:115`, `frontend/app/movies/[id]/page.tsx:120`, `frontend/components/movie/MovieModal.tsx:114`, `frontend/components/movie/MovieModal.tsx:118`
- [x] 평점 입력 시 기존 rating 이벤트 유지 + 별도 judgment 이벤트 전송
  - 근거: `frontend/app/movies/[id]/page.tsx:136`, `frontend/app/movies/[id]/page.tsx:146`, `frontend/components/movie/MovieModal.tsx:135`, `frontend/components/movie/MovieModal.tsx:144`
- [x] judgment 이벤트에 label_type, label_value, request_id 포함
  - 근거: `frontend/app/movies/[id]/page.tsx:149`, `frontend/app/movies/[id]/page.tsx:150`, `frontend/app/movies/[id]/page.tsx:151`, `frontend/components/movie/MovieModal.tsx:147`, `frontend/components/movie/MovieModal.tsx:148`, `frontend/components/movie/MovieModal.tsx:149`
- [x] 추천 외 컨텍스트(requestId=undefined)에서 정상 동작
  - 근거: `frontend/hooks/useImpressionTracker.ts:35`, `frontend/components/movie/MovieCard.tsx:67`, `frontend/components/movie/HybridMovieCard.tsx:79`, `frontend/components/movie/MovieModal.tsx:118`, `frontend/app/movies/[id]/page.tsx:53`

### 프론트엔드 — 영화 상세 페이지
- [x] URL 파라미터(rid)에서 request_id 추출
  - 근거: `frontend/app/movies/[id]/page.tsx:26`
- [x] detail_view, detail_leave 이벤트에 request_id 포함
  - 근거: `frontend/app/movies/[id]/page.tsx:47`, `frontend/app/movies/[id]/page.tsx:53`, `frontend/app/movies/[id]/page.tsx:59`, `frontend/app/movies/[id]/page.tsx:63`
- [x] rid 없는 직접 URL 접근 시 에러 없이 동작
  - 근거: `frontend/app/movies/[id]/page.tsx:26`, `frontend/app/movies/[id]/page.tsx:53`, `frontend/app/movies/[id]/page.tsx:63`

### 백엔드 — 이벤트 라우팅
- [x] click/detail_view/detail_leave/favorite_add/favorite_remove → reco_interactions INSERT
  - 근거: `backend/app/api/v1/events.py:100`, `backend/app/api/v1/events.py:101`, `backend/app/api/v1/events.py:133`, `backend/app/api/v1/events.py:134`, `backend/app/api/v1/events.py:135`, `backend/app/api/v1/events.py:136`, `backend/app/api/v1/events.py:137`, `backend/app/api/v1/events.py:138`
- [x] judgment → reco_judgments INSERT(label_type, label_value 추출)
  - 근거: `backend/app/api/v1/events.py:113`, `backend/app/api/v1/events.py:114`, `backend/app/api/v1/events.py:118`, `backend/app/api/v1/events.py:119`
- [x] 기존 user_events INSERT가 모든 이벤트에 대해 유지(하위 호환)
  - 근거: `backend/app/api/v1/events.py:91`, `backend/app/api/v1/events.py:122`
- [x] request_id가 NULL인 이벤트도 정상 INSERT 가능
  - 근거: `backend/app/api/v1/events.py:102`, `backend/app/api/v1/events.py:115`
- [ ] reco_interactions/judgments INSERT 실패가 전체 배치를 중단하지 않음
  - 상태: 미충족(동일 트랜잭션 커밋/롤백 구조)
  - 근거: `backend/app/api/v1/events.py:122`, `backend/app/api/v1/events.py:124`, `backend/app/api/v1/events.py:125`, `backend/app/api/v1/events.py:126`, `backend/app/api/v1/events.py:128`

### 타입 안정성
- [x] EventType에 "judgment" 추가
  - 근거: `frontend/lib/eventTracker.ts:24`
- [x] HomeRecommendations 타입에 request_id, algorithm_version 필드 추가
  - 근거: `frontend/types/index.ts:68`, `frontend/types/index.ts:69`
- [x] requestId prop이 string | undefined 타입으로 선언
  - 근거: `frontend/components/movie/MovieRow.tsx:16`, `frontend/components/movie/HybridMovieRow.tsx:17`, `frontend/components/movie/MovieCard.tsx:33`, `frontend/components/movie/HybridMovieCard.tsx:18`, `frontend/components/movie/MovieModal.tsx:19`

## 결론
- Step 01C 구현은 프론트엔드 request_id/rank 전파와 judgment 이벤트 확장, 백엔드 라우팅까지 대부분 체크리스트를 충족합니다.
- 단, 배치 저장 트랜잭션이 결합되어 있어 `reco_*` 저장 실패 시 `user_events`까지 롤백되는 **CRITICAL 1건**이 남아 있습니다.
