# 프로젝트 문서 동기화

$ARGUMENTS 를 기반으로 프로젝트 문서를 현재 코드와 동기화한다.

## 대상
CLAUDE.md, PROGRESS.md, .claude/skills/, docs/

## Phase 1: 조사 (수정 금지)
1. `git log --oneline -20` 최근 커밋
2. 각 문서의 마지막 업데이트 시점
3. 실제 코드와 문서 내용 비교
4. 갭 목록 → `claude_results.md`

## Phase 2: 수정 (갭 목록 보고 후 진행)
1. 갭 기반 업데이트
2. 기존 내용 보존 + 변경/신규만 추가
3. 기존 포맷 유지

```bash
git add -A && git commit -m 'docs: 프로젝트 문서 동기화' && git push origin HEAD:main
```
