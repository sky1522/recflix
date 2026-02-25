claude "Phase 52B: A/B 리포트 강화 — 통계적 유의성 + 추가 메트릭.

=== Research ===
다음 파일들을 읽을 것:
- backend/app/api/v1/events.py (ab-report 전체 로직)
- backend/app/schemas/user_event.py (ABReport, ABGroupStats 스키마)
- backend/app/api/v1/recommendation_constants.py (가중치 설정)
- backend/app/models/user.py (experiment_group)
- backend/app/core/config.py (설정)

=== 1단계: 통계적 유의성 추가 ===

ab-report API 응답에 각 메트릭별 통계 검증 추가:

1-1. Z-test for proportions (CTR 비교):
  - 두 그룹 간 CTR 차이가 유의한지
  - z = (p1 - p2) / sqrt(p_pool * (1-p_pool) * (1/n1 + 1/n2))
  - p-value 계산 (scipy.stats.norm 또는 직접 구현)
  - confidence_level: 0.95 기본

1-2. 각 그룹 쌍에 대해 비교:
  - control vs test_a
  - control vs test_b
  - test_a vs test_b

1-3. ABGroupStats에 추가 필드:
  - ctr_ci_lower, ctr_ci_upper (95% 신뢰구간)
  - ABReport에 추가:
    - comparisons: [{ group_a, group_b, metric, difference, p_value, significant }]
    - minimum_sample_size: 각 그룹 최소 표본 수 안내

⚠️ scipy 의존성 추가하지 말 것 — math 모듈로 직접 구현 (정규분포 근사)
⚠️ 표본 수 부족 시 'insufficient_data' 표시

=== 2단계: 추가 메트릭 ===

ab-report에 새 메트릭 추가:

2-1. 추천 수용률:
  - 추천 섹션에서 클릭한 영화에 대한 평균 평점
  - source_section이 추천 섹션인 rating 이벤트 집계
  
2-2. 섹션별 전환 퍼널:
  impression → click → detail_view → rating/favorite
  각 단계별 전환율

2-3. 일별 활성 사용자 추이:
  - 그룹별 일별 고유 사용자 수
  - 재방문율 (2일 이상 이벤트가 있는 사용자 비율)

2-4. 평균 세션 이벤트 수:
  - session_id별 이벤트 수 → 그룹별 평균

=== 3단계: 실험 그룹 비율 조절 ===

3-1. backend/app/core/config.py에 추가:
  EXPERIMENT_WEIGHTS: str = "control:34,test_a:33,test_b:33"
  파싱하여 가중치 기반 random.choices() 배정

3-2. backend/app/api/v1/auth.py 수정:
  기존: random.choice(EXPERIMENT_GROUPS)
  변경: weighted_random_group() 함수 사용
  환경변수로 비율 조절 가능 (예: control:80,test_a:10,test_b:10)

=== 규칙 ===
- scipy 추가 금지 (math 모듈로 구현)
- 기존 ab-report 응답 구조 하위 호환 (새 필드는 추가만)
- SQL 쿼리 성능: 인덱스 활용, 불필요한 전체 스캔 방지

=== 검증 ===
1. cd backend && ruff check app/ → 0 issues
2. cd backend && python -c 'from app.main import app; print(app.title)'
3. cd backend && pytest -v --tb=short
4. Z-test 계산 검증: 알려진 값으로 수동 확인
5. git add -A && git commit -m 'feat: Phase 52B A/B 리포트 통계 유의성 + 추가 메트릭' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- 통계 검증 구현 방식 (Z-test 공식)
- 추가된 메트릭 목록
- 그룹 비율 조절 방식
- ABReport 스키마 변경 전/후"