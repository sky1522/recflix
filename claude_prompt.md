claude "Phase 33-1: 임베딩 기반 시맨틱 검색 — Backend 구현.

=== Research ===
먼저 다음 파일들을 읽고 현재 구조를 파악할 것:
- CLAUDE.md
- backend/app/core/config.py (Settings 클래스)
- backend/app/main.py (lifespan, 라우터 등록)
- backend/app/api/v1/movies.py (기존 검색 엔드포인트)
- backend/app/api/v1/router.py (라우터 등록)
- backend/app/services/llm.py (Redis 클라이언트 패턴 참고)
- backend/requirements.txt
- backend/.env (VOYAGE_API_KEY 확인)

=== 1. Voyage AI 임베딩 클라이언트 ===
backend/app/services/embedding.py 생성:
- get_query_embedding(text: str) → np.ndarray | None
- Voyage AI API 호출 (voyage-multilingual-2, 1024차원)
- Redis 캐싱: 키 semantic_emb:{md5_hash}, TTL 24시간
- 벡터를 bytes로 변환해서 Redis에 저장/복원
- API 키 없으면 None 반환 (graceful)
- httpx.AsyncClient 사용 (timeout 10초)
- Redis 클라이언트는 기존 llm.py의 get_redis_client 패턴 재사용

=== 2. 벡터 검색 모듈 ===
backend/app/api/v1/semantic_search.py 생성:
- 모듈 레벨 변수: _corpus_embeddings (np.ndarray), _movie_ids (list[int])
- load_embeddings() — 서버 시작 시 호출, data/embeddings/movie_embeddings.npy + movie_id_index.json 로드
  - L2 정규화 적용 (코사인 유사도 → 내적으로 변환)
  - 파일 없으면 warning 로그만 남기고 pass (임베딩 미생성 상태에서도 서버 기동 가능)
- search_similar(query_embedding, top_k=100) → list[tuple[int, float]]
  - np.argpartition으로 Top-K 추출 (O(N), argsort보다 빠름)
- is_semantic_search_available() → bool

=== 3. 시맨틱 검색 API 엔드포인트 ===
backend/app/api/v1/movies.py에 추가:
- GET /api/v1/movies/semantic-search?q=...&limit=20
- 파라미터: q (str, 필수, 최소 2자), limit (int, 기본 20, 최대 50)
- 흐름:
  1. Redis 결과 캐시 확인 (semantic_res:{hash}, TTL 30분)
  2. 캐시 미스 → get_query_embedding(q)
  3. 임베딩 None이면 → 기존 키워드 검색으로 폴백
  4. search_similar(embedding, top_k=100) → 후보 movie_id 목록
  5. DB에서 후보 영화 조회 (SELECT WHERE id IN (...))
  6. semantic_score 기준 정렬 + 품질 필터 (weighted_score >= 5.0)
  7. 상위 limit개 반환
- 응답에 포함: id, title, title_ko, poster_path, release_date, weighted_score, genres, semantic_score, search_time_ms
- Rate limit: 10/minute (시맨틱 검색은 API 호출 비용이 있으므로)
- is_semantic_search_available() False면 → 키워드 검색 폴백 + 응답에 fallback: true 표시

=== 4. config.py 수정 ===
Settings 클래스에 추가:
- VOYAGE_API_KEY: str = ""

=== 5. main.py 수정 ===
lifespan 함수에 임베딩 로드 추가:
- from app.api.v1.semantic_search import load_embeddings
- load_embeddings() 호출
- 로드 성공/실패 로그

=== 6. 임베딩 생성 스크립트 ===
backend/scripts/generate_embeddings.py 생성:
- DB에서 전체 영화 로드 (id, title, title_ko, overview, director_ko, emotion_tags, weather_scores, mbti_scores, genres, keywords)
- build_embedding_text(movie) — 설계 문서의 템플릿대로
  - 제목, 장르, 줄거리(:500), 분위기(emotion_tags >= 0.5), 날씨(weather_scores >= 0.3), MBTI(상위 3개), 키워드, 감독
- Voyage AI API로 배치 임베딩 (100개씩, 0.25초 딜레이)
- 진행률 표시 (매 배치)
- 1000개마다 중간 저장 (progress.json + partial.npy)
- --resume 플래그로 중단 후 재개 지원
- 출력: data/embeddings/movie_embeddings.npy, movie_id_index.json, embedding_metadata.json
- DATABASE_URL은 환경변수에서 읽기 (기본값: backend/.env의 DATABASE_URL)
- 실행: cd backend && python scripts/generate_embeddings.py --batch-size 100

=== 7. 디렉토리 구조 ===
backend/data/embeddings/ 디렉토리 생성
backend/data/embeddings/.gitkeep 생성 (.npy 파일은 .gitignore에 추가)

=== 규칙 ===
- 기존 movies.py의 검색 엔드포인트 수정 금지 (새 엔드포인트만 추가)
- 기존 추천 로직 수정 금지
- 임베딩 파일 없어도 서버가 정상 기동해야 함 (graceful degradation)
- numpy는 이미 설치되어 있음 (scipy 의존성)
- httpx도 이미 설치되어 있음
- requirements.txt에 voyageai 패키지 추가하지 않음 (httpx로 직접 호출)
- .gitignore에 *.npy, backend/data/embeddings/*.npy 추가

=== 검증 ===
1. cd backend && ruff check app/services/embedding.py app/api/v1/semantic_search.py
2. cd backend && python -c "from app.api.v1.semantic_search import load_embeddings, is_semantic_search_available; load_embeddings(); print('available:', is_semantic_search_available())"
   → available: False (임베딩 파일 아직 없으므로)
3. cd backend && python -c "from app.services.embedding import get_query_embedding; print('import OK')"
4. cd backend && python -c "from scripts.generate_embeddings import build_embedding_text; print(build_embedding_text({'title_ko': '테스트', 'title': 'Test', 'overview': '테스트 줄거리', 'genres': '드라마', 'emotion_tags': {'healing': 0.8, 'tension': 0.2}, 'weather_scores': {'rainy': 0.5}, 'mbti_scores': {}, 'keywords': '', 'director_ko': ''}))"
5. npm run build (frontend 변경 없으므로 생략 가능)
6. git add -A && git commit -m 'feat: Phase 33-1 시맨틱 검색 Backend 구현 (Voyage AI + NumPy 인메모리)' && git push origin HEAD:main

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- 생성/수정된 파일 목록
- 각 검증 결과
- generate_embeddings.py 실행 방법 안내
- 다음 단계 (임베딩 생성 실행)"