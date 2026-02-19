# 워크플로우

## RPI 프로세스 (Research → Plan → Implement)

### 복잡한 작업 (3개+ 파일 수정, 원인 불명 버그, 새 기능)
1. **Research**: 관련 파일 열어서 구조 파악, grep 영향 범위, 유사 구현 패턴 검색
2. **Plan**: 수정 파일 목록 + 변경 함수/라인, 예상 부작용, 기존 패턴 재사용
3. **Implement**: 계획대로만 수정, 빌드 확인

### 간단한 작업 (1~2개 파일)
→ Research/Plan 생략 가능

## 디버깅: 2회 실패 규칙
같은 문제 2회 이상 실패 → Research부터 재시작, grep 전체 출력, 실패 원인 분석

## 컨텍스트 관리
- 500줄+ 파일은 grep으로 관련 함수만 (특히 recommendations.py 770줄)
- 스킬 파일 먼저 확인
- 한 번에 수정 3파일 이하
- 수정 전 기존 패턴 확인

## 검증
- Backend: `python -c "import ast; ast.parse(open('파일', encoding='utf-8').read())"` 또는 `ruff check`
- Frontend: `npx tsc --noEmit && npx next lint`
- 전체: 각 변경 후 빌드 확인
- Windows 주의: Bash에서 파일 경로는 `/c/dev/recflix/` 형식, Python 파일 읽기 시 `encoding='utf-8'` 명시

## 커밋 컨벤션
```
feat(scope): 새 기능
fix(scope): 버그 수정
refactor(scope): 코드 구조 변경
docs: 문서/스킬 변경
chore: 설정/빌드/의존성
```
