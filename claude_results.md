# CI/CD Railway 배포 실패 디버깅 결과

## 날짜
2026-02-20

## 실패 원인 분석

### 근본 원인
- 이전 `RAILWAY_TOKEN` (`f8e8303f-...`)이 유효하지 않은 토큰이었음
- Railway CLI 에러: `Invalid RAILWAY_TOKEN. Please check that it is valid and has access to the resource you're trying to use.`

### Railway 토큰 유형
| 유형 | 용도 | CI/CD 사용 |
|------|------|-----------|
| **Project Token** | 특정 프로젝트+환경 스코프 | **권장** |
| Account Token | 계정 전체 접근 | 비권장 (과도한 권한) |
| User Token (로컬) | 브라우저 OAuth 로그인 | CI/CD 불가 |

- `railway whoami`는 프로젝트 토큰에서 미지원 (User Token 전용)
- `railway status`로 프로젝트 토큰 유효성 검증 가능

## 수정 내용

### 1. Railway Project Token 교체
- Railway Dashboard → Project Settings → Tokens에서 새 토큰 생성
- GitHub Secrets API로 `RAILWAY_TOKEN` 시크릿 업데이트 (HTTP 204)

### 2. ci.yml 개선
- `railway up --service backend --environment production --detach`
- `--environment production`: 배포 환경 명시

## GitHub Actions 실행 결과 (커밋 `3f5fe06`)

| Job | 결과 | 비고 |
|-----|------|------|
| Backend Lint | **SUCCESS** | ruff 0.1.13 critical rules |
| Backend Type Check | FAILURE | continue-on-error (정보성) |
| Frontend Build | **SUCCESS** | Next.js 빌드 |
| Deploy Backend (Railway) | **SUCCESS** | Railway CD 자동 배포 성공! |

### Deploy Backend 성공 로그
- Install Railway CLI: npm 설치 성공
- Deploy to Railway: `railway up --service backend --environment production --detach` 성공

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
- Vercel GitHub 연동 자동 배포 정상 작동

## 최종 CI/CD 파이프라인 (완성)

```
Push to main
  ├── CI (항상 실행)
  │   ├── backend-lint (ruff critical rules) ── SUCCESS
  │   ├── backend-typecheck (pyright, 정보성) ── 정보성
  │   └── frontend-build (Next.js) ── SUCCESS
  │
  ├── CD (main push만, CI 통과 후)
  │   └── deploy-backend (Railway CLI) ── SUCCESS
  │
  └── Vercel 자동 배포 (GitHub 연동, Actions 외부) ── SUCCESS
```

## GitHub Secrets 현황
| Secret | 상태 |
|--------|------|
| `RAILWAY_TOKEN` | **등록 완료** (Project Token, production 스코프) |
