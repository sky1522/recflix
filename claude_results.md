# CI/CD 파이프라인 수정 결과

## 날짜
2026-02-20

## 수정 내용

### 1. deploy-frontend job 제거
- Vercel이 GitHub 연동으로 push 시 자동 배포 → Actions CD job 불필요 (이중 배포 방지)
- `deploy-frontend` job 전체 삭제

### 2. deploy-backend 개선
- `railway up --service backend` → `railway up --service backend --detach` (비동기 배포)
- RAILWAY_TOKEN 환경변수 참조 방식 확인: `${{ secrets.RAILWAY_TOKEN }}` (정상)

### 3. 주석 정리
- CD 섹션 주석에 Vercel 자동 배포 안내 추가

## 변경 파일
- `.github/workflows/ci.yml`: deploy-frontend 삭제, deploy-backend --detach 추가 (-31줄, +3줄)

## GitHub Actions 실행 결과 (커밋 `c8e59d6`)

| Job | 결과 | 비고 |
|-----|------|------|
| Backend Lint | **SUCCESS** | ruff 0.1.13 critical rules |
| Backend Type Check | FAILURE | continue-on-error (정보성) |
| Frontend Build | **SUCCESS** | Next.js 빌드 |
| Deploy Backend (Railway) | **FAILURE** | RAILWAY_TOKEN 미설정 |
| ~~Deploy Frontend (Vercel)~~ | **제거됨** | Vercel GitHub 자동 배포 사용 |

### Deploy Backend 실패 원인 + 해결 안내
- `RAILWAY_TOKEN` GitHub Secret이 미등록 상태
- Railway CLI가 인증 없이 `railway up` 실행 불가

**RAILWAY_TOKEN 등록 방법:**
1. Railway Dashboard → Project Settings → Tokens → Create Token
2. GitHub → Repository Settings → Secrets and variables → Actions
3. `RAILWAY_TOKEN` 이름으로 시크릿 등록
4. 다음 push 시 자동 배포 실행

### CI Jobs (3개) 정상 동작 확인
- `backend-lint`: ruff 0.1.13 critical rules (E9,F63,F7,F82) 통과
- `backend-typecheck`: pyright 타입 체크 (continue-on-error, 정보성)
- `frontend-build`: Next.js 빌드 성공

## 프로덕션 검증

### Backend 헬스체크
```json
{
  "status": "ok",
  "environment": "production",
  "database": "connected",
  "redis": "connected",
  "semantic_search": "enabled",
  "cf_model": "loaded",
  "version": "v1.0.0"
}
```

### Frontend
- `https://jnsquery-reflix.vercel.app` → HTTP 200 정상

## 최종 CI/CD 파이프라인 구조

```
Push to main
  ├── CI (항상 실행)
  │   ├── backend-lint (ruff critical rules)
  │   ├── backend-typecheck (pyright, 정보성)
  │   └── frontend-build (Next.js)
  │
  ├── CD (main push만)
  │   └── deploy-backend (Railway CLI, needs: lint+build)
  │
  └── Vercel 자동 배포 (GitHub 연동, Actions 외부)
```

## 남은 작업
1. GitHub Secrets에 `RAILWAY_TOKEN` 등록 → Deploy Backend 자동화 완성
