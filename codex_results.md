# Step 05A Review - 다중 모델 비교 + Interleaving

## Findings (Severity Order)

### CRITICAL
- 없음

### WARNING
1. `Hybrid v1`와 `TwoTower only`가 동일한 랭킹 함수(`rank_by_score`)를 사용해 사실상 같은 모델로 평가됩니다.
- 이 경우 Ablation 단계의 `+ Two-Tower` 개선치가 왜곡되거나 0에 수렴해 실험 해석력이 떨어집니다.
- 근거: `backend/scripts/compare_models.py:163`, `backend/scripts/compare_models.py:167`, `backend/scripts/compare_models.py:169`, `backend/scripts/compare_models.py:412`, `backend/scripts/compare_models.py:413`

2. `run_interleaving.py`가 `app/services/interleaving.py`의 공용 함수를 재사용하지 않고 동일 로직을 별도 구현합니다.
- 현재 동작은 가능하지만, 이후 로직 변경 시 스크립트/서비스 간 결과 불일치 리스크가 있습니다.
- 근거: `backend/scripts/run_interleaving.py:106`, `backend/scripts/run_interleaving.py:158`, `backend/app/services/interleaving.py:9`, `backend/app/services/interleaving.py:81`

### INFO
1. `compare_models.py` 모듈 설명에는 4개 모델로 적혀 있으나 실제 구현은 LGBM 존재 시 5개 모델 평가를 지원합니다.
- 근거: `backend/scripts/compare_models.py:5`, `backend/scripts/compare_models.py:416`, `backend/scripts/compare_models.py:417`

## 체크리스트 검증

### compare_models.py
- [x] 5개 모델 점수 생성 (Popularity, MBTI, Hybrid, TwoTower only, TwoTower+LGBM)
  - 상태: LGBM 모델이 있을 때 5개 모두 평가
  - 근거: `backend/scripts/compare_models.py:408`, `backend/scripts/compare_models.py:416`, `backend/scripts/compare_models.py:418`
- [x] LGBM 모델 없으면 해당 모델 스킵하고 나머지 비교
  - 근거: `backend/scripts/compare_models.py:393`, `backend/scripts/compare_models.py:404`, `backend/scripts/compare_models.py:416`
- [x] NDCG/Recall/MRR/HitRate @K=5,10,20 계산
  - 근거: `backend/scripts/compare_models.py:241`, `backend/scripts/compare_models.py:260`, `backend/scripts/compare_models.py:261`, `backend/scripts/compare_models.py:262`, `backend/scripts/compare_models.py:263`, `backend/scripts/compare_models.py:365`
- [x] Coverage, Novelty 포함
  - 근거: `backend/scripts/compare_models.py:264`, `backend/scripts/compare_models.py:265`
- [x] Bootstrap CI 계산
  - 근거: `backend/scripts/compare_models.py:97`, `backend/scripts/compare_models.py:273`, `backend/scripts/compare_models.py:276`
- [x] Ablation Study 생성
  - 근거: `backend/scripts/compare_models.py:428`, `backend/scripts/compare_models.py:441`, `backend/scripts/compare_models.py:446`
- [x] Markdown + JSON 출력
  - 근거: `backend/scripts/compare_models.py:455`, `backend/scripts/compare_models.py:469`
- [x] DB 조회 없음 (JSONL + 모델 파일만 사용)
  - 근거: `backend/scripts/compare_models.py:116`, `backend/scripts/compare_models.py:376`, `backend/scripts/compare_models.py:398`

### interleaving.py
- [x] `team_draft_interleave`: 팀 균형 유지하며 교대 선택
  - 근거: `backend/app/services/interleaving.py:33`, `backend/app/services/interleaving.py:35`
- [x] 중복 movie_id 방지 (`seen` set)
  - 근거: `backend/app/services/interleaving.py:29`, `backend/app/services/interleaving.py:40`, `backend/app/services/interleaving.py:46`
- [x] `compute_interleaving_result`: clicked_ids로 team_a/b 비교
  - 근거: `backend/app/services/interleaving.py:81`, `backend/app/services/interleaving.py:90`, `backend/app/services/interleaving.py:91`
- [x] `compute_win_rate`: 승률 + 95% CI (binomial)
  - 근거: `backend/app/services/interleaving.py:99`, `backend/app/services/interleaving.py:124`, `backend/app/services/interleaving.py:128`

### run_interleaving.py
- [x] test.jsonl에서 request별 모델 점수 생성
  - 근거: `backend/scripts/run_interleaving.py:213`, `backend/scripts/run_interleaving.py:237`, `backend/scripts/run_interleaving.py:241`
- [x] `team_draft_interleave`로 섞기
  - 근거: `backend/scripts/run_interleaving.py:106`, `backend/scripts/run_interleaving.py:245`
- [x] `label > 0`을 "클릭"으로 간주
  - 근거: `backend/scripts/run_interleaving.py:247`
- [x] 승패 + CI 출력
  - 근거: `backend/scripts/run_interleaving.py:260`, `backend/scripts/run_interleaving.py:267`, `backend/scripts/run_interleaving.py:301`
- [x] JSON 결과 저장
  - 근거: `backend/scripts/run_interleaving.py:289`, `backend/scripts/run_interleaving.py:291`

### 안정성
- [x] scipy 미사용
  - 근거: `backend/scripts/compare_models.py:26`, `backend/scripts/run_interleaving.py:26`, `backend/app/services/interleaving.py:5`
- [x] 기존 코드 수정 없음
  - 근거: 현재 워크트리 기준 Step 05A 대상 파일 변경 없음
- [x] 빈 데이터 처리
  - 근거: `backend/scripts/compare_models.py:377`, `backend/scripts/run_interleaving.py:209`, `backend/app/services/interleaving.py:111`

## 결론
- Step 05A는 오프라인 모델 비교 및 interleaving 실험 파이프라인이 전반적으로 구현되어 있으며, 체크리스트의 핵심 기능은 대부분 충족합니다.
- 다만 실험 신뢰도 측면에서 **WARNING 2건**(Hybrid/TwoTower 랭킹 동일, interleaving 로직 이중화)이 확인되어 보완이 필요합니다.
