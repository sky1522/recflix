# Phase 36-2: CD 자동 배포 결과

## 날짜
2026-02-20

## 선택한 CD 방식

**방식 B: GitHub Actions에서 CI 통과 후 배포**

이유:
- CI 실패 시 배포 차단 (안전)
- PR에서는 CI만 실행, main push에서만 배포
- 단일 워크플로우에서 CI+CD 관리

## 워크플로우 구성 (`.github/workflows/ci.yml`)

```
CI/CD Pipeline
├── backend-lint (ruff 0.1.13, critical rules)
├── backend-typecheck (pyright, continue-on-error)
├── frontend-build (Node 20, npm ci && npm run build)
├── deploy-backend (Railway) ← needs: [backend-lint, frontend-build]
│   └── main push only, railway up --service backend
└── deploy-frontend (Vercel) ← needs: [backend-lint, frontend-build]
    └── main push only, vercel --prod
```

## GitHub Actions 실행 결과

| Job | 결과 | 비고 |
|-----|------|------|
| Backend Lint | SUCCESS | ruff 0.1.13 critical rules |
| Frontend Build | SUCCESS | Next.js 빌드 |
| Backend Type Check | FAILURE | continue-on-error (정보성) |
| Deploy Backend | FAILURE | RAILWAY_TOKEN 미설정 (예상) |
| Deploy Frontend | FAILURE | VERCEL_TOKEN 미설정 (예상) |

## 사용자가 수동으로 해야 할 설정

### 1. Railway 토큰 발급
1. [Railway Dashboard](https://railway.com) → Account Settings → Tokens
2. "Create Token" → 이름: `github-actions` → 생성
3. 토큰 복사

### 2. Vercel 토큰 발급
1. [Vercel Dashboard](https://vercel.com) → Settings → Tokens
2. "Create Token" → 이름: `github-actions`, Scope: Full Account → 생성
3. 토큰 복사

### 3. GitHub Secrets 등록
GitHub → `sky1522/recflix` → Settings → Secrets and variables → Actions → New repository secret

| Secret Name | 값 | 발급처 |
|-------------|-----|--------|
| `RAILWAY_TOKEN` | Railway API 토큰 | Railway Dashboard → Tokens |
| `VERCEL_TOKEN` | Vercel API 토큰 | Vercel Dashboard → Tokens |
| `VERCEL_ORG_ID` | `team_KpEtY3XBScahe0aRIDHhdv8D` | `frontend/.vercel/project.json` |
| `VERCEL_PROJECT_ID` | `prj_HrNkx74LTuaZ3z3ZWjF7qhfLd2vK` | `frontend/.vercel/project.json` |

### 4. Railway 대시보드 자동 배포 비활성화
Railway가 GitHub 연동 자동 배포가 켜져 있으면 중복 배포가 발생합니다:
- Railway Dashboard → Service → Settings → Source → "Automatic Deployments" OFF

## 설정 완료 후 검증 방법

1. 아무 파일에 사소한 변경 후 push to main
2. GitHub Actions 탭에서 CI/CD 워크플로우 확인
3. 5개 job 모두 성공 확인 (typecheck은 continue-on-error)
4. Railway 배포 로그 확인: `railway logs`
5. 프로덕션 헬스체크: `curl https://backend-production-cff2.up.railway.app/api/v1/health`
6. Vercel 배포 확인: `https://jnsquery-reflix.vercel.app` 접속

## 변경 파일

| 파일 | 변경 |
|------|------|
| `.github/workflows/ci.yml` | CI → CI/CD 확장, deploy-backend + deploy-frontend jobs 추가 |
