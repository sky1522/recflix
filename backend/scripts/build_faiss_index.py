# ruff: noqa: T201
"""
FAISS 인덱스 빌드 스크립트.

Two-Tower Item 임베딩으로 Inner Product 기반 ANN 인덱스를 생성합니다.

Usage:
    python backend/scripts/build_faiss_index.py \
        --embeddings data/models/two_tower/item_embeddings_tt.npy \
        --movie-id-map data/models/two_tower/movie_id_map.json \
        --output data/models/two_tower/faiss_index.bin \
        --index-type flat --verbose
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import faiss
import numpy as np


def build_index(
    embeddings: np.ndarray,
    index_type: str = "flat",
    nlist: int = 256,
    nprobe: int = 16,
) -> faiss.Index:
    """FAISS 인덱스 생성."""
    dim = embeddings.shape[1]

    if index_type == "ivfflat":
        quantizer = faiss.IndexFlatIP(dim)
        index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
        index.train(embeddings)
        index.nprobe = nprobe
    else:
        index = faiss.IndexFlatIP(dim)

    index.add(embeddings)
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS index from Two-Tower item embeddings")
    parser.add_argument("--embeddings", required=True, help="Path to item_embeddings_tt.npy")
    parser.add_argument("--movie-id-map", required=True, help="Path to movie_id_map.json")
    parser.add_argument("--output", default="data/models/two_tower/faiss_index.bin", help="Output index path")
    parser.add_argument("--index-type", choices=["flat", "ivfflat"], default="flat", help="Index type")
    parser.add_argument("--nlist", type=int, default=256, help="IVF nlist (only for ivfflat)")
    parser.add_argument("--nprobe", type=int, default=16, help="IVF nprobe (only for ivfflat)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Load embeddings
    emb_path = Path(args.embeddings)
    if not emb_path.exists():
        print(f"ERROR: Embeddings file not found: {emb_path}")
        raise SystemExit(1)

    embeddings = np.load(emb_path).astype(np.float32)
    if args.verbose:
        print(f"Loaded embeddings: {embeddings.shape} ({embeddings.dtype})")

    # Verify movie_id_map
    map_path = Path(args.movie_id_map)
    if not map_path.exists():
        print(f"ERROR: Movie ID map not found: {map_path}")
        raise SystemExit(1)

    with open(map_path, encoding="utf-8") as f:
        movie_id_map = json.load(f)
    if len(movie_id_map) != embeddings.shape[0]:
        print(f"WARNING: movie_id_map ({len(movie_id_map)}) != embeddings ({embeddings.shape[0]})")

    # Build index
    if args.verbose:
        print(f"Building {args.index_type} index (dim={embeddings.shape[1]})...")

    t0 = time.time()
    index = build_index(embeddings, args.index_type, args.nlist, args.nprobe)
    build_time = time.time() - t0

    # Save
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(out_path))

    # Search benchmark
    if args.verbose:
        print("Running search benchmark (100 queries, top-200)...")
    rng = np.random.default_rng(42)
    query_vecs = rng.standard_normal((100, embeddings.shape[1])).astype(np.float32)
    # L2 normalize queries (matching model output)
    norms = np.linalg.norm(query_vecs, axis=1, keepdims=True)
    query_vecs = query_vecs / np.maximum(norms, 1e-8)

    t0 = time.time()
    _scores, _indices = index.search(query_vecs, 200)
    search_time = (time.time() - t0) / 100 * 1000  # ms per query

    # Report
    print("=" * 60)
    print("FAISS Index Build Complete")
    print(f"  Type: {args.index_type}")
    print(f"  Vectors: {index.ntotal:,}")
    print(f"  Dimension: {embeddings.shape[1]}")
    print(f"  Build time: {build_time:.2f}s")
    print(f"  File size: {out_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"  Search latency: {search_time:.2f} ms/query (top-200)")
    print(f"  Output: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
