## 리뷰 대상: Step 01C — 프론트엔드 이벤트 request_id + rank 전파

### 리뷰 범위
- frontend/types/index.ts (수정)
- frontend/lib/eventTracker.ts (수정)
- frontend/app/page.tsx (수정)
- frontend/components/movie/MovieRow.tsx (수정)
- frontend/components/movie/HybridMovieRow.tsx (수정)
- frontend/components/movie/MovieCard.tsx (수정)
- frontend/components/movie/HybridMovieCard.tsx (수정)
- frontend/components/movie/MovieModal.tsx (수정)
- frontend/app/movies/[id]/page.tsx (수정)
- frontend/hooks/useImpressionTracker.ts (수정)
- backend/app/schemas/user_event.py (수정)
- backend/app/api/v1/events.py (수정)

### 체크리스트

#### 프론트엔드 — request_id 전파 체인
- [ ] page.tsx에서 추천 응답의 request_id를 상태로 보관하고 MovieRow/HybridMovieRow에 전달
- [ ] MovieRow → MovieCard로 requestId + rank(index) 전달
- [ ] HybridMovieRow → HybridMovieCard로 requestId + rank 전달
- [ ] requestId가 모든 경로에서 optional (undefined 시 에러 없음)

#### 프론트엔드 — 이벤트 payload
- [ ] MovieCard 클릭 시 metadata에 request_id, rank/position, section 포함
- [ ] 찜 토글 시 metadata에 request_id 포함
- [ ] 평점 입력 시 기존 rating 이벤트 유지 + 별도 judgment 이벤트 전송
- [ ] judgment 이벤트에 label_type, label_value, request_id 포함
- [ ] 검색 결과 등 추천 외 컨텍스트에서 requestId=undefined → 정상 동작

#### 프론트엔드 — 영화 상세 페이지
- [ ] URL 파라미터(rid)에서 request_id 추출
- [ ] detail_view, detail_leave 이벤트에 request_id 포함
- [ ] 직접 URL 접근 시 (rid 없음) 에러 없이 동작

#### 백엔드 — 이벤트 라우팅
- [ ] events.py에서 event_type별 분기: click/detail_view/detail_leave/favorite_add/favorite_remove → reco_interactions INSERT
- [ ] judgment → reco_judgments INSERT (label_type, label_value 추출)
- [ ] 기존 user_events INSERT가 모든 이벤트에 대해 유지 (하위 호환)
- [ ] request_id가 NULL인 이벤트도 정상 INSERT (검색 클릭 등)
- [ ] reco_interactions/judgments INSERT 실패가 전체 배치를 중단하지 않는지

#### 타입 안전성
- [ ] EventType에 "judgment" 추가
- [ ] HomeRecommendations 타입에 request_id, algorithm_version 필드 추가
- [ ] requestId prop이 string | undefined 타입으로 선언

### 발견사항 분류
- CRITICAL: request_id 전파 누락, 이벤트 데이터 손실, 빌드 실패
- WARNING: 특정 경로에서 request_id 누락, 라우팅 누락, 타입 불일치
- INFO: 네이밍 일관성, 코멘트

### 출력
결과를 codex_results.md에 저장하세요.