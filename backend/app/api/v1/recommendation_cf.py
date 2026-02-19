"""
협업 필터링 모듈

사전 학습된 SVD 모델에서 item_bias를 로드하여
영화별 CF 품질 점수를 제공한다.

RecFlix 사용자는 MovieLens에 없으므로,
CF 점수 = global_mean + item_bias (아이템 품질 추정).
"""

import logging
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent.parent.parent.parent / "data" / "movielens" / "svd_model.pkl"

_cf_data: dict | None = None


def _load_model() -> dict | None:
    """SVD 모델 데이터 로드 (lazy singleton)"""
    global _cf_data
    if _cf_data is not None:
        return _cf_data
    if not MODEL_PATH.exists():
        logger.warning("CF 모델 없음: %s", MODEL_PATH)
        return None
    try:
        with open(MODEL_PATH, "rb") as f:
            _cf_data = pickle.load(f)
        logger.info(
            "CF 모델 로드: items=%d, global_mean=%.4f",
            len(_cf_data["item_map"]),
            _cf_data["global_mean"],
        )
        return _cf_data
    except Exception:
        logger.exception("CF 모델 로드 실패")
        return None


def predict_cf_score(movie_id: int) -> float | None:
    """
    영화의 CF 품질 점수 예측.

    RecFlix 사용자는 MovieLens에 없으므로
    global_mean + item_bias를 반환 (0.5~5.0 범위).
    모델이 없거나 해당 영화가 매핑에 없으면 None.
    """
    data = _load_model()
    if data is None:
        return None

    item_map: dict = data["item_map"]
    i_idx = item_map.get(movie_id)
    if i_idx is None:
        return None

    score = data["global_mean"] + data["item_bias"][i_idx]
    return float(np.clip(score, 0.5, 5.0))


def normalize_cf_score(cf_score: float) -> float:
    """CF 점수(0.5~5.0)를 0~1 범위로 정규화"""
    return (cf_score - 0.5) / 4.5


def is_cf_available() -> bool:
    """CF 모델 사용 가능 여부"""
    return _load_model() is not None
