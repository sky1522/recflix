"""
Two-Tower 학습용 데이터셋.

JSONL 파일에서 (user_features, item_features) positive pair를 로드합니다.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

# RecFlix 19개 장르 (한국어, DB 기준)
GENRE_LIST = [
    "SF", "TV 영화", "가족", "공포", "다큐멘터리",
    "드라마", "로맨스", "모험", "미스터리", "범죄",
    "서부", "스릴러", "애니메이션", "액션", "역사",
    "음악", "전쟁", "코미디", "판타지",
]
GENRE_TO_IDX = {g: i for i, g in enumerate(GENRE_LIST)}

# MBTI 16종
MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP",
]
MBTI_TO_IDX = {m: i for i, m in enumerate(MBTI_TYPES)}

# Emotion 7종
EMOTION_KEYS = ["healing", "tension", "energy", "romance", "deep", "fantasy", "light"]


def _genre_multihot(genres: list[str]) -> torch.Tensor:
    """장르 리스트 → 19차원 멀티핫 벡터."""
    vec = torch.zeros(len(GENRE_LIST), dtype=torch.float32)
    for g in genres:
        idx = GENRE_TO_IDX.get(g)
        if idx is not None:
            vec[idx] = 1.0
    return vec


def _emotion_vec(tags: dict) -> torch.Tensor:
    """emotion_tags dict → 7차원 벡터."""
    return torch.tensor([tags.get(k, 0.0) for k in EMOTION_KEYS], dtype=torch.float32)


class RecoDataset(Dataset):
    """JSONL 기반 Two-Tower 학습 데이터셋.

    label > 0인 행만 positive pair로 사용합니다.

    Args:
        jsonl_path: 학습/검증 JSONL 파일 경로
        embedding_path: movie_embeddings.npy (42917, 1024)
        id_index_path: movie_id_index.json (array_idx → movie_id)
    """

    def __init__(
        self,
        jsonl_path: str | Path,
        embedding_path: str | Path | None = None,
        id_index_path: str | Path | None = None,
    ) -> None:
        self.records: list[dict] = []
        self.embeddings: np.ndarray | None = None
        self.movie_id_to_idx: dict[int, int] = {}

        # Voyage 임베딩 로드
        if embedding_path and Path(embedding_path).exists():
            self.embeddings = np.load(embedding_path)
            if id_index_path and Path(id_index_path).exists():
                with open(id_index_path, encoding="utf-8") as f:
                    raw = json.load(f)
                # raw: {"array_idx": movie_id} → 역매핑
                self.movie_id_to_idx = {int(v): int(k) for k, v in raw.items()}

        # JSONL 로드 (label > 0만)
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("label", 0) > 0:
                    self.records.append(rec)

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
        rec = self.records[idx]
        ctx = rec.get("context") or {}
        feat = rec.get("features") or {}

        # --- User features ---
        mbti = ctx.get("mbti", "INTJ")
        mbti_idx = torch.tensor(MBTI_TO_IDX.get(mbti, 0), dtype=torch.long)

        # user preferred_genres는 context에 없으므로 item 장르를 proxy로 사용
        # (synthetic 데이터는 user preferred_genres 정보가 JSONL에 미포함)
        user_genre_vec = _genre_multihot(feat.get("genres", []))

        history_emb = torch.zeros(128, dtype=torch.float32)

        user_features = {
            "mbti_idx": mbti_idx,
            "genre_vec": user_genre_vec,
            "history_emb": history_emb,
        }

        # --- Item features ---
        movie_id = rec["movie_id"]
        if self.embeddings is not None and movie_id in self.movie_id_to_idx:
            arr_idx = self.movie_id_to_idx[movie_id]
            voyage_emb = torch.from_numpy(self.embeddings[arr_idx].copy())
        else:
            voyage_emb = torch.zeros(1024, dtype=torch.float32)

        item_genre_vec = _genre_multihot(feat.get("genres", []))
        emotion_vec = _emotion_vec(feat.get("emotion_tags", {}))
        ws = feat.get("weighted_score", 0) or 0
        quality_score = torch.tensor([ws / 10.0], dtype=torch.float32)

        item_features = {
            "voyage_emb": voyage_emb,
            "genre_vec": item_genre_vec,
            "emotion_vec": emotion_vec,
            "quality_score": quality_score,
        }

        return user_features, item_features


def collate_fn(batch: list[tuple[dict, dict]]) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    """배치 내 dict-of-tensors를 스택합니다."""
    user_batch: dict[str, list[torch.Tensor]] = {}
    item_batch: dict[str, list[torch.Tensor]] = {}

    for user_feat, item_feat in batch:
        for k, v in user_feat.items():
            user_batch.setdefault(k, []).append(v)
        for k, v in item_feat.items():
            item_batch.setdefault(k, []).append(v)

    user_stacked = {k: torch.stack(vs) for k, vs in user_batch.items()}
    item_stacked = {k: torch.stack(vs) for k, vs in item_batch.items()}
    return user_stacked, item_stacked
