## 작업: 오프라인 평가 지표 자동 산출 + 비교 리포트

### 배경
Step 02A에서 train/valid/test.jsonl이 생성됩니다.
이 데이터로 현재 모델의 오프라인 성능을 측정하고,
향후 모든 모델 비교의 기준점(베이스라인)을 확립합니다.

핵심 원칙:
- request_id 단위(= 리스트 단위) 평가: 한 번의 추천 요청이 하나의 평가 단위
- 4개 베이스라인 비교: Popularity, MBTI-only, 현재 Hybrid, (향후) Two-Tower
- Bootstrap CI로 소표본 신뢰구간 확보

### 요구사항

#### 1. 스크립트: backend/scripts/offline_eval.py

#### 2. 평가 지표 함수
```python
import math
import numpy as np

def ndcg_at_k(ranked_movie_ids: list[int], relevance: dict[int, float], k: int) -> float:
    """
    Normalized Discounted Cumulative Gain.
    relevance: {movie_id: label} (label 0~3)
    높은 관련성 영화를 상위에 올릴수록 높은 점수.
    """
    dcg = sum(relevance.get(mid, 0) / math.log2(i + 2)
              for i, mid in enumerate(ranked_movie_ids[:k]))
    ideal = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0

def recall_at_k(ranked_movie_ids: list[int], relevant_set: set[int], k: int) -> float:
    """Top-K에 positive(label>0) 영화가 얼마나 들어왔는가"""
    if not relevant_set:
        return 0.0
    hits = len(set(ranked_movie_ids[:k]) & relevant_set)
    return hits / min(len(relevant_set), k)

def mrr_at_k(ranked_movie_ids: list[int], relevant_set: set[int], k: int) -> float:
    """첫 번째 positive의 역순위"""
    for i, mid in enumerate(ranked_movie_ids[:k]):
        if mid in relevant_set:
            return 1.0 / (i + 1)
    return 0.0

def hit_rate_at_k(ranked_movie_ids: list[int], relevant_set: set[int], k: int) -> float:
    """Top-K에 positive가 1개라도 있으면 1, 없으면 0"""
    return 1.0 if set(ranked_movie_ids[:k]) & relevant_set else 0.0

# 다양성 지표
def genre_coverage(ranked_movie_ids: list[int], movie_genres: dict[int, list[str]], k: int, total_genres: int = 19) -> float:
    """추천된 영화가 커버하는 장르 비율"""
    genres = set()
    for mid in ranked_movie_ids[:k]:
        genres.update(movie_genres.get(mid, []))
    return len(genres) / total_genres

def novelty(ranked_movie_ids: list[int], popularity: dict[int, float], k: int) -> float:
    """덜 인기 있는 영화를 추천할수록 높은 점수"""
    scores = [-math.log2(max(popularity.get(mid, 1e-6), 1e-6))
              for mid in ranked_movie_ids[:k]]
    return sum(scores) / len(scores) if scores else 0.0
```

#### 3. Bootstrap 신뢰구간
```python
def bootstrap_ci(values: list[float], n_bootstrap: int = 1000, ci: float = 0.95) -> tuple[float, float, float]:
    """
    유저/request 단위 metric 리스트로 95% CI 계산.
    Returns: (mean, ci_lower, ci_upper)
    """
    values = np.array(values)
    means = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(values, size=len(values), replace=True)
        means.append(np.mean(sample))
    means = sorted(means)
    alpha = (1 - ci) / 2
    lower = means[int(alpha * n_bootstrap)]
    upper = means[int((1 - alpha) * n_bootstrap)]
    return float(np.mean(values)), lower, upper
```

#### 4. 평가 흐름
test.jsonl 로드
↓
request_id별 그룹핑
↓
각 request_id에 대해:
ranked_list = score 내림차순 정렬된 movie_id 리스트
relevance = {movie_id: label}
relevant_set = {movie_id for movie_id, label in ... if label > 0}
↓
NDCG@K, Recall@K, MRR@K, HitRate@K 계산 (K=5,10,20)
↓
request_id별 metric 수집
↓
평균 + Bootstrap CI
↓
experiment_group별, algorithm_version별 분리 집계

#### 5. Popularity 베이스라인 자동 생성

test.jsonl에 있는 각 request_id에 대해:
- 해당 request의 모든 movie_id를 features.weighted_score 내림차순으로 정렬
- 이 순서를 "Popularity 모델의 추천"으로 사용
- 동일한 지표(NDCG/Recall/MRR/HitRate)를 계산

이것이 "아무 개인화 없이 인기순으로만 보여줬을 때"의 최소 기준선.

#### 6. MBTI-only 베이스라인 자동 생성

test.jsonl에 있는 각 request_id에 대해:
- context.mbti가 있으면: features.mbti_score 내림차순으로 정렬
- context.mbti가 없으면: Popularity와 동일 (fallback)
- "MBTI 하나만으로 추천했을 때"의 중간 기준선

#### 7. 리포트 출력 (stdout + JSON)

터미널 출력:
============================================================
RecFlix Offline Evaluation Report
Dataset: data/offline/test.jsonl (750 samples, 12 users, 45 requests)
Generated: 2026-02-26T15:00:00
[1/3] Popularity Baseline (weighted_score ordering)
┌──────────┬──────────┬──────────┬──────────┬──────────────┐
│ Metric   │   @5     │  @10     │  @20     │  95% CI(@10) │
├──────────┼──────────┼──────────┼──────────┼──────────────┤
│ NDCG     │  0.142   │  0.168   │  0.195   │ ±0.028       │
│ Recall   │  0.087   │  0.112   │  0.156   │ ±0.021       │
│ MRR      │  0.198   │  0.213   │  0.225   │ ±0.035       │
│ HitRate  │  0.333   │  0.467   │  0.600   │ ±0.048       │
│ Coverage │  0.316   │  0.474   │  0.632   │    -         │
│ Novelty  │  7.21    │  7.05    │  6.89    │    -         │
└──────────┴──────────┴──────────┴──────────┴──────────────┘
[2/3] MBTI-only Baseline (mbti_score ordering)
...동일 형식...
[3/3] Current Model (score ordering = hybrid_v1)
...동일 형식...
============================================================
Comparison vs Current Model (NDCG@10)
┌──────────────────┬──────────┬──────────┬──────────┐
│ Model            │ NDCG@10  │   Δ      │  Δ%      │
├──────────────────┼──────────┼──────────┼──────────┤
│ Popularity       │  0.168   │  -0.045  │ -21.1%   │
│ MBTI-only        │  0.189   │  -0.024  │ -11.3%   │
│ Current (hybrid) │  0.213   │    -     │    -     │
└──────────────────┴──────────┴──────────┴──────────┘

JSON 출력: data/offline/reports/eval_{model_name}_{date}.json
```json
{
  "model_name": "hybrid_v1",
  "dataset": "data/offline/test.jsonl",
  "generated_at": "2026-02-26T15:00:00",
  "n_samples": 750,
  "n_users": 12,
  "n_requests": 45,
  "metrics": {
    "ndcg": {"@5": 0.182, "@10": 0.213, "@20": 0.248},
    "recall": {"@5": 0.098, "@10": 0.156, "@20": 0.201},
    "mrr": {"@5": 0.245, "@10": 0.287, "@20": 0.312},
    "hit_rate": {"@5": 0.417, "@10": 0.583, "@20": 0.750},
    "coverage": {"@5": 0.421, "@10": 0.579, "@20": 0.684},
    "novelty": {"@5": 8.42, "@10": 8.15, "@20": 7.89}
  },
  "ci_95": {
    "ndcg@10": [0.182, 0.244],
    "recall@10": [0.132, 0.180]
  },
  "per_group": {
    "control": {"ndcg@10": 0.198, "recall@10": 0.142},
    "test_a": {"ndcg@10": 0.221, "recall@10": 0.163}
  }
}
```

#### 8. CLI 인터페이스
```bash
python backend/scripts/offline_eval.py \
  --test-file data/offline/test.jsonl \
  --output-dir data/offline/reports/ \
  --k-values 5 10 20 \
  --n-bootstrap 1000 \
  --verbose
```

- --test-file: test.jsonl 경로 (필수)
- --output-dir: JSON 리포트 출력 디렉토리 (기본: data/offline/reports/)
- --k-values: 평가할 K 값들 (기본: 5 10 20)
- --n-bootstrap: Bootstrap 샘플 수 (기본: 1000)
- --verbose: 상세 로그

#### 9. 데이터가 없거나 부족할 때

- test.jsonl이 비어있으면: "No test data found." 출력 후 종료
- request_id가 1개뿐이면: Bootstrap CI 생략하고 point estimate만 표시
- positive(label>0)가 하나도 없으면: 모든 지표 0으로 표시 + 경고

### 검증
1. Popularity < MBTI-only < Hybrid 순서가 대체로 유지되는지 (아니면 분석 코멘트)
2. NDCG, Recall, MRR 값이 0~1 범위
3. Bootstrap CI가 합리적 (mean ± CI가 0~1 이내)
4. JSON 파일과 터미널 출력이 일치
5. 빈 데이터 시 깨끗한 종료
6. Ruff 린트 통과

### 금지사항
- scipy 의존 금지 (math + numpy만 사용)
- 실제 모델 추론 금지 — test.jsonl의 score/rank를 "현재 모델 예측"으로 사용
- Popularity/MBTI 베이스라인도 test.jsonl의 features에서 추출 (별도 DB 조회 불필요)

### 완료 후
작업 결과를 claude_results.md에 저장하세요. 포함:
- 생성 파일 목록
- CLI 사용 예시
- 검증 결과
- 리포트 출력 예시 (축약)