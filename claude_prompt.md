claude "Phase 49A: 시맨틱 재랭킹 인기 편향 감소 + similar_movies 갱신 자동화.

=== Research ===
다음 파일들을 읽을 것:
- backend/app/api/v1/movies.py (시맨틱 검색 재랭킹 부분, 269번 라인 근처)
- backend/scripts/compute_similar_movies.py (유사 영화 계산 스크립트)
- backend/scripts/ 디렉토리 전체 확인

=== 1단계: 시맨틱 재랭킹 인기 편향 감소 ===
backend/app/api/v1/movies.py의 재랭킹 공식 수정:

현재: relevance = semantic × 0.50 + popularity × 0.30 + quality × 0.20
변경: relevance = semantic × 0.60 + popularity × 0.15 + quality × 0.25

추가: popularity 점수에 log 스케일 적용
- 현재 popularity 정규화 방식 확인
- min-max 정규화라면: log(1 + popularity) / log(1 + max_popularity) 로 변경
- 효과: 인기도 100 vs 10000의 차이를 압축 → 인디 영화 노출 증가

⚠️ 기존 정규화 로직을 읽고 이해한 후 수정
⚠️ 검색 결과 순서에 영향이 크므로 변경 내용 명확히 기록

=== 2단계: similar_movies 갱신 문서화 + 자동화 ===

2-1. backend/scripts/compute_similar_movies.py 읽고:
  - 현재 실행 방법 확인
  - 필요 환경변수 확인
  - 실행 시간 추정

2-2. backend/scripts/README.md 생성 (신규):
  - 전체 배치 스크립트 목록 + 설명 + 실행 방법
  - 권장 실행 주기:
    - collect_trailers.py: 월 1회 (신작 반영)
    - compute_similar_movies.py: 월 1회 (유사 영화 갱신)
    - llm_emotion_tags.py: 신작 추가 시
  - 환경변수 목록

2-3. GitHub Actions 워크플로우 (선택적, 가능하면):
  .github/workflows/data-refresh.yml
  - schedule: cron '0 3 1 * *' (매월 1일 03시)
  - 또는 workflow_dispatch (수동 트리거만)
  - similar_movies + trailers 갱신
  ⚠️ Railway DB 접속이 GitHub Actions에서 가능한지 확인 필요
  ⚠️ 불가능하면 문서화만 하고 워크플로우는 생략

=== 규칙 ===
- 재랭킹 공식 변경 시 기존 테스트/빌드 통과 필수
- scripts/README.md는 운영자 관점으로 작성
- 비즈니스 로직 외 변경 금지

=== 검증 ===
1. cd backend && ruff check app/ → 0 issues
2. cd backend && python -c 'from app.main import app; print(app.title)'
3. 재랭킹 공식 변경 확인 (코드 diff)
4. git add -A && git commit -m 'feat: Phase 49A 시맨틱 재랭킹 튜닝 + scripts 문서화' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- 재랭킹 공식 before/after
- popularity 정규화 변경 내용
- scripts/README.md 요약
- GitHub Actions 워크플로우 상태 (생성/생략 + 사유)"