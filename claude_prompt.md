claude "CI/CD Railway 배포 실패 디버깅.

=== Research ===
1. .github/workflows/ci.yml 전체 읽기 — deploy-backend job 구조 확인
2. GitHub Actions 로그에서 deploy-backend 실패 원인 확인:
   - 'RAILWAY_TOKEN 미설정'인지 'project not found'인지 'service not found'인지
3. 로컬에서 railway 프로젝트 정보 확인:
   - cat .railway/config.json 또는 cat backend/.railway/config.json (있으면)
   - railway status (로컬에서 연결된 프로젝트/서비스 ID 확인)

=== 문제 분석 ===
railway up은 프로젝트/서비스 컨텍스트가 필요함.
로컬에서는 railway link로 연결되어 있지만, GitHub Actions에서는:
- RAILWAY_TOKEN만으로는 어떤 프로젝트에 배포할지 모름
- --service 또는 RAILWAY_PROJECT_ID + RAILWAY_SERVICE_ID 환경변수 필요

=== 수정 ===
deploy-backend job에 프로젝트/서비스 ID 추가:
env:
  RAILWAY_TOKEN: \${{ secrets.RAILWAY_TOKEN }}
  RAILWAY_PROJECT_ID: 실제_프로젝트_ID
  RAILWAY_SERVICE_ID: 실제_서비스_ID

프로젝트/서비스 ID 확인 방법:
- railway status 출력에서 확인
- 또는 Railway Dashboard URL에서 추출 (railway.com/project/PROJECT_ID/service/SERVICE_ID)

Vercel 이중 배포도 정리:
- deploy-frontend job 제거 (Vercel GitHub 연동이 이미 자동 배포)

=== 검증 ===
1. ci.yml 수정 후 push
2. GitHub Actions에서 deploy-backend 성공 확인
3. 프로덕션 헬스체크: curl https://backend-production-cff2.up.railway.app/api/v1/health

git add -A && git commit -m 'fix: Railway CD 프로젝트/서비스 ID 추가 + Vercel 이중 배포 제거' && git push origin HEAD:main

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- 실패 원인 분석
- 수정 내용
- GitHub Actions 실행 결과
- 추가 필요한 GitHub Secrets (있으면)"