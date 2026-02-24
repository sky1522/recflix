claude "Phase 48B: Alembic 마이그레이션 도입 + Dockerfile 체크섬 검증.

=== Research ===
다음 파일들을 읽을 것:
- backend/app/main.py (create_all 위치)
- backend/app/database.py (엔진/세션 설정)
- backend/app/models/ 전체 (모든 모델 import 확인)
- backend/requirements.txt (alembic 포함 여부)
- backend/Dockerfile (curl 다운로드 부분)

=== 1단계: Alembic 초기화 ===

1-1. cd backend && alembic init alembic
  (alembic이 requirements.txt에 있는지 확인, 없으면 추가)

1-2. backend/alembic.ini 수정:
  - sqlalchemy.url은 비워두고 env.py에서 동적 설정

1-3. backend/alembic/env.py 수정:
  - from app.database import Base
  - from app.models import * (모든 모델 로드)
  - from app.core.config import settings
  - config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
  - target_metadata = Base.metadata

1-4. 초기 마이그레이션 생성 (현재 스키마 스냅샷):
  alembic revision --autogenerate -m "initial schema snapshot"
  ⚠️ 이미 테이블이 존재하므로 이 리비전은 스탬프만:
  alembic stamp head

=== 2단계: create_all 제거 ===

2-1. backend/app/main.py:
  - Base.metadata.create_all(bind=engine) 라인 제거
  - 주석으로 'Alembic manages schema migrations' 추가

=== 3단계: Dockerfile 체크섬 검증 ===

3-1. backend/Dockerfile의 curl 다운로드 부분에 SHA256 체크섬 추가:
  - 현재 다운로드 파일 목록 확인
  - 각 파일의 SHA256 해시 계산 (로컬에서)
  - Dockerfile에 검증 추가:
    RUN curl -L -o model.pkl https://... && \
        echo "expected_hash  model.pkl" | sha256sum -c -

⚠️ 해시값은 실제 파일을 다운로드해서 계산해야 함
⚠️ 다운로드 URL이 변경 불가능한(immutable) 경로인지 확인

=== 규칙 ===
- Alembic 초기 리비전은 stamp만 (이미 존재하는 DB에 적용하지 않음)
- create_all 제거 후에도 앱 정상 시작 확인
- Dockerfile 체크섬은 빌드 실패 시 명확한 에러 메시지

=== 검증 ===
1. cd backend && alembic check (또는 alembic heads)
2. cd backend && python -c 'from app.main import app; print(app.title)' (create_all 없이)
3. cd backend && ruff check app/ alembic/ → 0 issues
4. Dockerfile 문법 확인 (docker build --check 또는 hadolint)
5. git add -A && git commit -m 'chore: Phase 48B Alembic 마이그레이션 + Dockerfile 체크섬' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- Alembic 설정 구조
- 초기 리비전 정보
- create_all 제거 확인
- Dockerfile 체크섬 추가 내역"