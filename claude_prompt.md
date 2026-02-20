claude "Phase 35: SVD 모델 프로덕션 배포 — Research + 구현.

=== Research ===
먼저 다음을 확인할 것:
- backend/app/api/v1/recommendation_engine.py (CF 관련 코드 — SVD 모델 로드, CF 점수 계산 부분)
- backend/app/api/v1/recommendation_constants.py (CF 가중치 설정)
- backend/data/ 디렉토리 구조 확인
- SVD 모델 파일 위치 찾기: dir /s /b *.pkl 또는 find . -name '*.pkl' -o -name '*.pickle'
- .gitignore에서 pkl/pickle 관련 라인 확인
- git lfs ls-files (현재 lfs 추적 파일 확인)

=== 현재 상태 파악 ===
1. SVD 모델 파일이 어디에 있는지 (로컬 경로)
2. 파일 크기 확인
3. recommendation_engine.py에서 모델을 어떻게 로드하는지 (경로, fallback 처리)
4. CF가 비활성일 때 어떤 fallback 가중치를 쓰는지
5. CF 활성 시 하이브리드 스코어링에서 CF의 가중치가 얼마인지

=== 구현 ===

1. SVD 모델 파일을 git-lfs로 추적:
   - git lfs track 'backend/data/**/*.pkl' (또는 실제 파일 경로에 맞게)
   - .gitignore에서 해당 파일 차단 해제

2. 관련 데이터 파일도 포함:
   - MovieLens 매핑 파일이나 tmdb_id 매핑이 있으면 같이 포함
   - 모델이 의존하는 데이터 파일 모두 확인

3. git add + commit + push

4. Railway 재배포:
   - railway up
   - 서버 로그에서 SVD 모델 로드 성공 확인
   - CF 활성화 로그 확인

5. 프로덕션 테스트:
   - 로그인한 사용자로 /recommendations/for-you 호출
   - CF 점수가 반영되는지 확인 (응답에 CF 관련 태그나 점수 표시)
   - 또는 /recommendations 홈 추천에서 CF 반영 확인

=== 규칙 ===
- recommendation_engine.py의 CF 로직 수정 금지 (이미 구현되어 있음)
- 모델 파일 배포만 수행
- CF 모델 로드 실패 시 기존 fallback이 동작하는지 확인
- .md 문서 파일 건드리지 말 것

=== 검증 ===
1. git lfs ls-files — SVD 모델 파일이 lfs 추적 중인지
2. 로컬 서버에서 CF 활성화 확인 (로그)
3. 프로덕션 Railway에서 CF 활성화 확인 (로그)
4. 프로덕션 API 호출 — CF 비활성 때와 결과가 다른지 비교
5. git add -A && git commit -m 'feat: Phase 35 SVD 모델 프로덕션 배포 (git-lfs)' && git push origin HEAD:main

결과를 claude_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기):
- SVD 모델 파일 경로/크기
- git-lfs 설정 결과
- CF 활성화 전/후 추천 결과 비교
- 프로덕션 배포 결과"