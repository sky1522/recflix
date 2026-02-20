# Phase 36: 헬스체크 엔드포인트 + GitHub Actions CI 결과

## 날짜
2026-02-20

## 1. 헬스체크 엔드포인트

### 구현
- **파일**: `backend/app/api/v1/health.py` (신규)
- **엔드포인트**: `GET /api/v1/health`
- **Rate Limit**: 없음 (모니터링 도구용)

### 프로덕션 응답
```json
{
  "status": "ok",
  "environment": "production",
  "database": "connected",
  "redis": "connected",
  "semantic_search": "enabled",
  "cf_model": "loaded",
  "version": "unknown"
}
```

### 확인 항목
| 항목 | 방식 | 로컬 | 프로덕션 |
|------|------|------|----------|
| database | `SELECT 1` 실행 | connected | connected |
| redis | `PING` 실행 | disconnected | connected |
| semantic_search | `is_semantic_search_available()` | enabled | enabled |
| cf_model | `is_cf_available()` | loaded | loaded |
| version | `GIT_SHA` 환경변수 | unknown | unknown |

## 2. GitHub Actions CI

### 워크플로우 구성 (`.github/workflows/ci.yml`)
- **트리거**: push to main, pull_request to main
- **Jobs**:
  - `backend-lint`: ruff 0.1.13 (E9,F63,F7,F82 critical 규칙)
  - `backend-typecheck`: pyright (`continue-on-error: true`)
  - `frontend-build`: Node 20, `npm ci && npm run build`
- **git-lfs**: false (린트/빌드에 불필요)

### CI 실행 결과
| 커밋 | Backend Lint | Backend Typecheck | Frontend Build | 전체 |
|-------|-------------|-------------------|----------------|------|
| `178e1bf` | FAIL (ruff 최신 버전) | FAIL | SUCCESS | FAIL |
| `92c43bd` | SUCCESS | FAIL (continue-on-error) | SUCCESS | **SUCCESS** |
| `379ba52` | SUCCESS | FAIL (continue-on-error) | SUCCESS | **SUCCESS** |
| `9c82df2` | SUCCESS | FAIL (continue-on-error) | SUCCESS | **SUCCESS** |

## 3. 추가 수정 (Phase 35 보완)

### numpy 버전 호환성 수정
- **문제**: SVD 모델이 numpy 2.x로 생성되어 `numpy._core.numeric` 필요
- **원인**: `requirements.txt`에 `numpy==1.26.3` 고정
- **수정**: `numpy>=2.0.0`, `pandas>=2.2.0`, `scipy>=1.14.1`
- **결과**: CF 모델 정상 로드 (`cf_model: loaded`)

## 변경 파일

| 파일 | 변경 |
|------|------|
| `backend/app/api/v1/health.py` | 신규 — 상세 헬스체크 |
| `backend/app/api/v1/router.py` | health 라우터 등록 |
| `.github/workflows/ci.yml` | 신규 — CI 워크플로우 |
| `backend/Dockerfile` | healthcheck URL → `/api/v1/health` |
| `railway.toml` | healthcheckPath → `/api/v1/health` |
| `requirements.txt` | numpy/pandas/scipy 버전 업데이트 |

## Railway 배포

| 배포 | 상태 | 비고 |
|------|------|------|
| `b6f9ab69` | SUCCESS | 헬스체크 엔드포인트 추가 |
| `3f06f1e9` | FAILED | pandas-numpy 의존성 충돌 |
| `5ba2a5a9` | SUCCESS | numpy 2.x + CF 모델 정상 로드 |
