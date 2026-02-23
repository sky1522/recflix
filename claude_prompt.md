claude "Phase 47A: TMDB 트레일러 데이터 수집 + API 반영.

=== Research ===
다음 파일들을 읽을 것:
- backend/app/models/movie.py (Movie 모델 전체)
- backend/app/schemas/movie.py (MovieDetail, MovieListItem 스키마)
- backend/app/api/v1/movies.py (영화 상세 API)
- backend/app/core/config.py (TMDB_API_KEY 설정 확인)
- backend/app/database.py (DB 연결)
- backend/scripts/ 디렉토리 구조 확인 (기존 배치 스크립트 패턴 참고)

=== 1단계: DB 스키마 변경 ===
movies 테이블에 trailer_key 컬럼 추가:

1-1. Alembic이 아직 없으므로 SQL 스크립트 생성:
backend/scripts/migrate_trailer.sql:
  ALTER TABLE movies ADD COLUMN IF NOT EXISTS trailer_key VARCHAR(20);
  CREATE INDEX IF NOT EXISTS idx_movies_trailer_key ON movies (trailer_key) WHERE trailer_key IS NOT NULL;

1-2. Movie 모델에 trailer_key 컬럼 추가:
  trailer_key = Column(String(20), nullable=True)

=== 2단계: TMDB 트레일러 수집 배치 스크립트 ===
backend/scripts/collect_trailers.py 생성:

2-1. TMDB API 호출:
  GET https://api.themoviedb.org/3/movie/{tmdb_id}/videos?language=ko-KR&include_video_language=ko,en
  Authorization: Bearer {TMDB_API_KEY}

2-2. 트레일러 선택 우선순위:
  - type='Trailer' AND site='YouTube' 필터
  - official=true 우선
  - iso_639_1='ko' 우선 → 없으면 'en'
  - 여러 개면 published_at 가장 최근 것

2-3. Rate limit 준수:
  - TMDB: ~40 requests/sec 허용
  - 안전하게 20 req/sec (0.05초 간격)
  - 총 42,917편 × 0.05초 = ~36분

2-4. 배치 처리:
  - 1000건씩 DB bulk update (commit 단위)
  - 진행률 표시: 매 1000건마다 로그 (processed/total, found/not_found)
  - 실패한 요청: 로그 후 스킵 (재실행 시 trailer_key IS NULL만 대상)
  - --dry-run 옵션: API 호출만 하고 DB 저장 안 함
  - --limit N 옵션: 테스트용 N건만 처리

2-5. 재실행 안전성:
  - WHERE trailer_key IS NULL인 영화만 대상
  - 이미 수집된 영화 스킵

2-6. 환경변수:
  - DATABASE_URL (필수)
  - TMDB_API_KEY (필수, bearer token)

=== 3단계: API 스키마/응답 반영 ===

3-1. MovieDetail 스키마에 trailer_key: Optional[str] 추가
3-2. MovieListItem 스키마에 trailer_key: Optional[str] 추가
3-3. 영화 상세 API 응답에 trailer_key 자동 포함 (ORM 필드 추가로 자동)

=== 규칙 ===
- 기존 API 동작 변경 금지 (trailer_key는 Optional 추가만)
- 배치 스크립트는 독립 실행 (python -m scripts.collect_trailers)
- TMDB API 키는 환경변수에서 읽기 (하드코딩 금지)
- httpx 사용 (기존 프로젝트 의존성)

=== 검증 ===
1. cd backend && ruff check app/ scripts/ → 0 issues
2. cd backend && python -c 'from app.main import app; print(app.title)'
3. cd backend && python scripts/collect_trailers.py --limit 5 --dry-run (스크립트 문법 확인)
4. SQL 스크립트 문법 확인
5. git add -A && git commit -m 'feat: Phase 47A TMDB 트레일러 수집 스크립트 + DB/API 스키마' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- migrate_trailer.sql 내용
- collect_trailers.py 주요 로직
- 스키마 변경 목록
- dry-run 테스트 결과"