"""
Two-Tower 추천 모델.

User Tower와 Item Tower가 각각 독립적으로 임베딩을 생성하고,
내적(dot product)으로 매칭 점수를 계산합니다.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class UserTower(nn.Module):
    """사용자 특성 → 128차원 임베딩.

    입력:
    - mbti_idx: (B,) int, 0~15 → Embedding(16, 32)
    - genre_vec: (B, 19) float, 선호 장르 멀티핫 → Linear(19, 32)
    - history_emb: (B, 128) float, 최근 상호작용 아이템 임베딩 평균

    출력: (B, 128) L2-normalized 벡터
    """

    def __init__(self) -> None:
        super().__init__()
        self.mbti_emb = nn.Embedding(16, 32)
        self.genre_proj = nn.Linear(19, 32)
        self.fc1 = nn.Linear(192, 256)
        self.ln1 = nn.LayerNorm(256)
        self.fc2 = nn.Linear(256, 128)

    def forward(self, mbti_idx: torch.Tensor, genre_vec: torch.Tensor, history_emb: torch.Tensor) -> torch.Tensor:
        mbti_out = self.mbti_emb(mbti_idx)  # (B, 32)
        genre_out = self.genre_proj(genre_vec)  # (B, 32)
        x = torch.cat([mbti_out, genre_out, history_emb], dim=1)  # (B, 192)
        x = self.ln1(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return F.normalize(x, p=2, dim=1)


class ItemTower(nn.Module):
    """아이템 특성 → 128차원 임베딩.

    입력:
    - voyage_emb: (B, 1024) float → Linear(1024, 128)
    - genre_vec: (B, 19) float, 장르 멀티핫 → Linear(19, 32)
    - emotion_vec: (B, 7) float, 감성 태그 → Linear(7, 16)
    - quality_score: (B, 1) float → Linear(1, 8)

    출력: (B, 128) L2-normalized 벡터
    """

    def __init__(self) -> None:
        super().__init__()
        self.voyage_proj = nn.Linear(1024, 128)
        self.genre_proj = nn.Linear(19, 32)
        self.emotion_proj = nn.Linear(7, 16)
        self.quality_proj = nn.Linear(1, 8)
        self.fc1 = nn.Linear(184, 256)
        self.ln1 = nn.LayerNorm(256)
        self.fc2 = nn.Linear(256, 128)

    def forward(
        self,
        voyage_emb: torch.Tensor,
        genre_vec: torch.Tensor,
        emotion_vec: torch.Tensor,
        quality_score: torch.Tensor,
    ) -> torch.Tensor:
        v = self.voyage_proj(voyage_emb)  # (B, 128)
        g = self.genre_proj(genre_vec)  # (B, 32)
        e = self.emotion_proj(emotion_vec)  # (B, 16)
        q = self.quality_proj(quality_score)  # (B, 8)
        x = torch.cat([v, g, e, q], dim=1)  # (B, 184)
        x = self.ln1(F.relu(self.fc1(x)))
        x = self.fc2(x)
        return F.normalize(x, p=2, dim=1)


class TwoTowerModel(nn.Module):
    """User Tower + Item Tower 결합.

    학습 시: logits = user_vecs @ item_vecs.T / temperature
    서빙 시: Item Tower 출력을 사전계산 → ANN 인덱스
    """

    def __init__(self, temperature: float = 0.07) -> None:
        super().__init__()
        self.user_tower = UserTower()
        self.item_tower = ItemTower()
        self.temperature = temperature

    def forward(
        self,
        user_features: dict[str, torch.Tensor],
        item_features: dict[str, torch.Tensor],
    ) -> tuple[torch.Tensor, torch.Tensor]:
        user_vecs = self.user_tower(
            user_features["mbti_idx"],
            user_features["genre_vec"],
            user_features["history_emb"],
        )
        item_vecs = self.item_tower(
            item_features["voyage_emb"],
            item_features["genre_vec"],
            item_features["emotion_vec"],
            item_features["quality_score"],
        )
        return user_vecs, item_vecs

    def compute_loss(self, user_vecs: torch.Tensor, item_vecs: torch.Tensor) -> torch.Tensor:
        """In-Batch Negatives + Cross Entropy."""
        logits = user_vecs @ item_vecs.T / self.temperature  # (B, B)
        labels = torch.arange(len(user_vecs), device=user_vecs.device)
        return F.cross_entropy(logits, labels)
