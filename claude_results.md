# Phase 42: DB 성능 최적화 — 결과

## 날짜
2026-02-23

## 변경 파일 목록

| # | 파일 | 주요 변경 |
|---|------|----------|
| 1 | `backend/app/api/v1/recommendation_engine.py` | N+1 제거(selectinload), LLM ID 캐시(TTL 5min), score_type 화이트리스트 |
| 2 | `backend/app/api/v1/recommendations.py` | popular/top_rated/for-you 쿼리 selectinload 추가 |
| 3 | `backend/app/api/v1/movies.py` | 영화 상세/검색/유사/온보딩 N+1 제거 (selectinload) |
| 4 | `backend/app/api/v1/semantic_search.py` | 쿼리 벡터 norm=0 가드 추가 |
| 5 | `backend/app/services/weather.py` | Redis 연결 REDIS_URL 우선 처리 (llm.py와 통일) |
| 6 | `backend/scripts/migrate_search_index.sql` | pg_trgm GIN 인덱스 3개 (title_ko, title, cast_ko) |

## 1단계: N+1 쿼리 제거 (selectinload)

**문제**: Movie.genres 등 M:M 관계를 반복문 내에서 접근 시 N+1 쿼리 발생

**해결**: 모든 Movie 쿼리에 `selectinload(Movie.genres)` 추가

| 위치 | 파일 | 적용 |
|------|------|------|
| `get_movies_by_score()` | recommendation_engine.py | `selectinload(Movie.genres)` |
| popular_q, top_rated_q | recommendations.py | `selectinload(Movie.genres)` |
| `/popular`, `/top-rated` | recommendations.py | `selectinload(Movie.genres)` |
| `/for-you` fallback | recommendations.py | `selectinload(Movie.genres)` |
| `get_movies()` 검색 | movies.py | `selectinload(Movie.genres)` |
| `get_movie()` 상세 | movies.py | `selectinload(Movie.genres, cast_members, keywords, countries)` |
| `get_similar_movies()` | movies.py | 직접 쿼리 + `selectinload(Movie.genres)` |
| `get_onboarding_movies()` | movies.py | `selectinload(Movie.genres)` |

## 2단계: LLM Movie ID 프로세스 캐시

**문제**: `get_llm_movie_ids()` — 매 요청마다 DB 쿼리 (popularity Top 1000)

**해결**: `time.monotonic()` 기반 프로세스 레벨 캐시 (TTL 5분)
```python
_llm_ids_cache: set | None = None
_llm_ids_cache_time: float = 0.0
_LLM_IDS_CACHE_TTL = 300.0  # 5 minutes
```

## 3단계: pg_trgm 검색 인덱스

**파일**: `backend/scripts/migrate_search_index.sql`

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_title_ko_trgm ON movies USING gin (title_ko gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_title_trgm ON movies USING gin (title gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_cast_ko_trgm ON movies USING gin (cast_ko gin_trgm_ops);
```

- `CONCURRENTLY`: 무중단 인덱스 생성 (테이블 락 없음)
- 적용 대상: `ilike('%...%')` 패턴 검색 쿼리 가속

## 4단계: 기타 최적화

### weather.py Redis 연결 통일
- `REDIS_URL` 환경변수가 있으면 우선 사용 (Railway 배포 호환)
- 기존 HOST/PORT/PASSWORD 방식은 폴백

### semantic_search.py norm=0 가드
```python
norm = np.linalg.norm(query_embedding)
if norm < 1e-10:
    return []
query_norm = query_embedding / norm
```

### score_type SQL 인젝션 방지
```python
_ALLOWED_SCORE_TYPES = {"mbti_scores", "weather_scores", "emotion_tags"}
if score_type not in _ALLOWED_SCORE_TYPES:
    logger.warning("Invalid score_type requested: %s", score_type)
    return []
```

## 검증 결과
- `ruff check` (Phase 42 파일): 0 errors
- `next build`: 성공 (13/13 pages)
- weather.py 기존 스타일 이슈 5건 (UP007, SIM108): Phase 42 범위 외, 기존 상태 유지
