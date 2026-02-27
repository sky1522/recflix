# ruff: noqa: T201
"""
LightGBM 기반 CTR 예측 재랭커 학습.

JSONL 데이터에서 76dim 피처를 추출하여 이진 분류 모델을 학습합니다.
Two-Tower 후보 200개 → GBDT 재랭킹 50개 → 하이브리드 품질보정 20개.

Usage:
    python backend/scripts/train_reranker.py \
        --train-file data/synthetic/train.jsonl \
        --valid-file data/synthetic/valid.jsonl \
        --output-dir data/models/reranker/ \
        --num-rounds 500 --early-stopping 30 --verbose
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import lightgbm as lgb
import numpy as np

# ---------------------------------------------------------------------------
# Feature constants
# ---------------------------------------------------------------------------

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

FEATURE_NAMES = [
    *[f"mbti_{t}" for t in MBTI_TYPES],
    *[f"user_genre_{g}" for g in GENRE_LIST],
    *[f"item_genre_{g}" for g in GENRE_LIST],
    "weighted_score",
    *[f"emotion_{k}" for k in EMOTION_KEYS],
    *[f"weather_{w}" for w in WEATHER_TYPES],
    *[f"mood_{m}" for m in MOOD_TYPES],
    "mbti_score", "weather_score",
    "tt_score", "rank_reciprocal",
]

N_FEATURES = len(FEATURE_NAMES)  # 76


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(rec: dict) -> np.ndarray:
    """JSONL 레코드 1건 → 76dim float 벡터."""
    vec = np.zeros(N_FEATURES, dtype=np.float32)
    ctx = rec.get("context") or {}
    feat = rec.get("features") or {}
    offset = 0

    # mbti one-hot (16)
    mbti = ctx.get("mbti", "")
    idx = MBTI_TO_IDX.get(mbti)
    if idx is not None:
        vec[offset + idx] = 1.0
    offset += len(MBTI_TYPES)

    # user genres (19) — synthetic 데이터는 item 장르를 proxy로 사용
    for g in feat.get("genres", []):
        gidx = GENRE_TO_IDX.get(g)
        if gidx is not None:
            vec[offset + gidx] = 1.0
    offset += len(GENRE_LIST)

    # item genres (19)
    for g in feat.get("genres", []):
        gidx = GENRE_TO_IDX.get(g)
        if gidx is not None:
            vec[offset + gidx] = 1.0
    offset += len(GENRE_LIST)

    # weighted_score (1)
    vec[offset] = (feat.get("weighted_score") or 0) / 10.0
    offset += 1

    # emotion tags (7)
    etags = feat.get("emotion_tags") or {}
    for i, k in enumerate(EMOTION_KEYS):
        vec[offset + i] = etags.get(k, 0.0)
    offset += len(EMOTION_KEYS)

    # weather one-hot (4)
    widx = WEATHER_TO_IDX.get(ctx.get("weather", ""))
    if widx is not None:
        vec[offset + widx] = 1.0
    offset += len(WEATHER_TYPES)

    # mood one-hot (6)
    midx = MOOD_TO_IDX.get(ctx.get("mood", ""))
    if midx is not None:
        vec[offset + midx] = 1.0
    offset += len(MOOD_TYPES)

    # cross features
    vec[offset] = feat.get("mbti_score", 0.0)
    vec[offset + 1] = feat.get("weather_score", 0.0)
    offset += 2

    # candidate features
    vec[offset] = rec.get("score", 0.0)
    rank = rec.get("rank", 0)
    vec[offset + 1] = 1.0 / (rank + 1)
    offset += 2

    return vec


def load_dataset(jsonl_path: str, verbose: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """JSONL → (X, y) 배열."""
    features_list: list[np.ndarray] = []
    labels: list[int] = []

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            features_list.append(extract_features(rec))
            labels.append(1 if rec.get("label", 0) >= 1 else 0)

    x = np.array(features_list, dtype=np.float32)
    y = np.array(labels, dtype=np.int32)

    if verbose:
        pos = int(y.sum())
        print(f"  Loaded {len(y)} samples (pos={pos}, neg={len(y)-pos}, rate={pos/len(y)*100:.1f}%)")

    return x, y


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Train LightGBM Reranker")
    parser.add_argument("--train-file", required=True, help="Path to train.jsonl")
    parser.add_argument("--valid-file", required=True, help="Path to valid.jsonl")
    parser.add_argument("--output-dir", default="data/models/reranker/", help="Output directory")
    parser.add_argument("--num-rounds", type=int, default=500, help="Max boosting rounds")
    parser.add_argument("--early-stopping", type=int, default=30, help="Early stopping rounds")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Load data
    if args.verbose:
        print("[1/4] Loading training data...")
    x_train, y_train = load_dataset(args.train_file, verbose=args.verbose)

    if args.verbose:
        print("[2/4] Loading validation data...")
    x_valid, y_valid = load_dataset(args.valid_file, verbose=args.verbose)

    # LightGBM datasets
    train_data = lgb.Dataset(x_train, label=y_train, feature_name=FEATURE_NAMES)
    valid_data = lgb.Dataset(x_valid, label=y_valid, feature_name=FEATURE_NAMES, reference=train_data)

    params = {
        "objective": "binary",
        "metric": ["auc", "binary_logloss"],
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "seed": 42,
    }

    # Train
    if args.verbose:
        print(f"[3/4] Training LightGBM ({args.num_rounds} rounds, early_stop={args.early_stopping})...")

    eval_results: dict[str, dict[str, list[float]]] = {}
    t0 = time.time()

    model = lgb.train(
        params,
        train_data,
        num_boost_round=args.num_rounds,
        valid_sets=[train_data, valid_data],
        valid_names=["train", "valid"],
        callbacks=[
            lgb.early_stopping(stopping_rounds=args.early_stopping),
            lgb.log_evaluation(period=50 if args.verbose else 0),
            lgb.record_evaluation(eval_results),
        ],
    )

    train_time = time.time() - t0

    # Metrics
    best_iter = model.best_iteration
    valid_auc = eval_results["valid"]["auc"][best_iter - 1]
    valid_logloss = eval_results["valid"]["binary_logloss"][best_iter - 1]
    train_auc = eval_results["train"]["auc"][best_iter - 1]

    # Feature importance
    gain_imp = model.feature_importance(importance_type="gain")
    split_imp = model.feature_importance(importance_type="split")
    total_gain = gain_imp.sum()
    fi_gain = {
        FEATURE_NAMES[i]: round(float(gain_imp[i] / total_gain * 100), 2)
        for i in range(N_FEATURES) if gain_imp[i] > 0
    }
    fi_gain_sorted = dict(sorted(fi_gain.items(), key=lambda x: -x[1]))
    fi_split = {FEATURE_NAMES[i]: int(split_imp[i]) for i in range(N_FEATURES)}

    # Save artifacts
    if args.verbose:
        print("[4/4] Saving artifacts...")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = out_dir / "lgbm_v1.txt"
    model.save_model(str(model_path))

    with open(out_dir / "feature_importance.json", "w", encoding="utf-8") as f:
        json.dump({"gain_pct": fi_gain_sorted, "split": fi_split}, f, indent=2, ensure_ascii=False)

    with open(out_dir / "eval_metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "best_iteration": best_iter,
            "valid_auc": round(valid_auc, 4),
            "valid_logloss": round(valid_logloss, 4),
            "train_auc": round(train_auc, 4),
            "train_time_sec": round(train_time, 1),
            "eval_history": {
                "train_auc": [round(v, 4) for v in eval_results["train"]["auc"]],
                "valid_auc": [round(v, 4) for v in eval_results["valid"]["auc"]],
                "valid_logloss": [round(v, 4) for v in eval_results["valid"]["binary_logloss"]],
            },
        }, f, indent=2)

    with open(out_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump({
            "created_at": datetime.now(UTC).isoformat(),
            "params": params,
            "num_boost_round": args.num_rounds,
            "early_stopping": args.early_stopping,
            "best_iteration": best_iter,
            "n_features": N_FEATURES,
            "feature_names": FEATURE_NAMES,
            "train_samples": len(y_train),
            "valid_samples": len(y_valid),
        }, f, indent=2, ensure_ascii=False)

    # Report
    print("=" * 60)
    print("LightGBM Reranker Training Complete")
    print(f"  Best iteration: {best_iter}")
    print(f"  Valid AUC:      {valid_auc:.4f}")
    print(f"  Valid Logloss:  {valid_logloss:.4f}")
    print(f"  Train AUC:      {train_auc:.4f}")
    print(f"  Train time:     {train_time:.1f}s")
    print("\nFeature Importance (top 15 by gain):")
    for i, (name, pct) in enumerate(fi_gain_sorted.items()):
        if i >= 15:
            break
        print(f"  {name:25s} {pct:>6.1f}%")
    print(f"\nArtifacts saved to {out_dir}/")
    print(f"  lgbm_v1.txt            ({model_path.stat().st_size / 1024:.0f} KB)")
    print("  feature_importance.json")
    print("  eval_metrics.json")
    print("  config.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
