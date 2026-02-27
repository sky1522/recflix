## 작업: LightGBM 기반 CTR 예측 재랭커

### 배경
Two-Tower가 관련성 후보 200개를 뽑으면, 최종 Top-20 순서를 결정하는
정밀 재랭킹이 필요합니다. 정형 피처가 많은 RecFlix에서는 GBDT가 효과적입니다.
(달리셔스 CatBoost 사례, 딥러닝 실습 강의의 "피처 활용 GBDT > 단순 DL" 결론 참고)

현재 파이프라인:
  Two-Tower(200) → 하이브리드 재랭킹 → 다양성 후처리 → Top-20

목표 파이프라인:
  Two-Tower(200) → GBDT 재랭킹(50) → 하이브리드 품질보정 + 다양성(20)

### 요구사항

#### 1. 학습 스크립트: backend/scripts/train_reranker.py

#### 2. 피처 설계

train.jsonl/valid.jsonl의 각 행에서 추출:

사용자 피처:
- mbti_onehot: 16dim (context.mbti → one-hot)
- user_genres: 19dim (user의 preferred_genres → 멀티핫, context에서 추출 불가 시 zeros)

아이템 피처:
- item_genres: 19dim (features.genres → 멀티핫)
- weighted_score: 1dim (features.weighted_score)
- emotion_tags: 7dim (features.emotion_tags의 7개 키)

컨텍스트 피처:
- weather_onehot: 4dim (context.weather → one-hot: sunny/rainy/cloudy/snowy)
- mood_onehot: 6dim (context.mood → one-hot: happy/sad/excited/calm/tired/emotional)

교차 피처 (이미 계산된 점수):
- mbti_score: 1dim (features.mbti_score)
- weather_score: 1dim (features.weather_score)

후보 생성 피처:
- tt_score: 1dim (score 필드 — Two-Tower 또는 하이브리드 점수)
- rank: 1dim (rank 필드 — 후보 생성 시 순위, 1/(rank+1)로 정규화)

총 피처: 16+19+19+1+7+4+6+1+1+1+1 = 76dim
```python
FEATURE_NAMES = [
    # mbti one-hot (16)
    *[f"mbti_{t}" for t in MBTI_TYPES],
    # user genres (19)
    *[f"user_genre_{g}" for g in GENRE_LIST],
    # item genres (19)
    *[f"item_genre_{g}" for g in GENRE_LIST],
    # item features
    "weighted_score",
    *[f"emotion_{k}" for k in EMOTION_KEYS],  # 7
    # context
    *[f"weather_{w}" for w in WEATHER_TYPES],  # 4
    *[f"mood_{m}" for m in MOOD_TYPES],        # 6
    # cross features
    "mbti_score", "weather_score",
    # candidate features
    "tt_score", "rank_reciprocal",
]
```

#### 3. 라벨

이진 분류 (CTR 예측):
- label >= 1 → positive (1) : 클릭/체류/찜/고평점 중 하나라도 있음
- label == 0 → negative (0) : 노출만 되고 반응 없음

#### 4. LightGBM 학습
```python
import lightgbm as lgb

params = {
    'objective': 'binary',
    'metric': ['auc', 'binary_logloss'],
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1,
    'seed': 42,
}

train_data = lgb.Dataset(X_train, label=y_train, feature_name=FEATURE_NAMES)
valid_data = lgb.Dataset(X_valid, label=y_valid, feature_name=FEATURE_NAMES, reference=train_data)

model = lgb.train(
    params,
    train_data,
    num_boost_round=500,
    valid_sets=[train_data, valid_data],
    valid_names=['train', 'valid'],
    callbacks=[
        lgb.early_stopping(stopping_rounds=30),
        lgb.log_evaluation(period=50),
    ],
)
```

#### 5. 출력 아티팩트

| 파일 | 설명 |
|------|------|
| data/models/reranker/lgbm_v1.txt | LightGBM 모델 (model.save_model) |
| data/models/reranker/feature_importance.json | 피처 중요도 (gain + split) |
| data/models/reranker/eval_metrics.json | AUC, logloss, 학습 곡선 |
| data/models/reranker/config.json | 하이퍼파라미터 |

#### 6. 피처 중요도 리포트 (stdout)
Feature Importance (top 15 by gain):

mbti_score         23.4%
tt_score           18.7%
weighted_score     12.1%
weather_score       8.3%
rank_reciprocal     6.2%
...


#### 7. CLI 인터페이스
```bash
python backend/scripts/train_reranker.py \
  --train-file data/synthetic/train.jsonl \
  --valid-file data/synthetic/valid.jsonl \
  --output-dir data/models/reranker/ \
  --num-rounds 500 \
  --early-stopping 30 \
  --verbose
```

#### 8. 서빙 모듈: backend/app/services/reranker.py (신규)
```python
class LGBMReranker:
    def __init__(self, model_path):
        self.model = lgb.Booster(model_file=str(model_path))
        self.ready = True
    
    def rerank(self, candidates: list[dict], top_k: int = 50) -> list[dict]:
        """
        candidates: [{movie_id, genres, weighted_score, emotion_tags, 
                       mbti_score, weather_score, tt_score, rank, ...}]
        
        1. 피처 벡터 구성 (76dim)
        2. model.predict() → CTR 확률
        3. 확률 내림차순 정렬
        4. top_k 반환
        
        에러 시 빈 리스트 반환 + 로깅 (추천 중단 방지)
        """
        try:
            features = self._prepare_features(candidates)
            scores = self.model.predict(features)
            
            for cand, score in zip(candidates, scores):
                cand['rerank_score'] = float(score)
            
            sorted_candidates = sorted(candidates, key=lambda x: x['rerank_score'], reverse=True)
            return sorted_candidates[:top_k]
        except Exception as e:
            logger.error("reranker_failed", error=str(e), exc_info=True)
            return candidates[:top_k]  # fallback: 원래 순서 유지
```

#### 9. 추천 API 결합

recommendation_constants.py 업데이트:
```python
GROUP_ALGORITHM_MAP = {
    "control": "hybrid_v1",
    "test_a": "twotower_lgbm_v1",    # ← Two-Tower + GBDT 재랭킹
    "test_b": "twotower_v1",          # Two-Tower only (비교용)
}
```

recommendations.py에서 분기 추가:
```python
if algorithm_version.startswith("twotower"):
    tt_candidates = retriever.retrieve(...)
    
    if "lgbm" in algorithm_version and reranker is not None:
        # GBDT 재랭킹 경로
        candidate_dicts = prepare_reranker_input(tt_candidates, movies, context)
        reranked = reranker.rerank(candidate_dicts, top_k=50)
        candidate_ids = [c['movie_id'] for c in reranked]
        movies = [movie_map[mid] for mid in candidate_ids if mid in movie_map]
    
    # 이후 calculate_hybrid_scores()로 최종 재랭킹 (동일)
```

#### 10. main.py에 Reranker 초기화 추가

TwoTowerRetriever와 동일 패턴:
```python
try:
    reranker = LGBMReranker(model_path=settings.RERANKER_MODEL_PATH)
except:
    reranker = None
    logger.warning("LGBM reranker not available")
```

config.py에 추가:
```python
RERANKER_MODEL_PATH: str = "data/models/reranker/lgbm_v1.txt"
RERANKER_ENABLED: bool = True
```

### 검증
1. AUC > 0.6 (synthetic 데이터 기준)
2. feature_importance 상위 피처가 합리적 (mbti_score, tt_score, weighted_score 등)
3. 서빙 모듈 predict 동작 확인
4. 재랭킹 후 후보 순서가 변경되는지 확인
5. reranker=None일 때 fallback 동작
6. 기존 control 그룹 미변경
7. Ruff 린트 통과
8. pytest 통과

### 금지사항
- CatBoost/XGBoost 금지 (LightGBM만, 의존성 최소화)
- 학습 시 test 데이터 사용 금지
- calculate_hybrid_scores 수정 금지
- 기존 control/test_b 경로 변경 금지

### 완료 후
작업 결과를 claude_results.md에 저장하세요. 포함:
- 생성/수정 파일 목록
- 모델 성능 (AUC, logloss)
- 피처 중요도 상위 10개
- 서빙 성능 (predict 시간)
- 검증 결과