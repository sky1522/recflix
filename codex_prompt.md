## 리뷰 대상: Step 01D — 실험 라우팅 확정 + algorithm_version 체계

### 리뷰 범위
- backend/app/api/v1/recommendation_constants.py (수정)
- backend/app/api/v1/recommendations.py (수정)
- frontend/lib/api.ts (수정)

### 체크리스트

#### 결정론적 배정
- [ ] get_deterministic_group()이 동일 user_id에 대해 항상 같은 그룹 반환
- [ ] user_id가 None일 때 session_id를 seed로 사용
- [ ] user_id와 session_id 모두 None일 때 fallback("anonymous") 처리
- [ ] md5 해시 → bucket(0~99) → weights 누적 비교 로직 정확
- [ ] 기존 _weighted_random_group()이 삭제되지 않고 유지

#### algorithm_version 레지스트리
- [ ] GROUP_ALGORITHM_MAP이 코드 상수로 선언
- [ ] get_algorithm_version()이 맵에 없는 그룹에 대해 안전한 기본값 반환
- [ ] recommendations.py에서 algorithm_version을 레지스트리에서 가져오는지

#### 프론트엔드 session_id
- [ ] localStorage에 session_id 저장/재사용
- [ ] SSR 환경(window undefined)에서 에러 없이 동작
- [ ] fetchAPI의 모든 호출에 X-Session-ID 헤더 포함
- [ ] 기존 fetchAPI 동작(인증 헤더, timeout 등) 미변경

#### 하위 호환성
- [ ] EXPERIMENT_WEIGHTS 환경변수 체계 유지
- [ ] get_weights_for_group() 등 기존 가중치 로직 미변경
- [ ] auth.py의 _weighted_random_group() (회원가입 시) 미변경
- [ ] 기존 추천 로직(calculate_hybrid_scores 등) 미변경

#### 보안
- [ ] md5가 보안 목적이 아닌 분배 목적으로만 사용 (적절)
- [ ] session_id에 PII 미포함 (UUID만)

### 발견사항 분류
- CRITICAL: 그룹 배정 불일관, 기존 기능 파손
- WARNING: fallback 미흡, 환경변수 파싱 이슈
- INFO: 네이밍, 코멘트

### 출력
결과를 codex_results.md에 저장하세요.