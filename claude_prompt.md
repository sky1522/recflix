claude "Phase 40: 프로젝트 설정 경량화 및 고도화 — md/skills/hooks 정리.

=== Research ===
먼저 다음을 읽고 현재 상태를 파악할 것:
- CLAUDE.md (전체)
- .claude/skills/ 디렉토리 전체 구조 + 각 스킬 파일 내용
- .claude/settings.json 또는 .claude/config 등 설정 파일
- .gitignore
- frontend/hooks/ 디렉토리 전체 (useWeather.ts, useInfiniteScroll.ts, useDebounce.ts, useImpressionTracker.ts)
- docs/ 디렉토리 전체 목록

=== 1단계: .claude/skills/ 정리 ===
각 스킬 파일을 읽고 분석:
- 중복되는 내용이 있으면 통합
- outdated된 정보 (Phase 33~38 이전 기준) 업데이트
- 실제 코드와 불일치하는 내용 수정
- INDEX.md가 실제 스킬 파일과 일치하는지 확인, 불일치 시 수정
- 각 스킬 파일이 100줄 이내인지 확인, 초과 시 핵심만 남기고 압축

=== 2단계: CLAUDE.md 경량화 ===
현재 CLAUDE.md를 분석:
- skills/ 파일과 중복되는 상세 내용을 skills로 위임하고 CLAUDE.md에서는 요약만 유지
- 핵심 구조 섹션: 실제 존재하는 파일만 남기고, 삭제된 파일 제거
- 규칙 섹션: 중복/모호한 규칙 통합
- 알려진 이슈 패턴: 해결 완료된 이슈 중 더 이상 재발 가능성 없는 것 제거
- 목표: CLAUDE.md가 프로젝트 진입점으로서 간결하고 정확하게

=== 3단계: frontend/hooks/ 고도화 ===
각 훅을 읽고 분석:
- useWeather.ts: localStorage 캐시 전략 적절한지, 에러 핸들링, 타입 안전성
- useInfiniteScroll.ts: IntersectionObserver 정리(cleanup), 메모리 누수 가능성
- useDebounce.ts: 제네릭 타입 활용, cleanup 로직
- useImpressionTracker.ts: IntersectionObserver 임계값, 배치 전송 효율성
- 공통 패턴이 있으면 추출 가능한지 확인
- 불필요한 리렌더링 유발하는 패턴 수정 (의존성 배열 검증)
- any 타입 사용 시 적절한 타입으로 교체

=== 4단계: docs/ 정리 ===
docs/ 내 파일 목록 확인:
- 중복 문서 식별 (HANDOFF_CONTEXT.md vs PROGRESS.md 등 겹치는 내용)
- 각 문서의 역할이 명확한지 확인
- PROJECT_INDEX.md가 실제 docs/ 파일과 일치하는지 확인

=== 5단계: Git hooks / 린트 설정 확인 ===
- .husky/ 디렉토리 존재 여부 확인
- pre-commit hook 유무 → 없으면 lint-staged + husky 도입 검토 (설치는 하지 말고 검토만)
- frontend/eslintrc 또는 eslint.config: 불필요한 규칙 비활성화 여부
- backend/ruff.toml 또는 pyproject.toml의 ruff 설정: 규칙 최적화 여부

=== 규칙 ===
- 기능 로직(.py 비즈니스 로직, .tsx 컴포넌트 로직) 수정 금지
- hooks는 버그/타입/성능만 수정, 동작 변경 금지
- 삭제 시에는 반드시 사유 주석으로 기록
- skills 파일은 실제 코드 기준 팩트만 기술

=== 검증 ===
1. cd backend && ruff check app/ --select E,F,W
2. cd frontend && npx tsc --noEmit
3. cd frontend && npm run build
4. 변경 파일 목록 + 각 파일 변경 요약
5. git add -A && git commit -m 'chore: Phase 40 설정 경량화 및 고도화 (skills/hooks/docs)' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기."