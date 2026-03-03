# Vercel 자동 배포 미동작 조사 + 복구 결과

> 작업일: 2026-03-03

## 원인

커밋 `c8e59d6` (2026-02-20)에서 `deploy-frontend` CI/CD job이 삭제됨:
- 삭제 사유: "Vercel GitHub 연동 자동 배포 사용"
- 하지만 Vercel GitHub App 연동은 **설정된 적이 없음**
- 증거: GitHub Deployments API에 Vercel 배포 기록 0건, Railway만 존재
- 이후 프론트엔드는 수동 `npx vercel --prod`에만 의존

## 해결: CI/CD에 deploy-frontend job 복원

### 변경 파일
| 파일 | 변경 내용 |
|------|-----------|
| `.github/workflows/ci.yml` | `deploy-frontend` job 추가 (Vercel CLI `--prod --token`) |

### 필수 GitHub Secrets 등록

GitHub → Settings → Secrets → Actions에 아래 3개 등록 필요:

| Secret | 값 | 확인 방법 |
|--------|-----|-----------|
| `VERCEL_TOKEN` | Vercel Personal Access Token | https://vercel.com/account/tokens → Create Token |
| `VERCEL_ORG_ID` | `team_KpEtY3XBScahe0aRIDHhdv8D` | `frontend/.vercel/project.json`에서 확인 |
| `VERCEL_PROJECT_ID` | `prj_HrNkx74LTuaZ3z3ZWjF7qhfLd2vK` | `frontend/.vercel/project.json`에서 확인 |

### deploy-frontend job 상세
```yaml
deploy-frontend:
  name: Deploy Frontend (Vercel)
  needs: [backend-lint, backend-test, frontend-build]
  runs-on: ubuntu-latest
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: "20"
    - name: Deploy to Vercel
      run: cd frontend && npx vercel --prod --token $VERCEL_TOKEN
      env:
        VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
        VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
        VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}
```

## 동작 흐름
1. `git push origin main`
2. GitHub Actions CI: backend-lint + backend-test + frontend-build
3. CI 통과 시:
   - `deploy-backend`: Railway CLI → 백엔드 배포
   - `deploy-frontend`: Vercel CLI → 프론트엔드 배포 (병렬)

## 주의: Secrets 미등록 시
- `deploy-frontend` job은 실패하지만 다른 CI job에는 영향 없음
- Secrets 등록 전까지는 기존처럼 `cd frontend && npx vercel --prod` 수동 배포 사용
