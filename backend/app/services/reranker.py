"""LightGBM 기반 CTR 예측 재랭커 서빙 모듈.

Two-Tower 후보 200개 → GBDT 재랭킹 50개 → 하이브리드 품질보정 20개.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np

logger = logging.getLogger(__name__)

# --- Feature constants (train_reranker.py와 동기화) ---

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP",
]
MBTI_TO_IDX = {m: i for i, m in enumerate(MBTI_TYPES)}

GENRE_LIST = [
    "SF", "TV 영화", "가족", "공포", "다큐멘터리",
    "드라마", "로맨스", "모험", "미스터리", "범죄",
    "서부", "스릴러", "애니메이션", "액션", "역사",
    "음악", "전쟁", "코미디", "판타지",
]
GENRE_TO_IDX = {g: i for i, g in enumerate(GENRE_LIST)}

EMOTION_KEYS = ["healing", "tension", "energy", "romance", "deep", "fantasy", "light"]

WEATHER_TYPES = ["sunny", "rainy", "cloudy", "snowy"]
WEATHER_TO_IDX = {w: i for i, w in enumerate(WEATHER_TYPES)}

MOOD_TYPES = ["happy", "sad", "excited", "calm", "tired", "emotional"]
MOOD_TO_IDX = {m: i for i, m in enumerate(MOOD_TYPES)}

N_FEATURES = 76  # 16+19+19+1+7+4+6+2+2


class LGBMReranker:
    """LightGBM CTR 예측 재랭커."""

    def __init__(self, model_path: str) -> None:
        self.model = lgb.Booster(model_file=str(model_path))
        self.ready = True
        logger.info("LGBMReranker loaded: %s", model_path)

    def rerank(
        self,
        candidates: list[dict],
        context: dict,
        top_k: int = 50,
    ) -> list[dict]:
        """후보 리스트를 CTR 확률 기준으로 재랭킹.

        Args:
            candidates: [{movie_id, genres, weighted_score, emotion_tags,
                          mbti_score, weather_score, tt_score, rank, ...}]
            context: {mbti, weather, mood}
            top_k: 반환 수

        Returns:
            CTR 확률 내림차순 정렬된 상위 top_k 후보.
            에러 시 원본 순서 유지 (추천 중단 방지).
        """
        try:
            t0 = time.perf_counter()
            features = self._prepare_features(candidates, context)
            scores = self.model.predict(features)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            for cand, score in zip(candidates, scores, strict=True):
                cand["rerank_score"] = float(score)

            sorted_candidates = sorted(
                candidates, key=lambda x: x["rerank_score"], reverse=True,
            )

            logger.info(
                "reranker_ok",
                extra={
                    "n_candidates": len(candidates),
                    "top_k": top_k,
                    "elapsed_ms": round(elapsed_ms, 2),
                    "top_score": round(float(sorted_candidates[0]["rerank_score"]), 4) if sorted_candidates else 0,
                },
            )
            return sorted_candidates[:top_k]
        except Exception:
            logger.exception("reranker_failed")
            return candidates[:top_k]

    def _prepare_features(
        self,
        candidates: list[dict],
        context: dict,
    ) -> np.ndarray:
        """후보 리스트 → (N, 76) 피처 행렬."""
        n = len(candidates)
        x = np.zeros((n, N_FEATURES), dtype=np.float32)

        mbti = context.get("mbti", "")
        weather = context.get("weather", "")
        mood = context.get("mood", "")

        # 공통 컨텍스트 피처 (모든 행 동일)
        mbti_idx = MBTI_TO_IDX.get(mbti)
        weather_idx = WEATHER_TO_IDX.get(weather)
        mood_idx = MOOD_TO_IDX.get(mood)

        for i, cand in enumerate(candidates):
            offset = 0

            # mbti one-hot (16)
            if mbti_idx is not None:
                x[i, offset + mbti_idx] = 1.0
            offset += len(MBTI_TYPES)

            # user genres (19) — 후보별 genre를 proxy로 사용
            genres = cand.get("genres", [])
            for g in genres:
                gidx = GENRE_TO_IDX.get(g)
                if gidx is not None:
                    x[i, offset + gidx] = 1.0
            offset += len(GENRE_LIST)

            # item genres (19)
            for g in genres:
                gidx = GENRE_TO_IDX.get(g)
                if gidx is not None:
                    x[i, offset + gidx] = 1.0
            offset += len(GENRE_LIST)

            # weighted_score (1)
            x[i, offset] = (cand.get("weighted_score") or 0) / 10.0
            offset += 1

            # emotion tags (7)
            etags = cand.get("emotion_tags") or {}
            for j, k in enumerate(EMOTION_KEYS):
                x[i, offset + j] = etags.get(k, 0.0)
            offset += len(EMOTION_KEYS)

            # weather one-hot (4)
            if weather_idx is not None:
                x[i, offset + weather_idx] = 1.0
            offset += len(WEATHER_TYPES)

            # mood one-hot (6)
            if mood_idx is not None:
                x[i, offset + mood_idx] = 1.0
            offset += len(MOOD_TYPES)

            # cross features
            x[i, offset] = cand.get("mbti_score", 0.0)
            x[i, offset + 1] = cand.get("weather_score", 0.0)
            offset += 2

            # candidate features
            x[i, offset] = cand.get("tt_score", 0.0)
            rank = cand.get("rank", 0)
            x[i, offset + 1] = 1.0 / (rank + 1)

        return x


# ---------------------------------------------------------------------------
# 싱글톤 인스턴스 관리
# ---------------------------------------------------------------------------

_reranker: LGBMReranker | None = None


def init_reranker(model_path: str) -> LGBMReranker | None:
    """Reranker 초기화. 파일이 없으면 None 반환."""
    global _reranker  # noqa: PLW0603

    if not Path(model_path).exists():
        logger.warning("Reranker model not found: %s", model_path)
        return None

    try:
        _reranker = LGBMReranker(model_path)
        return _reranker
    except Exception:
        logger.exception("Failed to load LGBMReranker")
        _reranker = None
        return None


def get_reranker() -> LGBMReranker | None:
    """현재 로드된 Reranker 반환 (없으면 None)."""
    return _reranker
