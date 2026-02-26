# Step 01D: 실험 그룹 결정론적 배정 + algorithm_version 레지스트리

> 작업일: 2026-02-26
> 목적: A/B 테스트를 위해 동일 사용자/세션이 항상 같은 그룹에 배정되도록 변경

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/api/v1/recommendation_constants.py` | GROUP_ALGORITHM_MAP, get_algorithm_version(), get_experiment_weights() 추가 |
| `backend/app/api/v1/recommendations.py` | get_deterministic_group() 추가, get_home_recommendations()에서 결정론적 배정 사용 |
| `frontend/lib/api.ts` | getSessionId() 추가, fetchAPI에 X-Session-ID 헤더 포함 |

## 결정론적 배정 로직

```
1. seed = str(user_id) if user_id else (session_id or "anonymous")
2. bucket = md5(seed) % 100
3. weights 순서대로 누적하여 bucket이 속하는 그룹 반환

예: weights = {control: 34, test_a: 33, test_b: 33}
   → bucket 0~33 → control
   → bucket 34~66 → test_a
   → bucket 67~99 → test_b
```

## GROUP_ALGORITHM_MAP 현재 값

```python
GROUP_ALGORITHM_MAP = {
    "control": "hybrid_v1",
    "test_a": "hybrid_v1_test_a",
    "test_b": "hybrid_v1_test_b",
}
```

## 프론트엔드 session_id 전송

- `getSessionId()`: localStorage에 `recflix_session_id` 키로 UUID 저장/재사용
- `fetchAPI()`: 모든 API 호출에 `X-Session-ID` 헤더 자동 포함
- SSR 환경(typeof window === "undefined")에서는 빈 문자열 → 헤더 미포함

## 기존 시스템과의 관계

- `_weighted_random_group()` (auth.py): 회원가입/OAuth 신규 유저 등록 시 사용 → **유지**
- `EXPERIMENT_WEIGHTS` 환경변수: get_experiment_weights()가 동일 포맷 파싱 → **재사용**
- 기존 get_weights_for_group 등 가중치 계산 로직: **미변경**

## 검증 결과

| 항목 | 결과 |
|------|------|
| 같은 user_id 5회 호출 → 같은 그룹 | OK (user_id=42 → 5회 test_b) |
| 비로그인 + 같은 session_id 5회 → 같은 그룹 | OK (session=abc123 → 5회 test_a) |
| 1000명 분포 (34:33:33 기대) | OK (35.0:31.0:34.0 근사) |
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |
| 프론트엔드 빌드 | OK |
