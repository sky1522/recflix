# Phase 3-2: 협업 필터링 구현 + 하이브리드 통합

Phase 3-1의 매핑 데이터로 CF 모델을 구현하고, 현재 Rule-based와 비교 평가한 뒤 프로덕션에 통합한다.

⚠️ Phase 3-1 완료 후 실행. mapped_ratings.csv와 eval_results.csv가 있어야 함.

먼저 읽을 것:
- .claude/skills/recommendation.md (현재 추천 엔진 구조)
- backend/app/api/v1/recommendation_engine.py (현재 스코어링 로직)
- backend/app/api/v1/recommendation_constants.py (가중치 상수)
- backend/data/movielens/mapping_stats.json (매핑 결과)
- backend/data/movielens/eval_results.csv (베이스라인 결과)
- backend/scripts/recommendation_eval.py (평가 프레임워크)

```bash
# 매핑 통계 확인
cat backend/data/movielens/mapping_stats.json

# 현재 베이스라인 결과 확인
cat backend/data/movielens/eval_results.csv

# 현재 추천 엔진 구조 확인
grep -n "def " backend/app/api/v1/recommendation_engine.py
```

---

=== 1단계: Surprise 라이브러리 설치 ===

```bash
pip install scikit-surprise pandas numpy --break-system-packages
```

requirements.txt에 추가:
```
scikit-surprise==1.1.4
```

---

=== 2단계: CF 모델 학습 + 평가 스크립트 ===

**backend/scripts/recommendation_eval.py 확장** (기존 파일에 추가):

Phase 3-1에서 만든 eval 스크립트에 CF 모델들을 추가한다.

```python
# === Item-based CF (Surprise KNNBaseline) ===

from surprise import Dataset, Reader, KNNBaseline, SVD, accuracy
from surprise.model_selection import train_test_split as surprise_split

def evaluate_surprise_models(train_df, test_df, k=10):
    """Surprise 라이브러리로 CF 모델 평가"""
    
    # Surprise 데이터셋 형식으로 변환
    reader = Reader(rating_scale=(0.5, 5.0))
    
    # Train + Test 합쳐서 Surprise Dataset 생성 후 분리
    full_df = pd.concat([train_df, test_df])
    data = Dataset.load_from_df(
        full_df[["userId", "recflix_movie_id", "rating"]], reader
    )
    
    # Surprise 자체 분리 (우리 분리와 다를 수 있으므로 전체 데이터로)
    trainset, testset = surprise_split(data, test_size=0.2, random_state=42)
    
    results = []
    
    # --- Item-based CF ---
    print("\n학습 중: Item-based KNN...")
    sim_options = {"name": "cosine", "user_based": False}
    item_knn = KNNBaseline(k=40, sim_options=sim_options, verbose=False)
    item_knn.fit(trainset)
    predictions_knn = item_knn.test(testset)
    rmse_knn = accuracy.rmse(predictions_knn, verbose=False)
    
    results.append({
        "model": "item_based_cf",
        "rmse": f"{rmse_knn:.4f}",
        **evaluate_topk(item_knn, trainset, testset, k)
    })
    
    # --- SVD ---
    print("학습 중: SVD...")
    svd = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42)
    svd.fit(trainset)
    predictions_svd = svd.test(testset)
    rmse_svd = accuracy.rmse(predictions_svd, verbose=False)
    
    results.append({
        "model": "svd",
        "rmse": f"{rmse_svd:.4f}",
        **evaluate_topk(svd, trainset, testset, k)
    })
    
    # --- SVD++ (더 정교하지만 느림) ---
    # 데이터가 크면 시간이 오래 걸릴 수 있음, 선택적
    # from surprise import SVDpp
    # svdpp = SVDpp(n_factors=50, n_epochs=10)
    # ...
    
    return results

def evaluate_topk(model, trainset, testset, k=10):
    """Top-K 추천 평가 (Precision, Recall, NDCG)"""
    # testset에서 사용자별 높은 평점 영화 = relevant
    user_relevant = defaultdict(list)
    for uid, iid, rating in testset:
        if rating >= 4.0:
            user_relevant[uid].append(iid)
    
    precisions, recalls, ndcgs = [], [], []
    
    for uid in user_relevant:
        if not trainset.knows_user(trainset.to_inner_uid(uid) if hasattr(trainset, 'to_inner_uid') else uid):
            continue
        
        # 사용자가 train에서 안 본 영화에 대해 예측
        train_items = set(trainset.ur[trainset.to_inner_uid(uid)])  # (iid, rating) 튜플
        train_item_ids = {trainset.to_raw_iid(iid) for iid, _ in train_items}
        
        all_items = set(trainset.all_items())
        unseen = [trainset.to_raw_iid(iid) for iid in all_items if trainset.to_raw_iid(iid) not in train_item_ids]
        
        # 예측 + 정렬
        predictions = [(iid, model.predict(uid, iid).est) for iid in unseen[:1000]]  # 상위 1000개만 (속도)
        predictions.sort(key=lambda x: x[1], reverse=True)
        recommended = [iid for iid, _ in predictions[:k]]
        
        relevant = user_relevant[uid]
        precisions.append(precision_at_k(recommended, relevant, k))
        recalls.append(recall_at_k(recommended, relevant, k))
        ndcgs.append(ndcg_at_k(recommended, relevant, k))
    
    return {
        "precision@10": f"{np.mean(precisions):.4f}" if precisions else "N/A",
        "recall@10": f"{np.mean(recalls):.4f}" if recalls else "N/A",
        "ndcg@10": f"{np.mean(ndcgs):.4f}" if ndcgs else "N/A",
    }
```

⚠️ 위 코드는 가이드라인. Surprise API와 실제 데이터 크기에 맞게 조정 필요.
⚠️ 25M 평점 전체로 하면 느릴 수 있음. 매핑된 데이터가 너무 크면 사용자 샘플링 (예: 10,000명)으로 시작.

```python
# 데이터가 크면 샘플링
if len(mapped_ratings) > 5_000_000:
    # 최소 50개 평점 이상인 사용자 중 10,000명 샘플
    user_counts = mapped_ratings.groupby("userId").size()
    active_users = user_counts[user_counts >= 50].index.tolist()
    sampled_users = np.random.choice(active_users, size=min(10000, len(active_users)), replace=False)
    mapped_ratings = mapped_ratings[mapped_ratings["userId"].isin(sampled_users)]
```

---

=== 3단계: 하이브리드 모델 평가 ===

현재 Rule-based + CF를 조합한 하이브리드 평가:

```python
def evaluate_hybrid(rule_scores, cf_scores, alpha_values=[0.3, 0.5, 0.7]):
    """
    Rule-based와 CF를 다양한 비율로 조합하여 최적 alpha 탐색
    Score = alpha * Rule + (1-alpha) * CF
    """
    results = []
    for alpha in alpha_values:
        hybrid_scores = {}
        for movie_id in set(rule_scores) | set(cf_scores):
            rule = rule_scores.get(movie_id, 0)
            cf = cf_scores.get(movie_id, 0)
            hybrid_scores[movie_id] = alpha * rule + (1 - alpha) * cf
        
        # 정렬 후 Top-K 평가
        ...
        results.append({"model": f"hybrid_alpha_{alpha}", ...})
    
    return results
```

---

=== 4단계: 프로덕션 통합 ===

평가 결과에서 가장 좋은 모델/조합을 recommendation_engine.py에 통합.

**backend/app/api/v1/recommendation_cf.py 신규 생성:**

```python
"""
협업 필터링 모듈
- 사전 학습된 SVD 모델 로드
- 사용자별 CF 점수 예측
- Rule-based 엔진과 조합
"""

import pickle
import os
from pathlib import Path

# 학습된 모델 로드 (pickle)
MODEL_PATH = Path(__file__).parent.parent.parent / "data" / "movielens" / "svd_model.pkl"

_cf_model = None

def get_cf_model():
    global _cf_model
    if _cf_model is None and MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            _cf_model = pickle.load(f)
    return _cf_model

def predict_cf_score(user_id: int, movie_id: int) -> float | None:
    """CF 모델로 예상 평점 예측. 모델 없으면 None."""
    model = get_cf_model()
    if model is None:
        return None
    try:
        prediction = model.predict(str(user_id), str(movie_id))
        return prediction.est
    except Exception:
        return None
```

**recommendation_engine.py 수정:**

기존 `calculate_hybrid_scores` 함수에 CF 점수 통합:

```python
# 기존 가중치에 CF 추가
# CF 모델이 있고 + 사용자 평점이 충분하면 CF 가중치 활성화
cf_score = predict_cf_score(user_id, movie.id)
if cf_score is not None:
    # CF 가중치 활성화
    weights = WEIGHTS_WITH_CF  # 새 상수
    scores["cf"] = normalize_cf_score(cf_score)
else:
    # 기존 Rule-based만
    weights = WEIGHTS_WITHOUT_CF  # 기존 상수
```

**recommendation_constants.py에 CF 관련 상수 추가:**

```python
# CF 모델 사용 시 가중치 (기존 Rule + CF)
WEIGHTS_WITH_CF = {
    "mbti": 0.15,
    "weather": 0.15,
    "mood": 0.20,
    "personal": 0.15,
    "cf": 0.35,
}

# CF 모델 없을 때 (기존과 동일)
WEIGHTS_WITHOUT_CF = {
    "mbti": 0.25,
    "weather": 0.20,
    "mood": 0.30,
    "personal": 0.25,
}
```

---

=== 5단계: 모델 학습 + 저장 스크립트 ===

**backend/scripts/train_cf_model.py 신규 생성:**

```python
"""
CF 모델 학습 + 저장

실행: cd backend && python scripts/train_cf_model.py
출력: data/movielens/svd_model.pkl
"""

import pandas as pd
import pickle
from surprise import Dataset, Reader, SVD

def train_and_save():
    ratings = pd.read_csv("data/movielens/mapped_ratings.csv")
    
    reader = Reader(rating_scale=(0.5, 5.0))
    data = Dataset.load_from_df(
        ratings[["userId", "recflix_movie_id", "rating"]], reader
    )
    trainset = data.build_full_trainset()
    
    # 최적 하이퍼파라미터 (eval 결과 기반)
    model = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42)
    model.fit(trainset)
    
    with open("data/movielens/svd_model.pkl", "wb") as f:
        pickle.dump(model, f)
    
    print(f"모델 저장: data/movielens/svd_model.pkl")
    print(f"학습 데이터: {trainset.n_ratings:,} ratings, {trainset.n_users:,} users, {trainset.n_items:,} items")

if __name__ == "__main__":
    train_and_save()
```

---

=== 건드리지 말 것 ===
- frontend/ 전체
- 기존 API 엔드포인트 로직 (recommendation_engine.py에 CF 통합만)
- models/, schemas/ (DB 변경 없음)
- 모든 .md 문서 파일

---

=== 검증 ===
```bash
# Surprise 설치 확인
python -c "from surprise import SVD; print('surprise OK')"

# 평가 스크립트 실행
cd backend && python scripts/recommendation_eval.py

# 결과 확인
cat data/movielens/eval_results.csv

# 모델 학습
cd backend && python scripts/train_cf_model.py

# 모델 로드 확인
python -c "from app.api.v1.recommendation_cf import get_cf_model; print('cf module OK')"

# 기존 추천 API 동작 확인
python -c "from app.api.v1.recommendation_engine import calculate_hybrid_scores; print('engine OK')"

# Ruff 린트
ruff check backend/scripts/recommendation_eval.py backend/scripts/train_cf_model.py backend/app/api/v1/recommendation_cf.py
```

---

결과를 claude_results.md에 **기존 내용 아래에 --- 구분선 후 이어서** 저장:

```markdown
---

# Phase 3-2: 협업 필터링 구현 + 하이브리드 통합 결과

## 날짜
YYYY-MM-DD

## 생성된 파일
| 파일 | 용도 | 줄 수 |
|------|------|-------|
| backend/app/api/v1/recommendation_cf.py | CF 모델 로드 + 예측 | N줄 |
| backend/scripts/train_cf_model.py | SVD 모델 학습 + pickle 저장 | N줄 |
| backend/data/movielens/svd_model.pkl | 학습된 SVD 모델 | - |

## 수정된 파일
| 파일 | 변경 내용 |
|------|----------|
| backend/scripts/recommendation_eval.py | Item-CF, SVD, 하이브리드 평가 추가 |
| backend/app/api/v1/recommendation_engine.py | CF 점수 통합 (predict_cf_score) |
| backend/app/api/v1/recommendation_constants.py | WEIGHTS_WITH_CF 상수 추가 |
| backend/requirements.txt | scikit-surprise 추가 |

## 오프라인 평가 결과 (★ 핵심)
| 모델 | RMSE | Precision@10 | Recall@10 | NDCG@10 |
|------|------|-------------|-----------|---------|
| Popularity Baseline | N | N | N | N |
| Item-based CF | N | N | N | N |
| SVD | N | N | N | N |
| Hybrid (α=0.5) | N | N | N | N |
| Hybrid (α=0.7) | N | N | N | N |

## 최적 하이브리드 조합
- α = N (Rule-based 비중)
- 1-α = N (CF 비중)
- Baseline 대비 NDCG 개선: +N%

## 검증 결과
- Surprise: Import OK ✅
- 평가 스크립트: 실행 OK ✅
- 모델 학습: OK ✅
- CF 모듈: Import OK ✅
- 기존 추천 API: 동작 OK ✅
- Ruff: No errors ✅
```

git add -A && git commit -m 'feat: 협업 필터링 (SVD) 구현 + 오프라인 평가 + 하이브리드 통합' && git push origin HEAD:main