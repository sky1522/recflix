# ruff: noqa: T201
"""
Two-Tower 모델 학습 스크립트.

Synthetic / 실제 데이터 JSONL로 학습하고,
모델 체크포인트 + Item 임베딩을 저장합니다.

Usage:
    python backend/scripts/train_two_tower.py \
        --train-file data/synthetic/train.jsonl \
        --valid-file data/synthetic/valid.jsonl \
        --embedding-file backend/data/embeddings/movie_embeddings.npy \
        --id-index-file backend/data/embeddings/movie_id_index.json \
        --epochs 30 --batch-size 256 --lr 1e-3 \
        --output-dir data/models/two_tower/ \
        --device cpu --verbose
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

# backend/ 를 sys.path에 추가하여 ml 모듈 import
_backend_dir = str(Path(__file__).resolve().parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from ml.dataset import GENRE_LIST, RecoDataset, collate_fn  # noqa: E402, I001
from ml.two_tower import TwoTowerModel  # noqa: E402, I001


# ---------------------------------------------------------------------------
# Item 임베딩 사전계산
# ---------------------------------------------------------------------------

def precompute_all_item_vecs(
    model: TwoTowerModel,
    embedding_path: str | None,
    id_index_path: str | None,
    db_url: str | None,
    device: torch.device,
    batch_size: int = 512,
    verbose: bool = False,
) -> tuple[torch.Tensor, list[int]]:
    """전체 아이템에 대해 Item Tower forward pass.

    Returns:
        all_item_vecs: (N, 128) 텐서
        movie_ids: 대응하는 movie_id 리스트
    """
    from ml.dataset import _emotion_vec, _genre_multihot

    # 영화 메타데이터 로드
    movie_metas = _load_movie_metadata(db_url, verbose)
    if not movie_metas:
        # DB 없으면 임베딩 파일 기준으로만 생성
        return _precompute_from_embeddings_only(model, embedding_path, id_index_path, device, batch_size, verbose)

    # Voyage 임베딩
    embeddings = None
    movie_id_to_idx: dict[int, int] = {}
    if embedding_path and Path(embedding_path).exists():
        embeddings = np.load(embedding_path)
        if id_index_path and Path(id_index_path).exists():
            with open(id_index_path, encoding="utf-8") as f:
                raw = json.load(f)
            movie_id_to_idx = {int(v): int(k) for k, v in raw.items()}

    movie_ids: list[int] = []
    all_voyage: list[torch.Tensor] = []
    all_genre: list[torch.Tensor] = []
    all_emotion: list[torch.Tensor] = []
    all_quality: list[torch.Tensor] = []

    for m in movie_metas:
        mid = m["id"]
        movie_ids.append(mid)

        if embeddings is not None and mid in movie_id_to_idx:
            v = torch.from_numpy(embeddings[movie_id_to_idx[mid]].copy())
        else:
            v = torch.zeros(1024, dtype=torch.float32)
        all_voyage.append(v)
        all_genre.append(_genre_multihot(m.get("genres", [])))
        all_emotion.append(_emotion_vec(m.get("emotion_tags", {})))
        ws = (m.get("weighted_score") or 0) / 10.0
        all_quality.append(torch.tensor([ws], dtype=torch.float32))

    n = len(movie_ids)
    if verbose:
        print(f"  Precomputing item embeddings for {n} movies...")

    model.eval()
    all_vecs: list[torch.Tensor] = []

    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        item_feats = {
            "voyage_emb": torch.stack(all_voyage[start:end]).to(device),
            "genre_vec": torch.stack(all_genre[start:end]).to(device),
            "emotion_vec": torch.stack(all_emotion[start:end]).to(device),
            "quality_score": torch.stack(all_quality[start:end]).to(device),
        }
        with torch.no_grad():
            vecs = model.item_tower(
                item_feats["voyage_emb"],
                item_feats["genre_vec"],
                item_feats["emotion_vec"],
                item_feats["quality_score"],
            )
        all_vecs.append(vecs.cpu())

    return torch.cat(all_vecs, dim=0), movie_ids


def _load_movie_metadata(db_url: str | None, verbose: bool = False) -> list[dict]:
    """DB에서 전체 영화 메타데이터 로드."""
    if not db_url:
        return []

    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        if verbose:
            print("  WARNING: sqlalchemy not available, skipping DB metadata load")
        return []

    engine = create_engine(db_url)
    query = text("""
        SELECT m.id, m.weighted_score, m.emotion_tags,
               COALESCE(
                   (SELECT array_agg(g.name)
                    FROM movie_genres mg
                    JOIN genres g ON g.id = mg.genre_id
                    WHERE mg.movie_id = m.id),
                   '{}'
               ) AS genres
        FROM movies m
        WHERE m.weighted_score > 0
        ORDER BY m.id
    """)

    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()

    movies = []
    for r in rows:
        genres_raw = r["genres"]
        if isinstance(genres_raw, str):
            genres_raw = [g.strip() for g in genres_raw.strip("{}").split(",") if g.strip()]
        movies.append({
            "id": r["id"],
            "weighted_score": r["weighted_score"] or 0,
            "emotion_tags": r["emotion_tags"] or {},
            "genres": list(genres_raw) if genres_raw else [],
        })

    if verbose:
        print(f"  Loaded {len(movies)} movies from DB")
    return movies


def _precompute_from_embeddings_only(
    model: TwoTowerModel,
    embedding_path: str | None,
    id_index_path: str | None,
    device: torch.device,
    batch_size: int,
    verbose: bool,
) -> tuple[torch.Tensor, list[int]]:
    """DB 없이 임베딩 파일만으로 Item Tower 사전계산 (zero 피처)."""
    if not embedding_path or not Path(embedding_path).exists():
        if verbose:
            print("  WARNING: No embeddings file and no DB. Returning empty.")
        return torch.zeros(0, 128), []

    embeddings = np.load(embedding_path)
    movie_ids: list[int] = []
    if id_index_path and Path(id_index_path).exists():
        with open(id_index_path, encoding="utf-8") as f:
            raw = json.load(f)
        # array_idx → movie_id
        for arr_idx in range(len(embeddings)):
            mid = raw.get(str(arr_idx))
            if mid is not None:
                movie_ids.append(int(mid))
            else:
                movie_ids.append(arr_idx)
    else:
        movie_ids = list(range(len(embeddings)))

    n = len(embeddings)
    if verbose:
        print(f"  Precomputing item embeddings for {n} items (no DB metadata)...")

    model.eval()
    all_vecs: list[torch.Tensor] = []

    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        chunk = torch.from_numpy(embeddings[start:end].copy()).to(device)
        item_feats = {
            "voyage_emb": chunk,
            "genre_vec": torch.zeros(end - start, 19, device=device),
            "emotion_vec": torch.zeros(end - start, 7, device=device),
            "quality_score": torch.zeros(end - start, 1, device=device),
        }
        with torch.no_grad():
            vecs = model.item_tower(
                item_feats["voyage_emb"],
                item_feats["genre_vec"],
                item_feats["emotion_vec"],
                item_feats["quality_score"],
            )
        all_vecs.append(vecs.cpu())

    return torch.cat(all_vecs, dim=0), movie_ids


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_recall(
    model: TwoTowerModel,
    valid_loader: DataLoader,
    all_item_vecs: torch.Tensor,
    movie_ids: list[int],
    device: torch.device,
    k: int = 200,
) -> float:
    """Recall@K: positive item이 Top-K에 포함되는 비율."""
    all_item_vecs_dev = all_item_vecs.to(device)

    hits = 0
    total = 0

    model.eval()
    with torch.no_grad():
        for user_feats, item_feats in valid_loader:
            user_feats = {k: v.to(device) for k, v in user_feats.items()}
            item_feats = {k: v.to(device) for k, v in item_feats.items()}

            user_vecs = model.user_tower(
                user_feats["mbti_idx"],
                user_feats["genre_vec"],
                user_feats["history_emb"],
            )  # (B, 128)

            # positive item의 Item Tower 출력
            pos_item_vecs = model.item_tower(
                item_feats["voyage_emb"],
                item_feats["genre_vec"],
                item_feats["emotion_vec"],
                item_feats["quality_score"],
            )  # (B, 128)

            # 전체 아이템과 유사도 계산
            scores = user_vecs @ all_item_vecs_dev.T  # (B, N)
            _, top_k_indices = scores.topk(min(k, scores.size(1)), dim=1)  # (B, k)

            # positive item과 가장 가까운 사전계산 벡터 찾기
            # (pos_item_vecs와 all_item_vecs 간 코사인 유사도로 매칭)
            pos_scores = pos_item_vecs @ all_item_vecs_dev.T  # (B, N)
            pos_best_idx = pos_scores.argmax(dim=1)  # (B,)

            for i in range(len(user_vecs)):
                if pos_best_idx[i].item() in top_k_indices[i].tolist():
                    hits += 1
                total += 1

    return hits / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def train(args: argparse.Namespace) -> None:
    """메인 학습 루프."""
    device = torch.device(args.device)

    # 데이터셋 로드
    if args.verbose:
        print("[1/6] Loading datasets...")

    emb_path = args.embedding_file if args.embedding_file and Path(args.embedding_file).exists() else None
    idx_path = args.id_index_file if args.id_index_file and Path(args.id_index_file).exists() else None

    if emb_path is None:
        print("WARNING: Voyage embeddings not found. Using zero embeddings.")

    train_ds = RecoDataset(args.train_file, emb_path, idx_path)
    valid_ds = RecoDataset(args.valid_file, emb_path, idx_path)

    if args.verbose:
        print(f"  Train: {len(train_ds)} positive pairs")
        print(f"  Valid: {len(valid_ds)} positive pairs")

    if len(train_ds) == 0:
        print("ERROR: No positive samples in training data.", file=sys.stderr)
        sys.exit(1)

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        collate_fn=collate_fn, num_workers=0, drop_last=True,
    )
    valid_loader = DataLoader(
        valid_ds, batch_size=args.batch_size, shuffle=False,
        collate_fn=collate_fn, num_workers=0,
    )

    # 모델 초기화
    if args.verbose:
        print("[2/6] Initializing model...")
    model = TwoTowerModel(temperature=args.temperature).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    if args.verbose:
        print(f"  Parameters: {n_params:,}")

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=2, min_lr=1e-6,
    )

    # Item 임베딩 사전계산 (Recall@K 평가용)
    if args.verbose:
        print("[3/6] Precomputing item embeddings...")
    all_item_vecs, movie_ids = precompute_all_item_vecs(
        model, emb_path, idx_path,
        db_url=args.db_url, device=device, verbose=args.verbose,
    )

    if len(movie_ids) == 0:
        print("WARNING: No item embeddings for recall evaluation. Skipping recall.")

    # 학습 시작
    if args.verbose:
        print(f"[4/6] Training for {args.epochs} epochs...")

    best_recall = -1.0
    patience_counter = 0
    training_log: list[dict] = []

    for epoch in range(args.epochs):
        epoch_start = time.time()

        # --- Train ---
        model.train()
        epoch_loss = 0.0
        n_batches = 0

        for user_feats, item_feats in train_loader:
            user_feats = {k: v.to(device) for k, v in user_feats.items()}
            item_feats = {k: v.to(device) for k, v in item_feats.items()}

            user_vecs, item_vecs = model(user_feats, item_feats)
            loss = model.compute_loss(user_vecs, item_vecs)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        avg_loss = epoch_loss / max(n_batches, 1)

        # --- Validation ---
        recall_200 = 0.0
        if len(movie_ids) > 0:
            # 아이템 임베딩 갱신 (학습 후 변경된 가중치 반영)
            if (epoch + 1) % 5 == 0 or epoch == 0:
                all_item_vecs, movie_ids = precompute_all_item_vecs(
                    model, emb_path, idx_path,
                    db_url=args.db_url, device=device,
                )
            recall_200 = evaluate_recall(
                model, valid_loader, all_item_vecs, movie_ids, device, k=200,
            )

        scheduler.step(recall_200)
        elapsed = time.time() - epoch_start

        log_entry = {
            "epoch": epoch,
            "train_loss": round(avg_loss, 6),
            "recall_200": round(recall_200, 4),
            "lr": optimizer.param_groups[0]["lr"],
            "elapsed_sec": round(elapsed, 1),
        }
        training_log.append(log_entry)

        if args.verbose or (epoch + 1) % 5 == 0 or epoch == 0:
            print(
                f"  Epoch {epoch:>3d}: loss={avg_loss:.4f}  "
                f"recall@200={recall_200:.4f}  "
                f"lr={optimizer.param_groups[0]['lr']:.2e}  "
                f"({elapsed:.1f}s)"
            )

        # Early stopping
        if recall_200 > best_recall:
            best_recall = recall_200
            patience_counter = 0
            # Best 모델 저장
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"  Early stopping at epoch {epoch} (patience={args.patience})")
                break

    # Best 모델 복원
    if best_state:  # noqa: F821 — always assigned (epoch 0)
        model.load_state_dict(best_state)

    # 저장
    if args.verbose:
        print("[5/6] Saving artifacts...")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 모델 state_dict
    model_path = out_dir / "model_v1.pt"
    torch.save(model.state_dict(), model_path)

    # 최종 Item 임베딩 사전계산
    if args.verbose:
        print("[6/6] Final item embedding computation...")
    final_item_vecs, final_movie_ids = precompute_all_item_vecs(
        model, emb_path, idx_path,
        db_url=args.db_url, device=device, verbose=args.verbose,
    )
    item_emb_path = out_dir / "item_embeddings_tt.npy"
    np.save(item_emb_path, final_item_vecs.numpy())

    # movie_id 매핑 저장
    with open(out_dir / "movie_id_map.json", "w", encoding="utf-8") as f:
        json.dump(final_movie_ids, f)

    # 학습 로그
    with open(out_dir / "training_log.json", "w", encoding="utf-8") as f:
        json.dump(training_log, f, indent=2, ensure_ascii=False)

    # 설정
    config = {
        "created_at": datetime.now(UTC).isoformat(),
        "train_file": str(args.train_file),
        "valid_file": str(args.valid_file),
        "embedding_file": str(args.embedding_file or "none"),
        "epochs_trained": len(training_log),
        "batch_size": args.batch_size,
        "lr": args.lr,
        "temperature": args.temperature,
        "patience": args.patience,
        "n_params": n_params,
        "best_recall_200": round(best_recall, 4),
        "final_loss": training_log[-1]["train_loss"],
        "item_embedding_shape": list(final_item_vecs.shape),
        "n_movies": len(final_movie_ids),
        "genre_list": GENRE_LIST,
    }
    with open(out_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # 결과 출력
    print("=" * 60)
    print("Training Complete")
    print(f"  Epochs: {len(training_log)}")
    print(f"  Final loss: {training_log[-1]['train_loss']:.4f}")
    print(f"  Best Recall@200: {best_recall:.4f}")
    print(f"  Parameters: {n_params:,}")
    print(f"  Item embeddings: {final_item_vecs.shape}")
    print(f"\nArtifacts saved to {out_dir}/")
    print(f"  model_v1.pt         ({model_path.stat().st_size / 1024:.0f} KB)")
    print(f"  item_embeddings_tt.npy ({item_emb_path.stat().st_size / 1024 / 1024:.1f} MB)")
    print("  training_log.json")
    print("  config.json")
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Train Two-Tower Recommendation Model")
    parser.add_argument("--train-file", required=True, help="Path to train.jsonl")
    parser.add_argument("--valid-file", required=True, help="Path to valid.jsonl")
    parser.add_argument("--embedding-file", default=None, help="Path to movie_embeddings.npy")
    parser.add_argument("--id-index-file", default=None, help="Path to movie_id_index.json")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="DB URL for full item precomputation")
    parser.add_argument("--epochs", type=int, default=30, help="Max epochs")
    parser.add_argument("--batch-size", type=int, default=256, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--temperature", type=float, default=0.07, help="InfoNCE temperature")
    parser.add_argument("--patience", type=int, default=5, help="Early stopping patience")
    parser.add_argument("--output-dir", default="data/models/two_tower/", help="Output directory")
    parser.add_argument("--device", default="cpu", help="Device (cpu/cuda)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    if not Path(args.train_file).exists():
        print(f"ERROR: Train file not found: {args.train_file}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.valid_file).exists():
        print(f"ERROR: Valid file not found: {args.valid_file}", file=sys.stderr)
        sys.exit(1)

    train(args)


if __name__ == "__main__":
    main()
