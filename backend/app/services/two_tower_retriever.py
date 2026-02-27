"""
Two-Tower 기반 후보 생성 서비스.

User Tower로 사용자 임베딩을 계산하고,
FAISS 인덱스에서 Top-K 유사 아이템을 검색합니다.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import faiss
import numpy as np
import torch

# backend/ 를 sys.path에 추가 (ml 모듈 접근)
_backend_dir = str(Path(__file__).resolve().parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from ml.dataset import GENRE_TO_IDX, MBTI_TO_IDX  # noqa: E402
from ml.two_tower import TwoTowerModel  # noqa: E402

logger = logging.getLogger(__name__)


class TwoTowerRetriever:
    """서버 시작 시 1회 로드하여 사용하는 Two-Tower 검색기."""

    def __init__(
        self,
        model_path: str,
        index_path: str,
        movie_id_map_path: str,
    ) -> None:
        self.model = self._load_model(model_path)
        self.index = faiss.read_index(str(index_path))
        with open(movie_id_map_path, encoding="utf-8") as f:
            self.movie_id_map: list[int] = json.load(f)
        self.ready = True
        logger.info(
            "TwoTowerRetriever loaded: %d items in index",
            self.index.ntotal,
        )

    @staticmethod
    def _load_model(model_path: str) -> TwoTowerModel:
        """모델 state_dict 로드."""
        model = TwoTowerModel()
        state = torch.load(model_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        model.eval()
        return model

    def retrieve(
        self,
        mbti: str | None,
        preferred_genres: list[str] | None = None,
        top_k: int = 200,
        exclude_ids: set[int] | None = None,
    ) -> list[tuple[int, float]]:
        """Top-K 후보 영화를 반환합니다.

        Returns:
            [(movie_id, similarity_score), ...] 최대 top_k개
        """
        exclude_ids = exclude_ids or set()

        with torch.no_grad():
            mbti_idx = torch.tensor([MBTI_TO_IDX.get(mbti or "INTJ", 0)], dtype=torch.long)
            genre_vec = self._genre_multihot(preferred_genres or []).unsqueeze(0)
            history_emb = torch.zeros(1, 128, dtype=torch.float32)

            user_vec = self.model.user_tower(mbti_idx, genre_vec, history_emb)  # (1, 128)
            user_vec_np = user_vec.numpy().astype(np.float32)

        # exclude 고려하여 여유분 요청
        search_k = top_k + len(exclude_ids) + 50
        scores, indices = self.index.search(user_vec_np, min(search_k, self.index.ntotal))

        results: list[tuple[int, float]] = []
        for score, idx in zip(scores[0], indices[0], strict=True):
            if idx < 0 or idx >= len(self.movie_id_map):
                continue
            movie_id = self.movie_id_map[idx]
            if movie_id in exclude_ids:
                continue
            results.append((movie_id, float(score)))
            if len(results) >= top_k:
                break

        return results

    @staticmethod
    def _genre_multihot(genres: list[str]) -> torch.Tensor:
        """장르 리스트 → 19차원 멀티핫."""
        vec = torch.zeros(len(GENRE_TO_IDX), dtype=torch.float32)
        for g in genres:
            idx = GENRE_TO_IDX.get(g)
            if idx is not None:
                vec[idx] = 1.0
        return vec


# ---------------------------------------------------------------------------
# 싱글톤 인스턴스 관리
# ---------------------------------------------------------------------------

_retriever: TwoTowerRetriever | None = None


def init_retriever(
    model_path: str,
    index_path: str,
    movie_id_map_path: str,
) -> TwoTowerRetriever | None:
    """Retriever 초기화. 파일이 없으면 None 반환."""
    global _retriever  # noqa: PLW0603

    for path, name in [
        (model_path, "model"),
        (index_path, "FAISS index"),
        (movie_id_map_path, "movie_id_map"),
    ]:
        if not Path(path).exists():
            logger.warning("Two-Tower %s not found: %s", name, path)
            return None

    try:
        _retriever = TwoTowerRetriever(model_path, index_path, movie_id_map_path)
        return _retriever
    except Exception:
        logger.exception("Failed to load Two-Tower retriever")
        _retriever = None
        return None


def get_retriever() -> TwoTowerRetriever | None:
    """현재 로드된 Retriever 반환 (없으면 None)."""
    return _retriever
