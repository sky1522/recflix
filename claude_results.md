# Step 01C CRITICAL: reco_* INSERT를 user_events와 트랜잭션 분리

> 작업일: 2026-02-26
> 목적: reco_* 삽입 실패 시 user_events까지 롤백되는 문제 해결

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/api/v1/events.py` | 배치 핸들러의 트랜잭션을 2단계로 분리 |

## 트랜잭션 분리 구조

```
기존 (문제):
  try:
    db.add_all(user_events + reco_records)  ← 동일 트랜잭션
    db.commit()
  except:
    db.rollback()  ← reco_* 실패 시 user_events도 롤백!

수정 후:
  # 1단계: user_events 저장 (최우선, 기존 로직)
  try:
    db.add_all(user_events)
    db.commit()  ← user_events 먼저 확정
  except:
    db.rollback()
    return  ← user_events 실패 시 여기서 종료

  # 2단계: reco_* 저장 (실패해도 user_events에 영향 없음)
  try:
    reco_interactions 벌크 INSERT
    reco_judgments 벌크 INSERT
    db.commit()
  except:
    db.rollback()
    logger.error(...)  ← 에러 로그만 남기고 조용히 통과
```

## 추가 개선: ORM → Core 벌크 INSERT

reco_* 저장을 ORM `db.add_all()` 대신 SQLAlchemy Core `__table__.insert()`로 변경:
- dict 리스트를 이벤트 순회 시 수집
- user_events commit 이후 한번에 벌크 INSERT
- 더 효율적이고, ORM 객체 생성 오버헤드 없음

## 검증 결과

| 항목 | 결과 |
|------|------|
| 정상 케이스 (user_events + reco_* 모두 저장) | OK |
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |
