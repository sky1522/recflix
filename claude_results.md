# Phase 48B: Alembic 마이그레이션 + Dockerfile 체크섬

**날짜**: 2026-02-24

## 변경/생성 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/alembic.ini` | Alembic 설정 (신규, sqlalchemy.url 동적) |
| `backend/alembic/env.py` | 모델 로드 + settings.DATABASE_URL 연동 |
| `backend/alembic/versions/e2b032d303d8_*.py` | 초기 스냅샷 (빈 baseline, stamp용) |
| `backend/app/main.py` | `Base.metadata.create_all()` 제거 |
| `backend/Dockerfile` | 다운로드 파일 SHA256 체크섬 검증 추가 |

## Alembic 설정 구조

```
backend/
  alembic.ini          # sqlalchemy.url은 env.py에서 동적 설정
  alembic/
    env.py             # app.config.settings.DATABASE_URL 사용
    versions/
      e2b032d303d8_*.py  # baseline (빈 migration, stamp만)
```

**env.py 핵심**:
- `from app.database import Base` + `from app.models import *` → autogenerate 지원
- `config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)` → .env 기반

## 초기 리비전

- Revision ID: `e2b032d303d8`
- 내용: 빈 upgrade/downgrade (기존 DB에 stamp만)
- `alembic stamp head` 실행 완료 (로컬 DB)

## create_all 제거

- `Base.metadata.create_all(bind=engine)` 라인 제거
- `from app.database import Base, engine` import 제거
- 주석: `# Schema migrations managed by Alembic (alembic upgrade head)`

## Dockerfile 체크섬 추가

| 파일 | SHA256 |
|------|--------|
| `svd_model.pkl` | `343853948b2e84...` |
| `movie_embeddings.npy` | `e76cb82509c1be...` |
| `embedding_metadata.json` | `767501ded5a042...` |
| `movie_id_index.json` | `6c248d08dcc1ed...` |

패턴: `curl -fSL -o <file> <url> && echo "<hash>  <file>" | sha256sum -c -`

## 검증 결과

| 항목 | 결과 |
|------|------|
| `alembic heads` | e2b032d303d8 (head) |
| `from app.main import app` | 정상 (create_all 없이) |
| `ruff check app/ alembic/` | 0 issues |
