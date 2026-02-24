claude "Phase 50 보완: 프로젝트 문서/skills 최종 동기화.

=== Research ===
다음 파일들을 모두 읽을 것:
- README.md
- CHANGELOG.md
- PROGRESS.md
- CLAUDE.md
- docs/ARCHITECTURE.md
- docs/HANDOFF_CONTEXT.md
- docs/PROJECT_INDEX.md
- docs/RECOMMENDATION_LOGIC.md
- .claude/skills/ 전체 파일
- claude_results.md
- codex_results.md

그리고 현재 프로젝트 상태 확인:
- backend/app/api/v1/ 디렉토리 (라우터 목록)
- backend/app/models/ (모델 목록)
- backend/app/middleware/ (미들웨어)
- backend/app/core/ (security, rate_limit, http_client, logging_config)
- backend/tests/ (테스트 파일 목록)
- backend/alembic/ (마이그레이션)
- frontend/app/ (페이지 목록)
- frontend/components/ (컴포넌트 목록)
- frontend/types/index.ts (타입 정의)

=== 1단계: CLAUDE.md 업데이트 ===
Phase 46~50에서 추가/변경된 내용 반영:
- 신규 파일: http_client.py, logging_config.py, request_id.py, ErrorBoundary.tsx, TrailerModal.tsx, MovieTrailer.tsx, MovieFilters.tsx, MovieGrid.tsx, SearchResults.tsx, HeaderMobileDrawer.tsx, loading.tsx 3개, layout.tsx 6개
- 신규 디렉토리: backend/tests/, backend/alembic/, backend/app/middleware/
- DB 변경: movies.trailer_key 컬럼
- 의존성 추가: structlog, pytest, pytest-asyncio
- 삭제된 코드: Base.metadata.create_all
- 변경된 설정: Alembic 마이그레이션 체계

=== 2단계: docs/HANDOFF_CONTEXT.md 업데이트 ===
Phase 46~50 작업 반영:
- 완료 항목 업데이트
- 프로덕션 미반영 사항 정리 (있다면)
- 현재 기술 부채 / 스코프 아웃 항목 정리

=== 3단계: docs/PROJECT_INDEX.md 업데이트 ===
신규 생성된 파일/디렉토리 추가:
- backend/tests/
- backend/alembic/
- backend/app/middleware/
- backend/app/core/http_client.py
- backend/app/core/logging_config.py
- backend/scripts/README.md
- backend/scripts/collect_trailers.py
- backend/scripts/migrate_trailer.sql
- frontend 신규 컴포넌트들
- frontend 신규 layout.tsx/loading.tsx들

=== 4단계: docs/RECOMMENDATION_LOGIC.md 업데이트 ===
Phase 46~49 추천 로직 변경 반영:
- Section: 콜드스타트 — preferred_genres → personal_score 시드
- Section: 피드백 루프 — interaction_version 캐시 무효화
- Section: 시맨틱 재랭킹 v2 — 60/15/25 가중치 + log popularity
- 기존 섹션 업데이트 (가중치 등 변경된 수치)

=== 5단계: .claude/skills/ 최종 점검 ===
각 skill 파일을 읽고 Phase 38~50 전체 변경사항이 빠짐없이 반영됐는지 확인:
- workflow.md: Codex CLI + Claude Code 워크플로우
- recommendation.md: 전체 추천 파이프라인 최신 상태
- database.md: 모든 테이블/컬럼 최신 상태
- deployment.md: CI/CD, Alembic, structlog
- frontend-patterns.md: 모든 컴포넌트/훅 최신 상태
- code-quality.md: pytest, ruff, 타입 현황

누락된 내용이 있으면 추가. 이미 최신이면 변경하지 않음.

=== 6단계: PROGRESS.md 최종 확인 ===
Phase 1~50 전체가 완료 표시되어 있는지 확인.
향후 과제(스코프 아웃) 섹션이 로드맵과 일치하는지 확인.

=== 7단계: codex_results.md / claude_results.md 정리 ===
최종 상태를 깔끔하게 정리:
- claude_results.md: Phase 50 완료 요약으로 덮어쓰기
- codex_results.md: 마지막 조사 결과 유지 (참조용)

=== 규칙 ===
- 코드 변경 금지 (문서만)
- 기존 내용이 이미 최신이면 불필요한 수정 하지 않음
- 파일 간 정보 일관성 유지 (수치, 파일 목록 등)
- 간결하게 작성 (불필요한 반복 제거)

=== 검증 ===
1. 모든 .md 파일 마크다운 문법 오류 없음
2. CLAUDE.md의 파일 목록이 실제 파일과 일치
3. skills 파일의 정보가 실제 코드와 일치
4. git add -A && git commit -m 'docs: 프로젝트 문서 최종 동기화 (Phase 38-50)' && git push origin HEAD:main"