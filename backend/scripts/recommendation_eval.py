"""
추천 알고리즘 오프라인 평가 프레임워크

mapped_ratings.csv를 Train/Test 분리하고
Precision@K, Recall@K, NDCG@K, RMSE 지표를 계산한다.

실행: cd backend && python scripts/recommendation_eval.py

출력:
  data/movielens/eval_results.csv - 모델별 평가 결과
"""

import logging
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "movielens"

# ── 데이터 로드 + Train/Test 분리 ──


def load_and_split(
    path: Path | None = None,
    test_ratio: float = 0.2,
    min_ratings: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    timestamp 기준으로 각 사용자의 최근 test_ratio%를 테스트셋으로 분리.
    평점 min_ratings개 미만인 사용자는 제외.
    """
    if path is None:
        path = DATA_DIR / "mapped_ratings.csv"

    df = pd.read_csv(path)
    logger.info("전체 평점: %s개", f"{len(df):,}")

    # 평점 수 필터
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

    logger.info(
        "Train: %s ratings, Test: %s ratings",
        f"{len(train):,}",
        f"{len(test):,}",
    )
    logger.info(
        "Users: %s, Movies: %s",
        f"{train['userId'].nunique():,}",
        f"{train['recflix_movie_id'].nunique():,}",
    )

    return train, test


# ── 평가 지표 ──


def rmse(predictions: list[float], actuals: list[float]) -> float:
    """Root Mean Squared Error"""
    return float(math.sqrt(np.mean((np.array(predictions) - np.array(actuals)) ** 2)))


def precision_at_k(recommended: list[int], relevant: set[int], k: int = 10) -> float:
    """추천 상위 K개 중 관련 아이템 비율"""
    rec_k = recommended[:k]
    return len(set(rec_k) & relevant) / k


def recall_at_k(recommended: list[int], relevant: set[int], k: int = 10) -> float:
    """관련 아이템 중 추천에 포함된 비율"""
    if len(relevant) == 0:
        return 0.0
    rec_k = recommended[:k]
    return len(set(rec_k) & relevant) / len(relevant)


def ndcg_at_k(recommended: list[int], relevant: set[int], k: int = 10) -> float:
    """Normalized Discounted Cumulative Gain"""
    rec_k = recommended[:k]
    dcg = sum(
        1.0 / math.log2(i + 2) for i, item in enumerate(rec_k) if item in relevant
    )
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), k)))
    return dcg / idcg if idcg > 0 else 0.0


# ── 베이스라인: 인기도 기반 추천 ──


def popularity_baseline(
    train: pd.DataFrame,
    test: pd.DataFrame,
    k: int = 10,
    min_count: int = 50,
) -> dict[str, str]:
    """가장 많이 평가받고 평점이 높은 영화를 모든 사용자에게 동일하게 추천"""
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

    logger.info("  인기 영화 Top %d 선정 (최소 %d평점, 평균 평점순)", k, min_count)

    precisions: list[float] = []
    recalls: list[float] = []
    ndcgs: list[float] = []

    for _, group in test.groupby("userId"):
        relevant = set(
            group[group["rating"] >= 4.0]["recflix_movie_id"].tolist()
        )
        if len(relevant) == 0:
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


# ── 베이스라인: 글로벌 평균 예측 ──


def global_mean_baseline(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> dict[str, str]:
    """모든 예측을 학습셋 전체 평균 평점으로"""
    global_mean = train["rating"].mean()
    predictions = [global_mean] * len(test)
    actuals = test["rating"].tolist()

    return {
        "model": "global_mean_baseline",
        "rmse": f"{rmse(predictions, actuals):.4f}",
        "global_mean": f"{global_mean:.4f}",
    }


# ── 베이스라인: 영화별 평균 예측 ──


def item_mean_baseline(
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> dict[str, str]:
    """각 영화의 학습셋 평균 평점으로 예측 (없으면 전체 평균)"""
    global_mean = train["rating"].mean()
    movie_means = train.groupby("recflix_movie_id")["rating"].mean().to_dict()

    predictions = [
        movie_means.get(mid, global_mean)
        for mid in test["recflix_movie_id"]
    ]
    actuals = test["rating"].tolist()

    return {
        "model": "item_mean_baseline",
        "rmse": f"{rmse(predictions, actuals):.4f}",
        "coverage": f"{sum(1 for m in test['recflix_movie_id'] if m in movie_means) / len(test) * 100:.1f}%",
    }


# ── 메인 ──


def main() -> None:
    logger.info("=== RecFlix 오프라인 평가 ===\n")

    train, test = load_and_split()
    results: list[dict[str, str]] = []

    # 1. Popularity Baseline (랭킹 지표)
    logger.info("\n--- Popularity Baseline ---")
    pop = popularity_baseline(train, test)
    for k, v in pop.items():
        logger.info("  %s: %s", k, v)
    results.append(pop)

    # 2. Global Mean Baseline (평점 예측 지표)
    logger.info("\n--- Global Mean Baseline ---")
    gm = global_mean_baseline(train, test)
    for k, v in gm.items():
        logger.info("  %s: %s", k, v)
    results.append(gm)

    # 3. Item Mean Baseline (평점 예측 지표)
    logger.info("\n--- Item Mean Baseline ---")
    im = item_mean_baseline(train, test)
    for k, v in im.items():
        logger.info("  %s: %s", k, v)
    results.append(im)

    # 결과 저장
    output = DATA_DIR / "eval_results.csv"
    pd.DataFrame(results).to_csv(output, index=False)
    logger.info("\n결과 저장: %s", output)


if __name__ == "__main__":
    main()
