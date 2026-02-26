# Step 01D CRITICAL: experiment_group 일관성 확보

> 작업일: 2026-02-26
> 목적: 결정론적 그룹 배정과 스코어링/로깅 간의 experiment_group 불일치 해소

## 문제

`get_home_recommendations()`에서:
- **그룹 배정 (로깅)**: `get_deterministic_group()` → 결정론적 그룹
- **스코어링**: `current_user.experiment_group` → DB 저장값 (회원가입 시 랜덤 배정)
- 두 값이 다를 수 있어 "로그에는 test_a인데 실제로는 control 가중치로 추천" 발생 가능

## 변경 파일

| 파일 | 변경 위치 | 변경 내용 |
|------|-----------|-----------|
| `backend/app/api/v1/recommendations.py` | L114 | `calculate_hybrid_scores(experiment_group=current_user.experiment_group)` → `experiment_group=experiment_group` |
| `backend/app/api/v1/recommendations.py` | L318~342 | `/hybrid` 엔드포인트에도 `get_deterministic_group()` 추가, `current_user.experiment_group` 대체 |

## 변경 전/후 experiment_group 흐름 비교

### 변경 전 (`get_home_recommendations`)
```
experiment_group(결정론적) ─→ log_impressions()     ← 그룹 A
current_user.experiment_group ─→ calculate_hybrid_scores() ← 그룹 B (다를 수 있음!)
```

### 변경 후
```
experiment_group(결정론적) ─→ log_impressions()          ← 그룹 A
experiment_group(결정론적) ─→ calculate_hybrid_scores()  ← 그룹 A (동일!)
```

### 변경 전 (`/hybrid` 엔드포인트)
```
current_user.experiment_group ─→ calculate_hybrid_scores() ← DB 값 (랜덤 배정)
```

### 변경 후
```
get_deterministic_group() ─→ calculate_hybrid_scores() ← 결정론적 (일관)
```

## 기존 시스템 미변경 사항
- `current_user.experiment_group` DB 컬럼: 미수정 (회원가입 시 참고용 유지)
- `calculate_hybrid_scores()` 함수 시그니처: 미변경 (호출 인자만 변경)
- `auth.py` 회원가입 그룹 배정: 미변경

## 검증 결과

| 항목 | 결과 |
|------|------|
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |
| 프론트엔드 빌드 영향 | 없음 (백엔드만 변경) |
