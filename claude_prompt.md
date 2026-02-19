# 범용 스킬 추가 & MCP 설정 업데이트

프로젝트의 코드 품질 원칙 스킬과 MCP 설정을 추가한다. 충분히 탐색하고 시작해.

먼저 읽을 것:
- CLAUDE.md (현재 규칙 섹션 확인)
- .claude/skills/INDEX.md (현재 스킬 목록 확인)
- .claude/settings.json (현재 MCP 설정 확인)

현재 코드 크기 문제 파악용:
- `find . -name '*.py' -o -name '*.tsx' -o -name '*.ts' | xargs wc -l | sort -rn | head -20`
- backend/app/api/v1/recommendations.py (770줄, calculate_hybrid_scores 133줄)
- frontend/app/movies/[id]/page.tsx (622줄)
- backend/app/services/weather.py (420줄)
- frontend/app/movies/page.tsx (436줄)
- frontend/lib/curationMessages.ts (415줄)
- frontend/components/layout/Header.tsx (373줄)

---

=== 1단계: .claude/settings.json 업데이트 ===

security-guidance MCP 추가:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic/context7-mcp"]
    },
    "security-guidance": {
      "command": "npx",
      "args": ["-y", "@anthropic/security-guidance-mcp"]
    }
  }
}
```

---

=== 2단계: .claude/skills/code-quality.md 생성 ===

목차형 원칙 유지. 실제 코드베이스를 탐색하여 500줄+ 파일 목록을 정확히 반영.

```markdown
# 코드 품질 원칙

## Karpathy 4원칙
1. **한 번에 하나만**: 각 함수/컴포넌트는 한 가지 역할만 수행
2. **작게 유지**: 파일 500줄 이하, 함수 50줄 이하
3. **명확한 이름**: 함수/변수명으로 역할이 드러나야 (약어 지양)
4. **부작용 최소화**: 순수 함수 선호, 상태 변경은 명시적으로

## 파일 크기 관리
- 500줄 이상: 분리 필수
- 300~499줄: 분리 검토
- 300줄 미만: 양호

### 분리 기준
- 역할별: 상수/유틸/컴포넌트/로직
- 도메인별: 추천/날씨/인증/영화
- 레이어별: UI/비즈니스 로직/데이터

### 현재 500줄+ 파일 (리팩토링 대상)
→ `find . -name '*.py' -o -name '*.tsx' -o -name '*.ts' | xargs wc -l | sort -rn | head -20` 으로 확인
- backend/app/api/v1/recommendations.py (770줄)
  - calculate_hybrid_scores() 133줄 → 스코어별 함수 분리
  - 가중치 상수, 태그 로직, 개인화 로직 분리 검토
- frontend/app/movies/[id]/page.tsx (622줄)
  - 히어로 배너, 상세 정보, 출연진, 유사 영화 → 서브 컴포넌트 분리 검토
(실제 탐색 결과로 이 목록을 업데이트해줘)

## 중복 제거
- 두 파일에서 같은 로직 발견 시 → 공통 유틸로 추출
- 매직넘버 → constants.ts 또는 Python 상수 모듈
- 캐시 키 → 중앙 관리 (frontend/lib/constants.ts)

## 함수 작성 규칙
- 함수 50줄 이하 (넘으면 헬퍼 분리)
- 인자 4개 이하 (넘으면 객체/DTO로 묶기)
- 중첩 3단계 이하 (넘으면 early return)
- 주석 대신 함수명으로 의도 표현

## 리팩토링 프로세스
1. Research: `find + wc -l` 로 500줄+ 파일 식별, 중복 검사
2. 우선순위: 저위험(유틸 추출) → 중위험(모듈 분리) → 고위험(구조 통합)
3. 실행: 기능 변경 없음 (순수 리팩토링), 각 단계 빌드 확인, 한 번에 한 파일

## Python 고유
- logging 사용 (print 금지) → Ruff T201 규칙
- ruff check + ruff format 통과
- 타입 힌트 필수 (함수 인자, 반환값)
- selectinload로 N+1 방지

## TypeScript 고유
- any 타입 사용 금지 → 구체적 타입 또는 unknown
- 모듈 레벨 mutable 변수 금지 → useRef/useState
- ESLint core-web-vitals 통과
- 상수는 constants.ts에서 import
```

---

=== 3단계: .claude/skills/INDEX.md 업데이트 ===

기존 테이블에 code-quality 행을 **workflow 바로 다음에** 추가:

```
| code-quality | Karpathy 4원칙, 파일 크기 관리, 중복 제거, 리팩토링 프로세스 |
```

---

=== 4단계: CLAUDE.md 규칙 섹션 보강 ===

기존 규칙에 아래 2개 추가 (기존 규칙 번호 뒤에 이어서):

```
N. 코드 품질: Karpathy 4원칙 준수 (파일 500줄↓, 함수 50줄↓, 단일 책임, 명확한 이름) → .claude/skills/code-quality.md 참조
N+1. any 타입 금지, Python 타입 힌트 필수 (함수 인자/반환값)
```

기존 규칙 번호 체계에 맞춰서 자연스럽게 삽입해줘.

---

=== 건드리지 말 것 ===
- 모든 소스 코드 파일 (*.py, *.tsx, *.ts, *.css)
- PROGRESS.md, CHANGELOG.md, PROJECT_CONTEXT.md, README.md, DEPLOYMENT.md, DECISION.md
- 기존 스킬 파일 7개 (workflow.md, recommendation.md, curation.md, weather.md, database.md, deployment.md, frontend-patterns.md)
- backend/.env, frontend/.env.local
- data/, node_modules/, __pycache__/

---

=== 검증 ===
- .claude/settings.json에 context7 + security-guidance 2개 MCP 존재 확인
- .claude/skills/code-quality.md 존재 + 500줄+ 파일 목록이 실제와 일치하는지 확인
- .claude/skills/INDEX.md에 code-quality 행 존재 확인
- CLAUDE.md에 Karpathy 원칙 규칙 존재 확인
- CLAUDE.md가 여전히 500줄 이하인지: `wc -l CLAUDE.md`

---

결과를 claude_results.md에 **기존 내용 아래에 --- 구분선 후 이어서** 저장:

```markdown
---

# 범용 스킬 추가 & MCP 설정 업데이트 결과

## 날짜
YYYY-MM-DD

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| .claude/skills/code-quality.md | Karpathy 원칙, 파일 크기, 중복 제거, 리팩토링 | N줄 |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| .claude/settings.json | security-guidance MCP 추가 |
| .claude/skills/INDEX.md | code-quality 스킬 추가 |
| CLAUDE.md | 규칙 섹션에 Karpathy 원칙, 타입 규칙 추가 |

## 500줄+ 파일 현황 (code-quality.md에 기록)
| 파일 | 줄 수 | 분리 방향 |
|------|-------|----------|
| (실제 탐색 결과) | ... | ... |

## 검증 결과
- .claude/settings.json: MCP 2개 ✅
- code-quality.md: 존재 ✅
- INDEX.md: code-quality 포함 ✅
- CLAUDE.md: N줄 (500줄 이하 ✅)
- 소스 코드 변경: 없음 ✅
```

git add -A && git commit -m 'docs: code-quality 스킬 추가, security-guidance MCP 설정' && git push origin HEAD:main