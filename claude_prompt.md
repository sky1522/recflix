claude "Phase 33-4: 시맨틱 검색 프로덕션 배포 + 최적화.

=== Research ===
먼저 다음을 확인할 것:
- backend/data/embeddings/movie_embeddings.npy 파일 크기 확인 (ls -la)
- backend/data/embeddings/movie_id_index.json 존재 확인
- backend/data/embeddings/embedding_metadata.json 존재 확인
- backend/app/api/v1/semantic_search.py (load_embeddings 함수)
- backend/app/api/v1/movies.py (semantic-search 엔드포인트)
- backend/app/services/embedding.py (get_query_embedding — Redis 캐싱 확인)

=== 1단계: 검색 시간 최적화 확인 ===
로컬에서 같은 쿼리 2번 연속 테스트:
- curl 'http://localhost:8000/api/v1/movies/semantic-search?q=비오는날혼자보기좋은잔잔한영화&limit=5'
- 1초 대기 후 같은 쿼리 재실행
- 두 번째 응답의 search_time_ms가 100ms 이하인지 확인 (Redis 캐시 히트)
- 안 되면 embedding.py의 Redis 캐싱 코드 확인

=== 2단계: Voyage API 응답 시간 분석 ===
semantic-search 엔드포인트에서 각 단계별 시간을 로깅하고 있는지 확인:
- Voyage API 호출 시간
- NumPy 검색 시간
- DB 조회 시간
만약 로깅이 없으면 추가:
```python
import time
t0 = time.time()
embedding = await get_query_embedding(q)
t1 = time.time()
results = search_similar(embedding, top_k=100)
t2 = time.time()
# DB 조회
t3 = time.time()
logger.info("Semantic search timing: embedding=%.0fms search=%.0fms db=%.0fms", 
            (t1-t0)*1000, (t2-t1)*1000, (t3-t2)*1000)
```

=== 3단계: Railway 배포 ===
- railway up 실행 (로컬 파일 직접 업로드)
- 176MB .npy 포함되므로 업로드 시간 좀 걸릴 수 있음
- 배포 후 서버 로그에서 'Loaded XXXXX movie embeddings' 확인
- curl https://backend-production-cff2.up.railway.app/api/v1/movies/semantic-search?q=비오는날좋은영화&limit=3
- 응답 확인

=== 4단계: Vercel 배포 ===
- cd frontend && npx vercel --prod
- 배포 완료 후 https://jnsquery-reflix.vercel.app 접속
- 검색창에 '비오는 날 혼자 보기 좋은 잔잔한 영화' 입력
- ✨ AI 추천 결과 섹션 표시되는지 확인

=== 규칙 ===
- 기존 검색/추천 코드 수정 금지
- 디버그 로깅 추가만 허용 (기존 로직 변경 X)
- Railway 배포 실패 시 원인 분석 후 결과에 기록

=== 검증 ===
1. 로컬 시맨틱 검색 — 캐시 히트 시 100ms 이하
2. Railway 배포 성공 + 임베딩 로드 로그 확인
3. 프로덕션 시맨틱 검색 API 응답 정상
4. Vercel 배포 + 프론트엔드 UI 동작 확인
5. git add -A && git commit -m 'feat: Phase 33-4 시맨틱 검색 프로덕션 배포 + 타이밍 로그' && git push origin HEAD:main

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- 검색 시간 분석 (단계별)
- Redis 캐시 히트 시 응답 시간
- Railway 배포 결과
- Vercel 배포 결과
- 프로덕션 E2E 테스트 결과"