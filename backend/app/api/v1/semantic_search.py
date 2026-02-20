"""
In-memory vector search using NumPy.
Loads pre-computed movie embeddings at server startup.
"""
import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# In-memory vector index
_corpus_embeddings: np.ndarray | None = None  # (N, 1024), L2 normalized
_movie_ids: list[int] = []  # index → movie_id mapping

EMBEDDINGS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "embeddings"


def load_embeddings() -> None:
    """서버 시작 시 임베딩을 메모리에 로드."""
    global _corpus_embeddings, _movie_ids

    emb_path = EMBEDDINGS_DIR / "movie_embeddings.npy"
    idx_path = EMBEDDINGS_DIR / "movie_id_index.json"

    if not emb_path.exists():
        logger.warning("Embedding file not found: %s — semantic search disabled", emb_path)
        return

    if not idx_path.exists():
        logger.warning("Movie ID index not found: %s — semantic search disabled", idx_path)
        return

    try:
        raw = np.load(str(emb_path)).astype(np.float32)

        # L2 정규화 (코사인 유사도 → 내적으로 변환)
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        norms[norms == 0] = 1  # zero-vector 방지
        _corpus_embeddings = raw / norms

        with open(idx_path, encoding="utf-8") as f:
            idx_map: dict[str, int] = json.load(f)
        _movie_ids = [idx_map[str(i)] for i in range(len(idx_map))]

        logger.info(
            "Loaded %d movie embeddings (%d dims, %.1f MB)",
            len(_movie_ids),
            _corpus_embeddings.shape[1],
            _corpus_embeddings.nbytes / 1024 / 1024,
        )
    except Exception as e:
        logger.error("Failed to load embeddings: %s", e)
        _corpus_embeddings = None
        _movie_ids = []


def search_similar(
    query_embedding: np.ndarray, top_k: int = 100
) -> list[tuple[int, float]]:
    """코사인 유사도 기반 Top-K 검색. (movie_id, score) 리스트 반환."""
    if _corpus_embeddings is None or len(_movie_ids) == 0:
        return []

    query_norm = query_embedding / np.linalg.norm(query_embedding)
    scores = _corpus_embeddings @ query_norm  # (N,)

    # Top-K 추출 (argpartition은 O(N), argsort O(N log N)보다 빠름)
    if top_k < len(scores):
        top_indices = np.argpartition(scores, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
    else:
        top_indices = np.argsort(scores)[::-1][:top_k]

    return [(int(_movie_ids[i]), float(scores[i])) for i in top_indices]


def is_semantic_search_available() -> bool:
    """시맨틱 검색 사용 가능 여부."""
    return _corpus_embeddings is not None and len(_movie_ids) > 0
