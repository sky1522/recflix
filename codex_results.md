# Step 01D Review — 실험 라우팅 확정 + algorithm_version 체계

## Findings (Severity Order)

### CRITICAL
1. 결정론적 라우팅으로 계산한 `experiment_group`과 실제 점수 계산에 사용되는 그룹이 불일치합니다.
- `get_home_recommendations`에서 `experiment_group = get_deterministic_group(...)`로 그룹을 결정하고 `algorithm_version = get_algorithm_version(experiment_group)`를 생성하지만, 하이브리드 스코어 계산 호출은 `experiment_group=current_user.experiment_group`를 사용합니다.
- 동일 함수 내에서 impression 로깅은 다시 `experiment_group=experiment_group`(결정론적 그룹)으로 기록합니다.
- 결과적으로 “노출 로그/algorithm_version”과 “실제 추천 가중치”가 서로 다른 그룹 기준이 될 수 있어 실험 해석이 깨질 수 있습니다.
- 근거: `backend/app/api/v1/recommendations.py:80`, `backend/app/api/v1/recommendations.py:85`, `backend/app/api/v1/recommendations.py:114`, `backend/app/api/v1/recommendations.py:293`, `backend/app/api/v1/recommendations.py:335`

### WARNING
- 없음

### INFO
- 없음

## 체크리스트 검증

### 결정론적 배정
- [x] `get_deterministic_group()`이 동일 user_id에 대해 항상 같은 그룹 반환
  - 근거: `backend/app/api/v1/recommendations.py:54`, `backend/app/api/v1/recommendations.py:55`, `backend/app/api/v1/recommendations.py:56`, `backend/app/api/v1/recommendations.py:59`
- [x] user_id가 None일 때 session_id를 seed로 사용
  - 근거: `backend/app/api/v1/recommendations.py:54`
- [x] user_id와 session_id 모두 None일 때 fallback("anonymous") 처리
  - 근거: `backend/app/api/v1/recommendations.py:54`
- [x] md5 해시 → bucket(0~99) → weights 누적 비교 로직 정확
  - 근거: `backend/app/api/v1/recommendations.py:55`, `backend/app/api/v1/recommendations.py:56`, `backend/app/api/v1/recommendations.py:59`
- [x] 기존 `_weighted_random_group()`이 삭제되지 않고 유지
  - 근거: `backend/app/api/v1/auth.py:43`, `backend/app/api/v1/auth.py:121`, `backend/app/api/v1/auth.py:350`, `backend/app/api/v1/auth.py:434`

### algorithm_version 레지스트리
- [x] `GROUP_ALGORITHM_MAP`이 코드 상수로 선언
  - 근거: `backend/app/api/v1/recommendation_constants.py:124`
- [x] `get_algorithm_version()`이 맵에 없는 그룹에 대해 안전한 기본값 반환
  - 근거: `backend/app/api/v1/recommendation_constants.py:133`
- [x] recommendations.py에서 algorithm_version을 레지스트리에서 가져옴
  - 근거: `backend/app/api/v1/recommendations.py:85`

### 프론트엔드 session_id
- [x] localStorage에 session_id 저장/재사용
  - 근거: `frontend/lib/api.ts:25`, `frontend/lib/api.ts:28`
- [x] SSR 환경(window undefined)에서 에러 없이 동작
  - 근거: `frontend/lib/api.ts:24`, `frontend/lib/api.ts:64`
- [x] fetchAPI 호출 경로에서 X-Session-ID 헤더 주입 로직 포함
  - 근거: `frontend/lib/api.ts:65`, `frontend/lib/api.ts:75`, `frontend/lib/api.ts:76`
- [x] 기존 fetchAPI 동작(인증 헤더, timeout, retry) 미변경
  - 근거: `frontend/lib/api.ts:18`, `frontend/lib/api.ts:20`, `frontend/lib/api.ts:73`, `frontend/lib/api.ts:95`, `frontend/lib/api.ts:96`

### 하위 호환성
- [x] `EXPERIMENT_WEIGHTS` 환경변수 체계 유지
  - 근거: `backend/app/api/v1/recommendation_constants.py:136`, `backend/app/api/v1/recommendation_constants.py:142`
- [x] `get_weights_for_group()` 등 기존 가중치 로직 유지
  - 근거: `backend/app/api/v1/recommendation_engine.py:55`, `backend/app/api/v1/recommendation_engine.py:60`, `backend/app/api/v1/recommendation_engine.py:62`
- [x] auth.py의 `_weighted_random_group()` (회원가입 시) 미변경
  - 근거: `backend/app/api/v1/auth.py:43`, `backend/app/api/v1/auth.py:121`
- [x] 기존 추천 로직(`calculate_hybrid_scores` 등) 유지
  - 근거: `backend/app/api/v1/recommendation_engine.py:284`, `backend/app/api/v1/recommendations.py:111`, `backend/app/api/v1/recommendations.py:332`

### 보안
- [x] md5가 보안 목적이 아닌 분배 목적으로만 사용 (적절)
  - 근거: `backend/app/api/v1/recommendations.py:55`
- [x] session_id에 PII 미포함 (UUID만)
  - 근거: `frontend/lib/api.ts:27`

## 결론
- Step 01D는 결정론적 배정, algorithm_version 레지스트리, 프론트 session_id 전파 구조 자체는 잘 반영되었습니다.
- 다만 **CRITICAL 1건**: 추천 점수 계산 경로가 결정론적 `experiment_group`이 아니라 `current_user.experiment_group`를 사용해 실험 라우팅 일관성이 깨집니다.
