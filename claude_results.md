# Step 02B: 오프라인 평가 지표 자동 산출 + 비교 리포트

> 작업일: 2026-02-26
> 목적: test.jsonl로 Popularity/MBTI-only/Current Hybrid 3종 오프라인 성능 비교

## 생성 파일

| 파일 | 설명 |
|------|------|
| `backend/scripts/offline_eval.py` | 오프라인 평가 CLI 스크립트 (약 320줄) |

## CLI 사용 예시

```bash
python backend/scripts/offline_eval.py \
  --test-file data/offline/test.jsonl \
  --output-dir data/offline/reports/ \
  --k-values 5 10 20 \
  --n-bootstrap 1000 \
  --verbose
```

## 평가 지표 (6종 × K=5,10,20)

| 지표 | 설명 | 범위 |
|------|------|------|
| NDCG@K | 높은 관련성을 상위에 올릴수록 높은 점수 | 0~1 |
| Recall@K | Top-K에 positive 영화가 들어온 비율 | 0~1 |
| MRR@K | 첫 positive의 역순위 | 0~1 |
| HitRate@K | Top-K에 positive 1개라도 있으면 1 | 0/1 |
| Coverage@K | 추천 장르 커버리지 (19종 대비) | 0~1 |
| Novelty@K | 비인기 영화 추천 정도 (-log2 popularity) | 0~∞ |

## 3종 베이스라인

| 모델 | 랭킹 기준 | 역할 |
|------|-----------|------|
| Popularity | features.weighted_score 내림차순 | 최소 기준선 |
| MBTI-only | features.mbti_score 내림차순 | 중간 기준선 |
| Current (hybrid) | score 내림차순 (현재 모델 예측) | 현재 성능 |

## 리포트 출력 예시 (합성 데이터 50건)

```
Comparison vs Current Model (NDCG@10)
┌──────────────────────────────────────────────────┐
│ Model            NDCG@10         Δ        Δ%     │
├──────────────────────────────────────────────────┤
│ Popularity         0.582    -0.114    -16.4%     │
│ MBTI-only          0.579    -0.117    -16.8%     │
│ Current (hybrid)   0.696         -         -     │
└──────────────────────────────────────────────────┘
```

## 검증 결과

| 항목 | 결과 |
|------|------|
| ndcg_at_k (perfect=1.0, reversed<1.0) | OK |
| recall_at_k (hits/min(relevant, k)) | OK |
| mrr_at_k (first hit rank) | OK |
| hit_rate_at_k (binary) | OK |
| genre_coverage (unique genres / 19) | OK |
| novelty (less popular = higher) | OK |
| bootstrap_ci (single/multi value) | OK |
| rank_by_score/popularity/mbti 정렬 | OK |
| MBTI fallback to popularity (no context) | OK |
| Current > Popularity, Current > MBTI-only (NDCG@10) | OK |
| 빈 데이터 → 깨끗한 종료 | OK |
| JSON 리포트 3개 생성 | OK |
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |
