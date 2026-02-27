## 작업: 다중 모델 오프라인 비교 리포트 + Interleaving 비교 도구

### 배경
지금까지 4개 모델의 추천 파이프라인이 완성되었습니다:
1. Popularity (weighted_score 순)
2. MBTI-only (mbti_score 순)
3. Hybrid v1 (현재 5축 하이브리드)
4. Two-Tower + LGBM (후보 생성 + 재랭킹)

이제 이 모델들을 자동으로 비교하는 리포트와,
소수 테스터로 두 모델을 공정하게 비교하는 Interleaving 도구가 필요합니다.

### Part A: 다중 모델 비교 리포트

#### 1. 스크립트: backend/scripts/compare_models.py

#### 2. 입력
```bash
python backend/scripts/compare_models.py \
  --test-file data/synthetic/test.jsonl \
  --output-dir data/offline/reports/ \
  --k-values 5 10 20 \
  --n-bootstrap 1000 \
  --verbose
```

test.jsonl 하나만 받고, 내부에서 4개 모델의 랭킹을 각각 생성합니다:
- Popularity: features.weighted_score 내림차순
- MBTI-only: features.mbti_score 내림차순 (mbti 없으면 popularity fallback)
- Hybrid (Current): score 내림차순
- Two-Tower+LGBM: 시뮬레이션 필요 — 아래 참조

Two-Tower+LGBM 시뮬레이션:
- test.jsonl의 각 request에서 tt_score(= score 필드)를 후보 생성 점수로 사용
- LightGBM 모델 로드 → 피처 구성 → predict → 재랭킹
- 모델 파일이 없으면 이 모델은 스킵하고 3개만 비교
```python
# LightGBM 로드 시도
lgbm_model = None
try:
    lgbm_model = lgb.Booster(model_file="data/models/reranker/lgbm_v1.txt")
except:
    print("LGBM model not found, skipping Two-Tower+LGBM comparison")
```

#### 3. 출력 (Markdown + JSON)

Markdown: data/offline/reports/comparison_report.md
```markdown
# RecFlix Model Comparison Report
Generated: 2026-02-27T15:00:00
Dataset: data/synthetic/test.jsonl (9,060 samples, 500 users, 755 requests)

## Overall Metrics

| Model              | NDCG@5 | NDCG@10 | NDCG@20 | Recall@10 | MRR@10 | HitRate@10 |
|--------------------|--------|---------|---------|-----------|--------|------------|
| Popularity         | 0.142  | 0.168   | 0.195   | 0.112     | 0.213  | 0.467      |
| MBTI-only          | 0.165  | 0.189   | 0.218   | 0.134     | 0.238  | 0.533      |
| Hybrid v1          | 0.182  | 0.213   | 0.248   | 0.156     | 0.287  | 0.583      |
| TwoTower+LGBM      | 0.198  | 0.231   | 0.265   | 0.178     | 0.312  | 0.633      |

## Improvement vs Baseline (NDCG@10)

| Model              | NDCG@10 | Δ vs Popularity | Δ vs Hybrid |
|--------------------|---------|-----------------|-------------|
| Popularity         | 0.168   |        -        |   -21.1%    |
| MBTI-only          | 0.189   |    +12.5%       |   -11.3%    |
| Hybrid v1          | 0.213   |    +26.8%       |      -      |
| TwoTower+LGBM      | 0.231   |    +37.5%       |    +8.5%    |

## Ablation Study

| Stage              | NDCG@10 | Δ vs Previous |
|--------------------|---------|---------------|
| Popularity only    | 0.168   |       -       |
| + MBTI             | 0.189   |    +12.5%     |
| + 5-axis Hybrid    | 0.213   |    +12.7%     |
| + Two-Tower        | 0.225   |     +5.6%     |
| + LGBM Reranker    | 0.231   |     +2.7%     |

## Diversity Metrics

| Model              | Coverage@10 | Novelty@10 |
|--------------------|-------------|------------|
| Popularity         | 0.316       | 7.05       |
| MBTI-only          | 0.368       | 7.42       |
| Hybrid v1          | 0.474       | 8.15       |
| TwoTower+LGBM      | 0.526       | 8.38       |

## Bootstrap 95% CI (NDCG@10)

| Model              | Mean  | Lower | Upper |
|--------------------|-------|-------|-------|
| Popularity         | 0.168 | 0.142 | 0.194 |
| Hybrid v1          | 0.213 | 0.185 | 0.241 |
| TwoTower+LGBM      | 0.231 | 0.201 | 0.261 |
```

JSON: data/offline/reports/comparison_full.json
- 모든 수치를 프로그래밍적으로 접근 가능한 형태로 저장

#### 4. Ablation을 위한 Two-Tower only 점수

Two-Tower만 사용(LGBM 없이):
- tt_score 내림차순으로 정렬
- 이것이 "Two-Tower only" 베이스라인

### Part B: Interleaving 비교 도구

#### 5. 모듈: backend/app/services/interleaving.py (신규)
```python
"""Team Draft Interleaving — 두 추천 리스트를 공정하게 섞어 비교"""

import random

def team_draft_interleave(
    list_a: list[int],  # 모델 A의 movie_id 리스트 (순위순)
    list_b: list[int],  # 모델 B의 movie_id 리스트 (순위순)
    k: int = 20
) -> tuple[list[int], set[int], set[int]]:
    """
    Returns:
    - interleaved: 섞인 리스트 (최대 k개)
    - team_a: 모델 A 소속 movie_id set
    - team_b: 모델 B 소속 movie_id set
    
    알고리즘:
    1. 팀 크기가 작은 쪽이 먼저 자기 리스트에서 아직 선택 안 된 최상위 선택
    2. 같으면 랜덤
    3. k개 채울 때까지 반복
    """
    interleaved = []
    team_a = set()
    team_b = set()
    seen = set()
    ptr_a = 0
    ptr_b = 0
    
    while len(interleaved) < k and (ptr_a < len(list_a) or ptr_b < len(list_b)):
        # 팀 크기가 작은 쪽 우선
        if len(team_a) <= len(team_b):
            # A가 선택
            while ptr_a < len(list_a) and list_a[ptr_a] in seen:
                ptr_a += 1
            if ptr_a < len(list_a):
                mid = list_a[ptr_a]
                interleaved.append(mid)
                team_a.add(mid)
                seen.add(mid)
                ptr_a += 1
        else:
            # B가 선택
            while ptr_b < len(list_b) and list_b[ptr_b] in seen:
                ptr_b += 1
            if ptr_b < len(list_b):
                mid = list_b[ptr_b]
                interleaved.append(mid)
                team_b.add(mid)
                seen.add(mid)
                ptr_b += 1
    
    return interleaved, team_a, team_b


def compute_interleaving_result(
    interleaved: list[int],
    team_a: set[int],
    team_b: set[int],
    clicked_ids: set[int]
) -> str:
    """
    클릭된 영화의 팀 귀속으로 승자 결정.
    Returns: "A", "B", or "tie"
    """
    score_a = len(clicked_ids & team_a)
    score_b = len(clicked_ids & team_b)
    if score_a > score_b:
        return "A"
    elif score_b > score_a:
        return "B"
    return "tie"


def compute_win_rate(results: list[str]) -> dict:
    """
    세션별 승패 리스트 → 승률 + 95% CI (binomial)
    
    Returns: {
        "a_wins": 15, "b_wins": 25, "ties": 10,
        "total": 50,
        "b_win_rate": 0.625,  # ties 제외
        "ci_lower": 0.48, "ci_upper": 0.77
    }
    """
```

#### 6. 오프라인 Interleaving 시뮬레이션 스크립트

backend/scripts/run_interleaving.py:
```bash
python backend/scripts/run_interleaving.py \
  --test-file data/synthetic/test.jsonl \
  --model-a-name "Hybrid v1" \
  --model-b-name "TwoTower+LGBM" \
  --lgbm-model data/models/reranker/lgbm_v1.txt \
  --k 20 \
  --output-dir data/offline/reports/
```

시뮬레이션 방식:
1. test.jsonl의 각 request_id에 대해:
   - Model A 랭킹 = score 내림차순 (Hybrid)
   - Model B 랭킹 = LGBM predict 점수 내림차순 (TwoTower+LGBM)
2. team_draft_interleave로 섞기
3. label > 0인 movie_id를 "클릭"으로 간주
4. 승자 결정
5. 전체 세션 승률 계산

출력:
============================================================
Interleaving Comparison: Hybrid v1 vs TwoTower+LGBM
Sessions: 755, K=20
Model A (Hybrid v1):     wins=210 (27.8%)
Model B (TwoTower+LGBM): wins=385 (51.0%)
Ties:                    160 (21.2%)
Win rate (B, excl ties): 64.7% [95% CI: 60.3% - 69.1%]
Verdict: TwoTower+LGBM significantly outperforms Hybrid v1

JSON: data/offline/reports/interleaving_result.json

### 검증
1. comparison_report.md가 4개 모델 비교표 + Ablation + Diversity + CI 포함
2. Popularity < MBTI < Hybrid < TwoTower+LGBM 서열 확인 (대체로)
3. Interleaving 승률이 50% 근처 (비슷한 모델) 또는 한쪽 우세
4. team_draft_interleave: 동일 리스트 입력 시 tie
5. 빈 데이터 시 깨끗한 종료
6. Ruff 린트 통과
7. pytest 통과

### 금지사항
- scipy 의존 금지 (math + numpy만)
- 실제 DB 조회 금지 (JSONL + 모델 파일만 사용)
- 기존 백엔드/프론트엔드 코드 수정 금지

### 완료 후
작업 결과를 claude_results.md에 저장하세요. 포함:
- 생성 파일 목록
- 비교 리포트 요약 (4개 모델 NDCG@10 비교)
- Ablation 결과
- Interleaving 승률
- 검증 결과