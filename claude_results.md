# Step 03: Two-Tower 추천 모델 구현 및 학습

> 작업일: 2026-02-27
> 목적: User-Item 임베딩 학습을 위한 Two-Tower 모델 + 학습 파이프라인 구축

## 생성 파일

| 파일 | 설명 |
|------|------|
| `backend/ml/__init__.py` | ML 모듈 패키지 |
| `backend/ml/two_tower.py` | Two-Tower 모델 (UserTower + ItemTower + TwoTowerModel) |
| `backend/ml/dataset.py` | RecoDataset + collate_fn (JSONL → PyTorch 텐서) |
| `backend/scripts/train_two_tower.py` | 학습 CLI 스크립트 |

## 아티팩트 (data/models/two_tower/)

| 파일 | 크기 | 설명 |
|------|------|------|
| `model_v1.pt` | 1.1 MB | 모델 state_dict |
| `item_embeddings_tt.npy` | 21.0 MB | Item Tower 출력 (42917, 128) |
| `training_log.json` | 1 KB | 에포크별 loss, recall |
| `config.json` | 1 KB | 하이퍼파라미터 |
| `movie_id_map.json` | 319 KB | movie_id 리스트 |

## 모델 아키텍처

```
TwoTowerModel (296,720 params, temperature=0.07)
├── UserTower
│   ├── mbti_emb: Embedding(16, 32)
│   ├── genre_proj: Linear(19, 32)
│   ├── fc1: Linear(192, 256) + ReLU + LayerNorm
│   └── fc2: Linear(256, 128) + L2 Normalize
└── ItemTower
    ├── voyage_proj: Linear(1024, 128)
    ├── genre_proj: Linear(19, 32)
    ├── emotion_proj: Linear(7, 16)
    ├── quality_proj: Linear(1, 8)
    ├── fc1: Linear(184, 256) + ReLU + LayerNorm
    └── fc2: Linear(256, 128) + L2 Normalize

Loss: In-Batch Negatives + Cross Entropy
```

## CLI 사용 예시

```bash
python backend/scripts/train_two_tower.py \
  --train-file data/synthetic/train.jsonl \
  --valid-file data/synthetic/valid.jsonl \
  --embedding-file backend/data/embeddings/movie_embeddings.npy \
  --id-index-file backend/data/embeddings/movie_id_index.json \
  --db-url "$DATABASE_URL" \
  --epochs 30 --batch-size 256 --lr 1e-3 \
  --output-dir data/models/two_tower/ \
  --device cpu --verbose
```

## 학습 결과

```
Epoch   0: loss=2.7893  recall@200=0.7452
Epoch   1: loss=1.2154  recall@200=0.8245
Epoch   2: loss=1.1035  recall@200=0.8473
Epoch   3: loss=1.0456  recall@200=0.8683  ← best
Epoch   4: loss=1.0158  recall@200=0.8001
...
Epoch   8: loss=0.8616  recall@200=0.8031
Early stopping at epoch 8 (patience=5)

Final: loss=0.8616, Best Recall@200=0.8683
```

## 검증 결과

| 항목 | 결과 |
|------|------|
| Loss 감소 추세 (2.789 → 0.862) | OK |
| Recall@200 > 0.3 (0.8683) | OK |
| item_embeddings_tt.npy shape (42917, 128) | OK |
| model_v1.pt 로드 + forward pass | OK |
| training_log.json 에포크별 기록 (9 entries) | OK |
| 임베딩 파일 없이 학습 가능 (zero fallback) | OK |
| Ruff 린트 (3 files) | OK |
| pytest (10 passed, 4 skipped) | OK |
