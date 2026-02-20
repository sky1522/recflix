claude "CI/CD 파이프라인 수정.

=== Research ===
- .github/workflows/ci.yml 전체 읽기
- deploy-backend job에서 RAILWAY_TOKEN 사용 방식 확인
- deploy-frontend job 확인

=== 수정 1: deploy-backend Railway 토큰 설정 확인 ===
deploy-backend job에서 RAILWAY_TOKEN 환경변수가 올바르게 참조되는지 확인:
- env 또는 steps 내에서 RAILWAY_TOKEN: \${{ secrets.RAILWAY_TOKEN }} 설정 확인
- railway up 명령에 --service 옵션이 올바른지 확인
- Railway CLI 인증 방식: RAILWAY_TOKEN 환경변수로 자동 인증되는지 확인

만약 railway up에 프로젝트/서비스 ID가 필요하면:
- railway link 또는 --project, --service 플래그 확인
- 필요한 추가 시크릿 (RAILWAY_PROJECT_ID, RAILWAY_SERVICE_ID) 식별

=== 수정 2: Vercel 이중 배포 제거 ===
Vercel이 GitHub 연동으로 이미 자동 배포하므로 deploy-frontend job 제거.
- deploy-frontend job 전체 삭제
- 또는 Vercel GitHub 자동 배포를 끄고 Actions만 사용
- Vercel 자동 배포가 더 간단하므로 job 제거 방향으로

=== 검증 ===
1. ci.yml 문법 검증
2. git add -A && git commit -m 'fix: CI/CD Railway 토큰 설정 수정 + Vercel 이중 배포 제거' && git push origin HEAD:main
3. GitHub Actions에서 deploy-backend 성공 확인

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- 수정 내용
- GitHub Actions 실행 결과 (5개 job 상태)
- deploy-backend 성공/실패 + 로그
- 실패 시 원인 + 추가 필요 시크릿 안내"