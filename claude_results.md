# Step 03B: TwoTowerRetriever.retrieve() 예외 처리

> 작업일: 2026-02-27
> 목적: retrieve() 에러 시 500 방지 → 빈 리스트 반환 + fallback

## 수정 파일

| 파일 | 변경 |
|------|------|
| `backend/app/services/two_tower_retriever.py` | retrieve() 전체 try/except 래핑 |

## 변경 내용

- retrieve() 내부 전체를 `try/except Exception`으로 감싸고
- 에러 시 `logger.exception("two_tower_retrieve_failed")` 로그 + `return []`
- 호출자(recommendations.py)의 기존 `len(tt_candidates) < 20` 분기가 fallback 처리

## 검증 결과

| 항목 | 결과 |
|------|------|
| 정상 동작: 200개 후보 반환 | OK |
| 에러 시: 빈 리스트 + structlog 로그 | OK |
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |
