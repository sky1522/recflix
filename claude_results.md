# Step 05: LightGBM 기반 CTR 예측 재랭커

> 작업일: 2026-02-27
> 목적: Two-Tower 후보 200개 → GBDT 재랭킹 50개 → 하이브리드 품질보정 20개

## 생성/수정 파일

| 파일 | 변경 |
|------|------|
| `backend/scripts/train_reranker.py` | 신규 — 76dim 피처 추출 + LightGBM 학습 스크립트 |
| `backend/app/services/reranker.py` | 신규 — LGBMReranker 서빙 모듈 (싱글톤 패턴) |
| `backend/app/config.py` | RERANKER_ENABLED, RERANKER_MODEL_PATH 설정 추가 |
| `backend/app/api/v1/recommendation_constants.py` | test_a → twotower_lgbm_v1, test_b → twotower_v1 |
| `backend/app/api/v1/recommendations.py` | LGBM 재랭킹 분기 + _prepare_reranker_input 헬퍼 |
| `backend/app/main.py` | lifespan에 reranker 초기화 추가 |

## 모델 성능

| 지표 | 값 |
|------|------|
| Valid AUC | 0.6608 |
| Valid Logloss | 0.5417 |
| Train AUC | 0.6813 |
| Best Iteration | 27 / 500 |
| 학습 시간 | 0.3s |
| 모델 크기 | 97 KB |

## 피처 중요도 (top 10 by gain)

| 피처 | Gain % |
|------|--------|
| tt_score | 67.44% |
| rank_reciprocal | 13.80% |
| weighted_score | 3.14% |
| mbti_score | 2.26% |
| weather_score | 1.70% |
| emotion_romance | 1.14% |
| emotion_tension | 1.08% |
| emotion_deep | 1.07% |
| emotion_healing | 0.90% |
| emotion_energy | 0.72% |

## 서빙 성능

| 지표 | 값 |
|------|------|
| 200 candidates predict (mean) | 0.134 ms |
| 200 candidates predict (median) | 0.115 ms |
| 200 candidates predict (P99) | 0.301 ms |

## 파이프라인 흐름

```
control:  DB 스캔 → calculate_hybrid_scores → Top 20
test_a:   Two-Tower(200) → LGBM 재랭킹(50) → calculate_hybrid_scores → Top 20
test_b:   Two-Tower(200) → calculate_hybrid_scores → Top 20
```

## A/B 테스트 그룹 매핑

| 그룹 | 알고리즘 |
|------|----------|
| control | hybrid_v1 |
| test_a | twotower_lgbm_v1 |
| test_b | twotower_v1 |

## 검증 결과

| 항목 | 결과 |
|------|------|
| AUC > 0.6 | OK (0.6608) |
| 피처 중요도 합리성 (tt_score, weighted_score, mbti_score 상위) | OK |
| 서빙 모듈 predict 동작 | OK (0.13ms) |
| 재랭킹 후 후보 순서 변경 확인 | OK (rerank_score 기준 정렬) |
| reranker=None fallback | OK (원본 순서 유지) |
| 기존 control 그룹 미변경 | OK |
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |
