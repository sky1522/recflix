claude "Phase 49B: 핵심 API pytest + 구조화 로깅.

=== Research ===
다음 파일들을 읽을 것:
- backend/app/main.py (앱 구조, 미들웨어)
- backend/app/api/v1/auth.py (인증 엔드포인트)
- backend/app/api/v1/recommendations.py (추천 엔드포인트)
- backend/app/api/v1/movies.py (영화 엔드포인트)
- backend/app/api/v1/health.py (헬스체크)
- backend/app/database.py (DB 세션)
- backend/app/core/config.py (설정)
- backend/requirements.txt (pytest 포함 여부)
- .github/workflows/ci.yml (현재 CI 구조)

=== 1단계: pytest 설정 ===

1-1. requirements.txt에 추가 (없으면):
  pytest>=7.0
  pytest-asyncio>=0.21
  httpx (이미 있을 것)

1-2. backend/pytest.ini 또는 pyproject.toml [tool.pytest] 설정:
  [pytest]
  asyncio_mode = auto
  testpaths = tests

1-3. backend/tests/ 디렉토리 구조:
  tests/
    __init__.py
    conftest.py (TestClient, 테스트 DB/모킹 설정)
    test_health.py
    test_auth.py
    test_movies.py
    test_recommendations.py

1-4. conftest.py:
  - FastAPI TestClient 설정 (from fastapi.testclient import TestClient)
  - DB 세션 오버라이드: 프로덕션 DB 접속하지 않도록
  - 방법 A: SQLite in-memory (가장 간단)
  - 방법 B: 테스트용 PostgreSQL (CI에서 services)
  - 방법 A로 시작 (빠른 셋업), PostgreSQL 특화 기능은 스킵 마킹

=== 2단계: 핵심 테스트 작성 ===

2-1. test_health.py (3건):
  - GET /health → 200, response에 status 포함
  - GET /health/db → DB 연결 상태
  - GET /health/redis → Redis 연결 상태 (Redis 없으면 graceful)

2-2. test_auth.py (5건):
  - POST /auth/signup → 201 (정상)
  - POST /auth/signup → 400 (중복 이메일)
  - POST /auth/login → 200 (정상, access_token 반환)
  - POST /auth/login → 401 (잘못된 비밀번호)
  - POST /auth/refresh → 200 (정상 토큰 갱신)

2-3. test_movies.py (5건):
  - GET /movies → 200 (목록)
  - GET /movies?genre=Action → 200 (필터)
  - GET /movies/{id} → 200 (상세)
  - GET /movies/{id} → 404 (존재하지 않는 ID)
  - GET /movies/autocomplete?q=test → 200

2-4. test_recommendations.py (3건):
  - GET /recommendations/popular → 200
  - GET /recommendations/top-rated → 200
  - GET /recommendations → 200 (비로그인 기본 추천)

⚠️ 테스트는 프로덕션 DB에 절대 접속하지 않을 것
⚠️ SQLite에서 안 되는 기능은 pytest.mark.skip으로 마킹
⚠️ 각 테스트는 독립적 (순서 무관)

=== 3단계: CI에 pytest 추가 ===
.github/workflows/ci.yml 수정:
  - backend job에 pytest 단계 추가
  - pip install -r requirements.txt
  - cd backend && pytest -v --tb=short
  - 실패 시 CI 실패 (필수 게이트)

=== 4단계: 구조화 로깅 ===

4-1. requirements.txt에 추가:
  structlog>=23.0
  python-json-logger>=2.0

4-2. backend/app/core/logging_config.py 생성 (신규):
  - structlog 설정: JSON 출력, timestamp, log_level
  - 개발환경: 컬러 콘솔 출력
  - 프로덕션: JSON 한 줄 출력

4-3. backend/app/middleware/request_id.py 생성 (신규):
  - 미들웨어: 각 요청에 X-Request-ID 헤더 추가 (uuid4)
  - structlog context에 request_id 바인딩
  - 응답 헤더에도 X-Request-ID 포함

4-4. backend/app/main.py:
  - structlog 초기화 (앱 시작 시)
  - RequestIDMiddleware 추가

⚠️ 기존 logging.info/warning/error 호출은 그대로 동작해야 함 (하위 호환)
⚠️ structlog는 stdlib logging과 통합 가능

=== 규칙 ===
- 테스트는 프로덕션 데이터/DB에 절대 접속 금지
- SQLite 호환 안 되는 테스트는 skip 마킹
- structlog 도입이 기존 로깅을 깨뜨리지 않을 것
- 새 파일 300줄 이내

=== 검증 ===
1. cd backend && pytest -v --tb=short → 전체 통과
2. cd backend && ruff check app/ tests/ → 0 issues
3. cd backend && python -c 'from app.main import app; print(app.title)'
4. cd backend && python -c 'import structlog; log = structlog.get_logger(); log.info(\"test\", key=\"value\")'
5. git add -A && git commit -m 'feat: Phase 49B pytest 기본 스위트 + 구조화 로깅' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- pytest 테스트 목록 + 결과 (pass/fail/skip)
- conftest.py 설정 요약
- CI 변경 내용
- structlog 설정 요약
- request_id 미들웨어 동작"