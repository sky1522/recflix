# Phase 49B: pytest 기본 스위트 + 구조화 로깅

**날짜**: 2026-02-24

## 변경/생성 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/tests/__init__.py` | 테스트 패키지 (신규) |
| `backend/tests/conftest.py` | 공유 픽스처: SQLite, JSONB→JSON, Redis mock (신규) |
| `backend/tests/test_health.py` | 헬스체크 테스트 2건 (신규) |
| `backend/tests/test_auth.py` | 인증 테스트 5건 (신규) |
| `backend/tests/test_movies.py` | 영화 테스트 4건 (신규) |
| `backend/tests/test_recommendations.py` | 추천 테스트 3건 (신규) |
| `backend/pytest.ini` | pytest 설정 (신규) |
| `backend/app/core/logging_config.py` | structlog 설정 (신규) |
| `backend/app/middleware/__init__.py` | 미들웨어 패키지 (신규) |
| `backend/app/middleware/request_id.py` | X-Request-ID 미들웨어 (신규) |
| `backend/app/main.py` | structlog 초기화 + RequestIDMiddleware 추가 |
| `.github/workflows/ci.yml` | backend-test job 추가 (pytest) |
| `backend/requirements.txt` | structlog, python-json-logger 추가 |

## pytest 테스트 결과

```
10 passed, 4 skipped in 6.61s
```

| 테스트 | 결과 |
|--------|------|
| `test_health_returns_200` | PASSED |
| `test_health_contains_components` | PASSED |
| `test_signup_success` | PASSED |
| `test_signup_duplicate_email` | PASSED |
| `test_login_success` | PASSED |
| `test_login_wrong_password` | PASSED |
| `test_refresh_token` | PASSED |
| `test_get_movies_returns_200` | PASSED |
| `test_get_movies_with_genre_filter` | PASSED |
| `test_get_movie_not_found` | PASSED |
| `test_autocomplete` | SKIPPED (pg_trgm) |
| `test_get_recommendations_home` | SKIPPED (JSONB cast) |
| `test_get_popular` | SKIPPED (JSONB ordering) |
| `test_get_top_rated` | SKIPPED (JSONB ordering) |

## conftest.py 설정 요약

- **DB**: SQLite in-memory + StaticPool (테스트 간 격리)
- **JSONB→JSON**: `Base.metadata` 순회하여 JSONB 컬럼을 JSON으로 변환
- **Rate Limiting**: `limiter.enabled = False`로 비활성화
- **Redis Mock**: `get_redis_client`를 None 반환 함수로 패치 (5개 모듈)
- **Foreign Keys**: SQLite PRAGMA foreign_keys=ON

## CI 변경 내용

- `backend-test` job 추가: `pip install -r requirements.txt` → `pytest -v --tb=short`
- `deploy-backend` needs에 `backend-test` 추가 (테스트 통과 필수)

## structlog 설정 요약

- **Production**: JSON one-line output (Railway 로그 파싱 가능)
- **Development**: Colored console output (human-readable)
- **통합**: stdlib logging과 완전 호환 (기존 `logging.info()` 코드 변경 불필요)
- **Request ID**: `X-Request-ID` 미들웨어로 모든 요청에 UUID 바인딩
- **Noisy loggers**: `uvicorn.access`, `httpx`, `httpcore` → WARNING 레벨

## 검증 결과

| 항목 | 결과 |
|------|------|
| `pytest -v --tb=short` | 10 passed, 4 skipped |
| `ruff check app/ tests/` | 0 issues |
| `from app.main import app` | 정상 (RecFlix) |
| `import structlog; log.info("test")` | 정상 출력 |
