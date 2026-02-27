# 배포

## 핵심 파일
→ `DEPLOYMENT.md` (상세 배포 가이드)
→ `backend/railway.toml`
→ `frontend/vercel.json`
→ `.github/workflows/ci.yml` (CI/CD 파이프라인)

## 프로덕션 URL
| 서비스 | URL |
|--------|-----|
| Frontend | https://jnsquery-reflix.vercel.app |
| Backend API | https://backend-production-cff2.up.railway.app |
| API Docs | https://backend-production-cff2.up.railway.app/docs |
| GitHub | https://github.com/sky1522/recflix |

## 환경변수
→ `backend/.env.example`, `frontend/.env.example` 참조

### Backend 필수 환경변수
- `DATABASE_URL`: PostgreSQL 연결 URL
- `REDIS_URL` / `REDIS_PASSWORD`: Redis 연결
- `JWT_SECRET_KEY`: JWT 시크릿
- `OPENWEATHER_API_KEY`: OpenWeatherMap API
- `ANTHROPIC_API_KEY`: Claude API (캐치프레이즈)
- `CORS_ORIGINS`: 허용 도메인 (쉼표 구분)
- `TWO_TOWER_ENABLED`: Two-Tower 활성화 (default: true)
- `RERANKER_ENABLED`: LGBM 재랭커 활성화 (default: true)
- `EXPERIMENT_WEIGHTS`: A/B 그룹 비율 (default: control:34,test_a:33,test_b:33)

### Frontend 필수 환경변수
- `NEXT_PUBLIC_API_URL`: Backend API URL

## CI/CD 파이프라인
→ `.github/workflows/ci.yml` 참조
- **CI**: GitHub Actions — Backend Lint (ruff) + Backend Test (pytest, ML 패키지 제외) + Frontend Build (next build)
- **CD**: GitHub Actions → `npx @railway/cli@4.30.5 up --service backend --environment production --detach`
- **Vercel**: GitHub 연동 자동 배포 (push 시, Actions 불필요)
- **Railway Token**: Project Token 사용 (Account Token 아님), GitHub Secrets `RAILWAY_TOKEN`
- **deploy-backend needs**: backend-lint + backend-test + frontend-build (모두 통과 필수)
- **CI ML 제외**: `grep -v 'torch==\|lightgbm\|faiss-cpu'` → requirements-ci.txt
- **CI 환경변수**: DATABASE_URL, JWT_SECRET_KEY (Settings 검증용)
- **Lazy imports**: torch/faiss/lightgbm는 클래스 __init__에서만 import (CI 호환)

## 구조화 로깅 (Phase 49)
→ `backend/app/core/logging_config.py` — structlog 설정
→ Production: JSON one-line, Development: colored console
→ `backend/app/middleware/request_id.py` — X-Request-ID 미들웨어

## Dockerfile 모델 다운로드 (Phase 48 + 53)
→ v1.0: svd_model.pkl, movie_embeddings.npy, embedding_metadata.json, movie_id_index.json
→ v2.0: model_v1.pt, faiss_index.bin, item_embeddings_tt.npy, movie_id_map.json, lgbm_v1.txt
→ 모두 SHA256 무결성 검증, GitHub LFS media URL에서 다운로드
→ `.railwayignore`로 로컬 `railway up` 시 모델 파일 업로드 제외 (413 방지)

## 배포 프로세스
- main 브랜치 push → CI/CD → Railway/Vercel 자동 배포
- CORS: `backend/app/config.py`의 `CORS_ORIGINS`에 도메인 추가

## DB 마이그레이션
→ `DEPLOYMENT.md`의 마이그레이션 섹션 참조
```bash
# 로컬 → Railway
PGPASSWORD=recflix123 pg_dump -h localhost -U recflix -d recflix --no-owner --no-acl -Fc -f dump.dump
PGPASSWORD=<railway_pw> pg_restore -h shinkansen.proxy.rlwy.net -p 20053 -U postgres -d railway --clean --if-exists --no-owner --no-acl dump.dump
```

## 배포 시 체크리스트
1. 로컬 빌드 성공 확인
2. 환경변수 누락 확인
3. CORS_ORIGINS 확인
4. `git push origin HEAD:main` → 자동 배포
5. `/health` 엔드포인트 확인
6. 프론트엔드 주요 기능 수동 확인
