"""
추천 알고리즘 오프라인 평가 프레임워크

mapped_ratings.csv를 Train/Test 분리하고
Precision@K, Recall@K, NDCG@K, RMSE 지표를 계산한다.
베이스라인 + SVD 협업 필터링 + 하이브리드 평가.

실행: cd backend && python scripts/recommendation_eval.py

출력:
  data/movielens/eval_results.csv - 모델별 평가 결과
"""

import logging
import math
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import svds

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "movielens"
RANDOM_SEED = 42

# ── 데이터 로드 + Train/Test 분리 ──


def load_and_split(
    test_ratio: float = 0.2,
    min_ratings: int = 5,
    sampled_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """timestamp 기준 각 사용자의 최근 test_ratio%를 테스트셋으로 분리."""
    df = sampled_df if sampled_df is not None else pd.read_csv(DATA_DIR / "mapped_ratings.csv")

    logger.info("평점: %s개", f"{len(df):,}")

    user_counts = df.groupby("userId").size()
    active_users = user_counts[user_counts >= min_ratings].index
    df = df[df["userId"].isin(active_users)]
    logger.info("활성 사용자 (>=%d평점): %s명", min_ratings, f"{len(active_users):,}")

    train_parts: list[pd.DataFrame] = []
    test_parts: list[pd.DataFrame] = []

    for _, group in df.groupby("userId"):
        group = group.sort_values("timestamp")
        split_idx = int(len(group) * (1 - test_ratio))
        train_parts.append(group.iloc[:split_idx])
        test_parts.append(group.iloc[split_idx:])

    train = pd.concat(train_parts)
    test = pd.concat(test_parts)

    logger.info("Train: %s, Test: %s", f"{len(train):,}", f"{len(test):,}")
    logger.info(
        "Users: %s, Movies: %s",
        f"{train['userId'].nunique():,}",
        f"{train['recflix_movie_id'].nunique():,}",
    )
    return train, test


def sample_users(
    df: pd.DataFrame,
    n_users: int = 10000,
    min_ratings: int = 20,
) -> pd.DataFrame:
    """활성 사용자 n_users명을 샘플링."""
    rng = np.random.RandomState(RANDOM_SEED)
    user_counts = df.groupby("userId").size()
    candidates = user_counts[user_counts >= min_ratings].index.tolist()
    sampled = rng.choice(candidates, size=min(n_users, len(candidates)), replace=False)
    return df[df["userId"].isin(sampled)]


# ── 평가 지표 ──


def rmse(predictions: list[float], actuals: list[float]) -> float:
    return float(math.sqrt(np.mean((np.array(predictions) - np.array(actuals)) ** 2)))


def precision_at_k(recommended: list[int], relevant: set[int], k: int = 10) -> float:
    rec_k = recommended[:k]
    return len(set(rec_k) & relevant) / k


def recall_at_k(recommended: list[int], relevant: set[int], k: int = 10) -> float:
    if len(relevant) == 0:
        return 0.0
    rec_k = recommended[:k]
    return len(set(rec_k) & relevant) / len(relevant)


def ndcg_at_k(recommended: list[int], relevant: set[int], k: int = 10) -> float:
    rec_k = recommended[:k]
    dcg = sum(
        1.0 / math.log2(i + 2) for i, item in enumerate(rec_k) if item in relevant
    )
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / idcg if idcg > 0 else 0.0


# ── 베이스라인: 인기도 기반 ──


def popularity_baseline(
    train: pd.DataFrame, test: pd.DataFrame, k: int = 10, min_count: int = 50,
) -> dict[str, str]:
    movie_stats = (
        train.groupby("recflix_movie_id")
        .agg(avg_rating=("rating", "mean"), count=("rating", "count"))
        .reset_index()
    )
    popular = (
        movie_stats[movie_stats["count"] >= min_count]
        .sort_values("avg_rating", ascending=False)["recflix_movie_id"]
        .tolist()[:k]
    )
    logger.info("  인기 영화 Top %d 선정 (최소 %d평점)", k, min_count)

    precisions, recalls, ndcgs = [], [], []
    for _, group in test.groupby("userId"):
        relevant = set(group[group["rating"] >= 4.0]["recflix_movie_id"].tolist())
        if not relevant:
            continue
        precisions.append(precision_at_k(popular, relevant, k))
        recalls.append(recall_at_k(popular, relevant, k))
        ndcgs.append(ndcg_at_k(popular, relevant, k))

    return {
        "model": "popularity_baseline",
        f"precision@{k}": f"{np.mean(precisions):.4f}",
        f"recall@{k}": f"{np.mean(recalls):.4f}",
        f"ndcg@{k}": f"{np.mean(ndcgs):.4f}",
        "evaluated_users": str(len(precisions)),
    }


def global_mean_baseline(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, str]:
    gm = train["rating"].mean()
    preds = [gm] * len(test)
    return {
        "model": "global_mean_baseline",
        "rmse": f"{rmse(preds, test['rating'].tolist()):.4f}",
        "global_mean": f"{gm:.4f}",
    }


def item_mean_baseline(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, str]:
    gm = train["rating"].mean()
    movie_means = train.groupby("recflix_movie_id")["rating"].mean().to_dict()
    preds = [movie_means.get(m, gm) for m in test["recflix_movie_id"]]
    coverage = sum(1 for m in test["recflix_movie_id"] if m in movie_means) / len(test)
    return {
        "model": "item_mean_baseline",
        "rmse": f"{rmse(preds, test['rating'].tolist()):.4f}",
        "coverage": f"{coverage * 100:.1f}%",
    }


# ── SVD 협업 필터링 (scipy) ──


class SVDModel:
    """Truncated SVD with bias terms for collaborative filtering."""

    def __init__(self, n_factors: int = 100):
        self.n_factors = n_factors
        self.global_mean: float = 0.0
        self.user_bias: np.ndarray = np.array([])
        self.item_bias: np.ndarray = np.array([])
        self.user_factors: np.ndarray = np.array([])
        self.item_factors: np.ndarray = np.array([])
        self.user_map: dict[int, int] = {}
        self.item_map: dict[int, int] = {}
        self.item_map_inv: dict[int, int] = {}

    def fit(self, train_df: pd.DataFrame) -> "SVDModel":
        """학습: sparse matrix → bias 제거 → truncated SVD"""
        users = train_df["userId"].unique()
        items = train_df["recflix_movie_id"].unique()
        self.user_map = {u: i for i, u in enumerate(users)}
        self.item_map = {m: i for i, m in enumerate(items)}
        self.item_map_inv = {i: m for m, i in self.item_map.items()}

        n_users, n_items = len(users), len(items)
        logger.info("  Matrix: %d users x %d items", n_users, n_items)

        rows = train_df["userId"].map(self.user_map).values
        cols = train_df["recflix_movie_id"].map(self.item_map).values
        vals = train_df["rating"].values.astype(np.float32)

        R = csr_matrix((vals, (rows, cols)), shape=(n_users, n_items))

        # Compute biases
        self.global_mean = float(vals.mean())
        rating_count = R.copy()
        rating_count.data = np.ones_like(rating_count.data)

        user_sum = np.array(R.sum(axis=1)).flatten()
        user_cnt = np.array(rating_count.sum(axis=1)).flatten()
        self.user_bias = np.where(user_cnt > 0, user_sum / user_cnt - self.global_mean, 0.0)

        item_sum = np.array(R.sum(axis=0)).flatten()
        item_cnt = np.array(rating_count.sum(axis=0)).flatten()
        self.item_bias = np.where(item_cnt > 0, item_sum / item_cnt - self.global_mean, 0.0)

        # Remove biases (vectorized on sparse COO)
        R_coo = R.tocoo()
        debiased_data = (
            R_coo.data
            - self.global_mean
            - self.user_bias[R_coo.row]
            - self.item_bias[R_coo.col]
        ).astype(np.float64)
        R_debiased = csr_matrix(
            (debiased_data, (R_coo.row, R_coo.col)), shape=R.shape
        )

        # Truncated SVD
        k = min(self.n_factors, min(n_users, n_items) - 1)
        logger.info("  SVD 분해 (k=%d)...", k)
        U, sigma, Vt = svds(R_debiased, k=k)
        S_sqrt = np.diag(np.sqrt(sigma))
        self.user_factors = U @ S_sqrt          # (n_users, k)
        self.item_factors = (S_sqrt @ Vt).T     # (n_items, k)

        logger.info("  학습 완료")
        return self

    def predict(self, user_id: int, item_id: int) -> float:
        """단일 (user, item) 예측"""
        u_idx = self.user_map.get(user_id)
        i_idx = self.item_map.get(item_id)
        if u_idx is None or i_idx is None:
            # Unknown user/item → global mean + available bias
            score = self.global_mean
            if u_idx is not None:
                score += self.user_bias[u_idx]
            if i_idx is not None:
                score += self.item_bias[i_idx]
            return float(np.clip(score, 0.5, 5.0))
        score = (
            self.global_mean
            + self.user_bias[u_idx]
            + self.item_bias[i_idx]
            + float(self.user_factors[u_idx] @ self.item_factors[i_idx])
        )
        return float(np.clip(score, 0.5, 5.0))

    def predict_all_items(self, user_id: int) -> np.ndarray | None:
        """한 사용자의 전체 아이템 예측 점수 (벡터 연산)"""
        u_idx = self.user_map.get(user_id)
        if u_idx is None:
            return None
        scores = (
            self.global_mean
            + self.user_bias[u_idx]
            + self.item_bias
            + self.item_factors @ self.user_factors[u_idx]
        )
        return np.clip(scores, 0.5, 5.0)


def svd_rmse_eval(
    model: SVDModel, test_df: pd.DataFrame,
) -> dict[str, str]:
    """SVD 모델의 RMSE 평가 (벡터화)"""
    actuals = test_df["rating"].values
    user_ids = test_df["userId"].values
    item_ids = test_df["recflix_movie_id"].values

    # 벡터화: 매핑 가능한 항목은 행렬 연산, 나머지는 fallback
    u_idxs = np.array([model.user_map.get(int(u), -1) for u in user_ids])
    i_idxs = np.array([model.item_map.get(int(m), -1) for m in item_ids])

    preds = np.full(len(actuals), model.global_mean)
    known_mask = (u_idxs >= 0) & (i_idxs >= 0)
    u_known = u_idxs[known_mask]
    i_known = i_idxs[known_mask]
    preds[known_mask] = (
        model.global_mean
        + model.user_bias[u_known]
        + model.item_bias[i_known]
        + np.sum(model.user_factors[u_known] * model.item_factors[i_known], axis=1)
    )
    # user만 알려진 경우
    u_only = (u_idxs >= 0) & (i_idxs < 0)
    preds[u_only] = model.global_mean + model.user_bias[u_idxs[u_only]]
    # item만 알려진 경우
    i_only = (u_idxs < 0) & (i_idxs >= 0)
    preds[i_only] = model.global_mean + model.item_bias[i_idxs[i_only]]
    preds = np.clip(preds, 0.5, 5.0)

    err = float(np.sqrt(np.mean((preds - actuals) ** 2)))
    return {"model": "svd", "rmse": f"{err:.4f}"}


def svd_topk_eval(
    model: SVDModel,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    k: int = 10,
    max_users: int = 2000,
) -> dict[str, str]:
    """SVD Top-K 평가 (벡터 연산으로 빠르게)"""
    rng = random.Random(RANDOM_SEED)

    # 테스트셋에서 사용자별 relevant 아이템 (rating >= 4.0)
    user_relevant: dict[int, set[int]] = {}
    for uid, group in test_df.groupby("userId"):
        rel = set(group[group["rating"] >= 4.0]["recflix_movie_id"].tolist())
        if rel:
            user_relevant[int(uid)] = rel

    # 학습셋에서 사용자별 본 아이템
    user_train_items: dict[int, set[int]] = {}
    for uid, group in train_df.groupby("userId"):
        user_train_items[int(uid)] = set(group["recflix_movie_id"].tolist())

    eval_users = list(user_relevant.keys())
    if len(eval_users) > max_users:
        eval_users = rng.sample(eval_users, max_users)

    precisions, recalls, ndcgs = [], [], []

    # item index → raw id 매핑 배열
    all_raw_ids = np.array([model.item_map_inv.get(i, -1) for i in range(len(model.item_bias))])

    for uid in eval_users:
        scores = model.predict_all_items(uid)
        if scores is None:
            continue

        seen = user_train_items.get(uid, set())
        # 안 본 아이템 마스크
        seen_mask = np.array([all_raw_ids[i] in seen for i in range(len(scores))])
        scores[seen_mask] = -1.0

        # 상위 K개 인덱스
        top_idxs = np.argpartition(scores, -k)[-k:]
        top_idxs = top_idxs[np.argsort(scores[top_idxs])[::-1]]
        recommended = [int(all_raw_ids[i]) for i in top_idxs if all_raw_ids[i] >= 0]

        relevant = user_relevant[uid]
        precisions.append(precision_at_k(recommended, relevant, k))
        recalls.append(recall_at_k(recommended, relevant, k))
        ndcgs.append(ndcg_at_k(recommended, relevant, k))

    return {
        "model": "svd",
        f"precision@{k}": f"{np.mean(precisions):.4f}",
        f"recall@{k}": f"{np.mean(recalls):.4f}",
        f"ndcg@{k}": f"{np.mean(ndcgs):.4f}",
        "evaluated_users": str(len(precisions)),
    }


# ── 하이브리드 평가: Popularity + SVD ──


def hybrid_topk_eval(
    model: SVDModel,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    alpha_values: list[float] | None = None,
    k: int = 10,
    max_users: int = 2000,
) -> list[dict[str, str]]:
    """Rule(인기도) + CF(SVD) 하이브리드 평가. alpha = Rule 비중."""
    if alpha_values is None:
        alpha_values = [0.3, 0.5, 0.7]

    rng = random.Random(RANDOM_SEED)

    # 영화별 인기도 점수 (평균평점, 0-1 정규화)
    movie_stats = train_df.groupby("recflix_movie_id")["rating"].mean()
    pop_min, pop_max = movie_stats.min(), movie_stats.max()
    pop_range = pop_max - pop_min if pop_max > pop_min else 1.0
    pop_norm = ((movie_stats - pop_min) / pop_range).to_dict()

    user_relevant: dict[int, set[int]] = {}
    for uid, group in test_df.groupby("userId"):
        rel = set(group[group["rating"] >= 4.0]["recflix_movie_id"].tolist())
        if rel:
            user_relevant[int(uid)] = rel

    user_train_items: dict[int, set[int]] = {}
    for uid, group in train_df.groupby("userId"):
        user_train_items[int(uid)] = set(group["recflix_movie_id"].tolist())

    eval_users = list(user_relevant.keys())
    if len(eval_users) > max_users:
        eval_users = rng.sample(eval_users, max_users)

    results = []
    for alpha in alpha_values:
        precisions, recalls, ndcgs = [], [], []

        for uid in eval_users:
            svd_scores = model.predict_all_items(uid)
            if svd_scores is None:
                continue

            seen = user_train_items.get(uid, set())
            item_scores = []
            for i_idx, svd_s in enumerate(svd_scores):
                raw_id = model.item_map_inv.get(i_idx)
                if raw_id and raw_id not in seen:
                    cf_norm = (svd_s - 0.5) / 4.5  # 0.5~5.0 → 0~1
                    pop_s = pop_norm.get(raw_id, 0.5)
                    hybrid = alpha * pop_s + (1 - alpha) * cf_norm
                    item_scores.append((raw_id, hybrid))

            item_scores.sort(key=lambda x: x[1], reverse=True)
            recommended = [iid for iid, _ in item_scores[:k]]

            relevant = user_relevant[uid]
            precisions.append(precision_at_k(recommended, relevant, k))
            recalls.append(recall_at_k(recommended, relevant, k))
            ndcgs.append(ndcg_at_k(recommended, relevant, k))

        results.append({
            "model": f"hybrid_alpha_{alpha}",
            f"precision@{k}": f"{np.mean(precisions):.4f}",
            f"recall@{k}": f"{np.mean(recalls):.4f}",
            f"ndcg@{k}": f"{np.mean(ndcgs):.4f}",
            "evaluated_users": str(len(precisions)),
        })
    return results


# ── 메인 ──


def main() -> None:
    logger.info("=== RecFlix 오프라인 평가 ===\n")

    # 샘플링: 10K 사용자 (20+ 평점)
    full_df = pd.read_csv(DATA_DIR / "mapped_ratings.csv")
    sampled_df = sample_users(full_df, n_users=10000, min_ratings=20)
    logger.info("샘플: %s ratings, %s users\n",
                f"{len(sampled_df):,}", f"{sampled_df['userId'].nunique():,}")

    train, test = load_and_split(sampled_df=sampled_df)
    results: list[dict[str, str]] = []

    # 1. Popularity Baseline
    logger.info("\n--- Popularity Baseline ---")
    pop = popularity_baseline(train, test)
    for kk, v in pop.items():
        logger.info("  %s: %s", kk, v)
    results.append(pop)

    # 2. Global Mean Baseline
    logger.info("\n--- Global Mean Baseline ---")
    gm = global_mean_baseline(train, test)
    for kk, v in gm.items():
        logger.info("  %s: %s", kk, v)
    results.append(gm)

    # 3. Item Mean Baseline
    logger.info("\n--- Item Mean Baseline ---")
    im = item_mean_baseline(train, test)
    for kk, v in im.items():
        logger.info("  %s: %s", kk, v)
    results.append(im)

    # 4. SVD (scipy)
    logger.info("\n--- SVD (n_factors=100) ---")
    svd = SVDModel(n_factors=100)
    svd.fit(train)

    logger.info("  RMSE 평가...")
    svd_rmse = svd_rmse_eval(svd, test)
    logger.info("  rmse: %s", svd_rmse["rmse"])

    logger.info("  Top-K 평가 (2000 users)...")
    svd_topk = svd_topk_eval(svd, train, test, k=10, max_users=2000)
    for kk, v in svd_topk.items():
        logger.info("  %s: %s", kk, v)

    # Merge SVD results
    svd_combined = {**svd_rmse, **svd_topk}
    results.append(svd_combined)

    # 5. Hybrid (Popularity + SVD)
    logger.info("\n--- Hybrid (Popularity + SVD) ---")
    hybrid_results = hybrid_topk_eval(
        svd, train, test, alpha_values=[0.3, 0.5, 0.7], k=10, max_users=2000,
    )
    for hr in hybrid_results:
        for kk, v in hr.items():
            logger.info("  %s: %s", kk, v)
        logger.info("")
        results.append(hr)

    # 결과 저장
    output = DATA_DIR / "eval_results.csv"
    pd.DataFrame(results).to_csv(output, index=False)
    logger.info("결과 저장: %s", output)


if __name__ == "__main__":
    main()
