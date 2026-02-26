## 긴급 수정: Step 01D CRITICAL — experiment_group 일관성 확보

### 문제
Codex 리뷰에서 발견된 핵심 불일치:

get_home_recommendations()에서:
1. experiment_group = get_deterministic_group(...)  ← 결정론적 그룹 (로깅용)
2. calculate_hybrid_scores(experiment_group=current_user.experiment_group)  ← DB에 저장된 그룹 (스코어링용)
3. log_impressions(experiment_group=experiment_group)  ← 결정론적 그룹 (로깅용)

→ 2번과 1,3번이 서로 다른 그룹을 사용할 수 있음
→ "로그에는 test_a인데 실제로는 control 가중치로 추천"이 발생 가능
→ 오프라인 평가 시 실험 해석이 완전히 깨짐

### 수정 방법

get_home_recommendations()에서 결정론적으로 배정한 experiment_group을
추천 스코어링에도 동일하게 사용하도록 통일합니다.

구체적으로:
- calculate_hybrid_scores() 호출 시 experiment_group 인자를
  current_user.experiment_group 대신 get_deterministic_group()의 결과를 사용
- 보조 섹션(mbti_picks, weather_picks 등) 생성 시에도 동일한 experiment_group 사용
- 즉, 하나의 요청 내에서 experiment_group은 단 하나의 값만 존재

변경 범위:
- backend/app/api/v1/recommendations.py 내에서
  calculate_hybrid_scores(..., experiment_group=...) 호출부
  및 기타 experiment_group을 참조하는 모든 지점을
  함수 상단에서 결정한 experiment_group 변수로 통일

주의:
- current_user.experiment_group (DB 저장값)은 건드리지 않음
- DB의 experiment_group은 회원가입 시 초기 배정값으로, 참고용으로만 남김
- 실제 추천/로깅에 사용하는 그룹은 항상 get_deterministic_group() 결과

### 검증
1. 로그인 사용자: reco_impressions의 experiment_group과
   실제 적용된 가중치(get_weights_for_group의 인자)가 동일한 그룹인지 확인
2. 비로그인 사용자: session_id 기반 그룹이 스코어링과 로깅 모두에 일관 적용
3. Ruff 린트 통과
4. pytest 통과
5. 프론트엔드 빌드 영향 없음

### 금지사항
- current_user.experiment_group DB 컬럼 수정 금지
- calculate_hybrid_scores 함수 시그니처 변경 금지 (호출 인자만 변경)
- auth.py의 회원가입 시 그룹 배정 로직 변경 금지

### 완료 후
작업 결과를 claude_results.md에 저장하세요. 포함:
- 변경된 코드 위치 (라인 단위)
- 변경 전/후 experiment_group 흐름 비교
- 검증 결과