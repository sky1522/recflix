"""
CF 모델(SVD) 학습 + 저장

mapped_ratings.csv 전체로 SVD 학습 후 pickle로 저장.
프로덕션 recommendation_cf.py에서 로드하여 사용.

실행: cd backend && python scripts/train_cf_model.py
출력: data/movielens/svd_model.pkl
"""

import logging
import pickle
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


def train_and_save(n_factors: int = 100, max_users: int = 50000) -> None:
    """SVD 모델 학습 + pickle 저장"""
    ratings_path = DATA_DIR / "mapped_ratings.csv"
    logger.info("데이터 로드: %s", ratings_path)
    df = pd.read_csv(ratings_path)
    logger.info("전체: %s ratings, %s users, %s items",
                f"{len(df):,}",
                f"{df['userId'].nunique():,}",
                f"{df['recflix_movie_id'].nunique():,}")

    # 활성 사용자 샘플링 (메모리 제한)
    user_counts = df.groupby("userId").size()
    active = user_counts[user_counts >= 20].index.tolist()
    if len(active) > max_users:
        rng = np.random.RandomState(42)
        active = rng.choice(active, size=max_users, replace=False).tolist()
    df = df[df["userId"].isin(active)]
    logger.info("학습 대상: %s ratings, %s users",
                f"{len(df):,}", f"{df['userId'].nunique():,}")

    # ID 매핑
    users = df["userId"].unique()
    items = df["recflix_movie_id"].unique()
    user_map = {u: i for i, u in enumerate(users)}
    item_map = {m: i for i, m in enumerate(items)}

    n_users, n_items = len(users), len(items)
    logger.info("Matrix: %d users x %d items", n_users, n_items)

    rows = df["userId"].map(user_map).values
    cols = df["recflix_movie_id"].map(item_map).values
    vals = df["rating"].values.astype(np.float32)

    R = csr_matrix((vals, (rows, cols)), shape=(n_users, n_items))

    # Bias 계산
    global_mean = float(vals.mean())
    count_mat = R.copy()
    count_mat.data = np.ones_like(count_mat.data)

    user_sum = np.array(R.sum(axis=1)).flatten()
    user_cnt = np.array(count_mat.sum(axis=1)).flatten()
    user_bias = np.where(user_cnt > 0, user_sum / user_cnt - global_mean, 0.0)

    item_sum = np.array(R.sum(axis=0)).flatten()
    item_cnt = np.array(count_mat.sum(axis=0)).flatten()
    item_bias = np.where(item_cnt > 0, item_sum / item_cnt - global_mean, 0.0)

    # Bias 제거 (sparse COO 벡터화)
    R_coo = R.tocoo()
    debiased = (
        R_coo.data - global_mean - user_bias[R_coo.row] - item_bias[R_coo.col]
    ).astype(np.float64)
    R_debiased = csr_matrix((debiased, (R_coo.row, R_coo.col)), shape=R.shape)

    # Truncated SVD
    k = min(n_factors, min(n_users, n_items) - 1)
    logger.info("SVD 분해 (k=%d)...", k)
    U, sigma, Vt = svds(R_debiased, k=k)
    S_sqrt = np.diag(np.sqrt(sigma))
    user_factors = U @ S_sqrt       # (n_users, k)
    item_factors = (S_sqrt @ Vt).T  # (n_items, k)
    logger.info("SVD 완료")

    # 모델 저장 (item 정보만 - 프로덕션에서 user 정보는 불필요)
    model_data = {
        "global_mean": global_mean,
        "item_bias": item_bias,
        "item_factors": item_factors,
        "user_bias": user_bias,
        "user_factors": user_factors,
        "item_map": item_map,
        "user_map": user_map,
        "n_factors": k,
    }

    output_path = DATA_DIR / "svd_model.pkl"
    with open(output_path, "wb") as f:
        pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info("모델 저장: %s (%.1f MB)", output_path, size_mb)
    logger.info("global_mean=%.4f, items=%d, users=%d, factors=%d",
                global_mean, n_items, n_users, k)


if __name__ == "__main__":
    train_and_save()
