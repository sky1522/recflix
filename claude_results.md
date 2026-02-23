# Phase 40: 프로젝트 설정 경량화 및 고도화 — 결과

## 날짜
2026-02-23

## 변경 파일 목록

| # | 파일 | 주요 변경 |
|---|------|----------|
| 1 | `.claude/skills/workflow.md` | outdated LOC 참조 수정 (770줄→300줄+ 기준) |
| 2 | `.claude/skills/recommendation.md` | diversity.py, semantic_search.py, recommendation_reason.py 추가 + 3개 섹션 신규 |
| 3 | `.claude/skills/database.md` | users 17컬럼 + user_events 테이블 섹션 추가, 모델 수 8→9 |
| 4 | `.claude/skills/deployment.md` | CI/CD 파이프라인 섹션 추가 (.github/workflows/ci.yml) |
| 5 | `.claude/skills/frontend-patterns.md` | useImpressionTracker + eventTracker.ts 추가 |
| 6 | `.claude/skills/code-quality.md` | 500줄+ 파일 목록 갱신 (리팩토링 완료 반영), 300-499줄 목록 갱신 |
| 7 | `CLAUDE.md` | LOC 수정 (recommendations.py 347→412, engine 330→396, movies/[id] 622→263), DB 복원 명령 skills 위임 |
| 8 | `docs/PROJECT_INDEX.md` | HANDOFF_CONTEXT.md 누락 추가 |

## 단계별 상세

### 1단계: .claude/skills/ 정리 (6개 파일 수정)

**workflow.md**: `500줄+ 파일은 grep으로 관련 함수만 (특히 recommendations.py 770줄)` → `300줄+ 파일은 grep으로 관련 함수만` (Phase 28에서 recommendations.py가 5개 모듈로 분리됨)

**recommendation.md**: 핵심 파일에 3개 추가 (recommendation_reason.py, diversity.py, semantic_search.py), 다양성 후처리/추천 이유/시맨틱 검색 섹션 추가, 체크리스트 7→8항목

**database.md**: users 테이블 17컬럼 상세 (인증/소셜/개인화/A/B), user_events 테이블 (10종 이벤트, 5개 인덱스), 모델 수 8→9개

**deployment.md**: CI/CD 파이프라인 섹션 신규 (GitHub Actions CI + Railway CD + Vercel 자동), 배포 프로세스 문구 업데이트

**frontend-patterns.md**: hooks 목록에 useImpressionTracker 추가, 핵심 파일에 eventTracker.ts 추가

**code-quality.md**: 500줄+ 목록 갱신:
- 제거: recommendations.py (770→412줄), movies/[id]/page.tsx (622→263줄) — Phase 28 리팩토링 완료
- 추가: movies/page.tsx (531줄), SearchAutocomplete.tsx (522줄)
- 300-499줄 목록에 recommendations.py (412줄) 추가, SearchAutocomplete.tsx 제거

### 2단계: CLAUDE.md 경량화 (3개 수정)
- recommendations.py LOC: 347→412
- recommendation_engine.py LOC: 330→396
- movies/[id]/page.tsx LOC: 622→263
- DB 복원 명령어: 상세 → `.claude/skills/database.md 참조`로 위임

### 3단계: frontend/hooks/ 분석 (변경 없음)
4개 훅 모두 양호:
- useWeather.ts (237줄): localStorage TTL 캐시, Geolocation fallback, 타입 안전
- useInfiniteScroll.ts (82줄): IntersectionObserver cleanup 정상, ref로 stale closure 방지
- useDebounce.ts (25줄): 제네릭 타입, cleanup 정상
- useImpressionTracker.ts (47줄): observe-once 패턴, disconnect 정상
- `any` 타입 사용 없음, 불필요한 리렌더링 패턴 없음

### 4단계: docs/ 정리 (1개 수정)
- docs/PROJECT_INDEX.md에 HANDOFF_CONTEXT.md 누락 → 추가
- HANDOFF_CONTEXT.md vs PROGRESS.md: 역할 구분 명확 (핸드오프 컨텍스트 vs 상세 진행기록)
- 중복 문서 없음

### 5단계: Lint/Hooks 설정 확인 (변경 없음)
- `.husky/`: 미설정 (pre-commit hook 없음, 도입 검토만)
- `frontend/.eslintrc.json`: `next/core-web-vitals` — 최소한 설정, 적절
- `pyproject.toml` ruff: E,W,F,I,B,UP,T20,SIM 규칙, E501/B008 무시 — 적절
- 기존 ruff 이슈 13개 (E501 5개, F401 4개, E402 3개, UP 계열): 모두 pre-existing, Phase 40 범위 외

## 검증 결과
- `ruff check app/ --select E,F,W`: 13개 기존 이슈 (Phase 40 변경 없음)
- `npx tsc --noEmit`: 통과
- `npm run build`: 성공 (모든 페이지 빌드 완료)
