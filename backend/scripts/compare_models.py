# ruff: noqa: T201
"""
다중 모델 오프라인 비교 리포트.

Popularity / MBTI-only / Hybrid v1 / Two-Tower+LGBM 4개 모델을
NDCG, Recall, MRR, HitRate, Coverage, Novelty + Bootstrap CI로 비교합니다.

Usage:
    python backend/scripts/compare_models.py \
        --test-file data/synthetic/test.jsonl \
        --output-dir data/offline/reports/ \
        --k-values 5 10 20 \
        --n-bootstrap 1000 \
        --verbose
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# 피처 상수 (train_reranker.py와 동기화)
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

N_FEATURES = 76


# ---------------------------------------------------------------------------
# Metric functions (offline_eval.py에서 재사용)
# ---------------------------------------------------------------------------

def ndcg_at_k(ranked: list[int], relevance: dict[int, float], k: int) -> float:
    dcg = sum(relevance.get(mid, 0) / math.log2(i + 2) for i, mid in enumerate(ranked[:k]))
    ideal = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(ranked: list[int], relevant: set[int], k: int) -> float:
    if not relevant:
        return 0.0
    return len(set(ranked[:k]) & relevant) / min(len(relevant), k)


def mrr_at_k(ranked: list[int], relevant: set[int], k: int) -> float:
    for i, mid in enumerate(ranked[:k]):
        if mid in relevant:
            return 1.0 / (i + 1)
    return 0.0


def hit_rate_at_k(ranked: list[int], relevant: set[int], k: int) -> float:
    return 1.0 if set(ranked[:k]) & relevant else 0.0


def genre_coverage(ranked: list[int], genres_map: dict[int, list[str]], k: int) -> float:
    genres: set[str] = set()
    for mid in ranked[:k]:
        genres.update(genres_map.get(mid, []))
    return len(genres) / 19


def novelty_score(ranked: list[int], pop: dict[int, float], k: int) -> float:
    scores = [-math.log2(max(pop.get(mid, 1e-6), 1e-6)) for mid in ranked[:k]]
    return sum(scores) / len(scores) if scores else 0.0


def bootstrap_ci(values: list[float], n_boot: int = 1000) -> tuple[float, float, float]:
    arr = np.array(values)
    if len(arr) <= 1:
        m = float(np.mean(arr)) if len(arr) == 1 else 0.0
        return m, m, m
    rng = np.random.default_rng(42)
    means = sorted(
        float(np.mean(rng.choice(arr, size=len(arr), replace=True)))
        for _ in range(n_boot)
    )
    lo = means[int(0.025 * n_boot)]
    hi = means[min(int(0.975 * n_boot), len(means) - 1)]
    return float(np.mean(arr)), lo, hi


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def group_by_request(records: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        groups[rec["request_id"]].append(rec)
    return dict(groups)


def build_maps(records: list[dict]) -> tuple[dict[int, list[str]], dict[int, float]]:
    genres_map: dict[int, list[str]] = {}
    pop_map: dict[int, float] = {}
    for rec in records:
        mid = rec["movie_id"]
        feat = rec.get("features") or {}
        if mid not in genres_map:
            genres_map[mid] = feat.get("genres", [])
        if mid not in pop_map:
            ws = feat.get("weighted_score")
            if ws is not None:
                pop_map[mid] = max(ws / 10.0, 1e-6)
    return genres_map, pop_map


# ---------------------------------------------------------------------------
# Ranking strategies
# ---------------------------------------------------------------------------

def rank_by_popularity(items: list[dict]) -> list[int]:
    return [it["movie_id"] for it in sorted(items, key=lambda x: (x.get("features", {}).get("weighted_score") or 0), reverse=True)]


def rank_by_mbti(items: list[dict]) -> list[int]:
    ctx = items[0].get("context") or {} if items else {}
    if not ctx.get("mbti"):
        return rank_by_popularity(items)
    return [it["movie_id"] for it in sorted(items, key=lambda x: (x.get("features", {}).get("mbti_score") or 0), reverse=True)]


def rank_by_score(items: list[dict]) -> list[int]:
    return [it["movie_id"] for it in sorted(items, key=lambda x: (x.get("score") or 0), reverse=True)]


def rank_by_tt_only(items: list[dict]) -> list[int]:
    """Two-Tower only: score(= tt_score) 내림차순."""
    return rank_by_score(items)


# ---------------------------------------------------------------------------
# LGBM feature extraction (train_reranker.py와 동기)
# ---------------------------------------------------------------------------

def extract_features(rec: dict) -> np.ndarray:
    vec = np.zeros(N_FEATURES, dtype=np.float32)
    ctx = rec.get("context") or {}
    feat = rec.get("features") or {}
    offset = 0

    idx = MBTI_TO_IDX.get(ctx.get("mbti", ""))
    if idx is not None:
        vec[offset + idx] = 1.0
    offset += len(MBTI_TYPES)

    for g in feat.get("genres", []):
        gidx = GENRE_TO_IDX.get(g)
        if gidx is not None:
            vec[offset + gidx] = 1.0
    offset += len(GENRE_LIST)

    for g in feat.get("genres", []):
        gidx = GENRE_TO_IDX.get(g)
        if gidx is not None:
            vec[offset + gidx] = 1.0
    offset += len(GENRE_LIST)

    vec[offset] = (feat.get("weighted_score") or 0) / 10.0
    offset += 1

    etags = feat.get("emotion_tags") or {}
    for i, k in enumerate(EMOTION_KEYS):
        vec[offset + i] = etags.get(k, 0.0)
    offset += len(EMOTION_KEYS)

    widx = WEATHER_TO_IDX.get(ctx.get("weather", ""))
    if widx is not None:
        vec[offset + widx] = 1.0
    offset += len(WEATHER_TYPES)

    midx = MOOD_TO_IDX.get(ctx.get("mood", ""))
    if midx is not None:
        vec[offset + midx] = 1.0
    offset += len(MOOD_TYPES)

    vec[offset] = feat.get("mbti_score", 0.0)
    vec[offset + 1] = feat.get("weather_score", 0.0)
    offset += 2

    vec[offset] = rec.get("score", 0.0)
    rank = rec.get("rank", 0)
    vec[offset + 1] = 1.0 / (rank + 1)

    return vec


def rank_by_lgbm(items: list[dict], lgbm_model) -> list[int]:
    """LGBM predict → 재랭킹."""
    x = np.array([extract_features(it) for it in items], dtype=np.float32)
    scores = lgbm_model.predict(x)
    indexed = list(zip(items, scores, strict=True))
    indexed.sort(key=lambda t: t[1], reverse=True)
    return [it["movie_id"] for it, _ in indexed]


# ---------------------------------------------------------------------------
# Evaluate one model
# ---------------------------------------------------------------------------

METRIC_NAMES = ["ndcg", "recall", "mrr", "hit_rate", "coverage", "novelty"]


def evaluate_model(
    groups: dict[str, list[dict]],
    rank_fn,
    k_values: list[int],
    genres_map: dict[int, list[str]],
    pop_map: dict[int, float],
    n_boot: int,
) -> dict:
    per_req: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for _rid, items in groups.items():
        ranked = rank_fn(items)
        relevance = {it["movie_id"]: it["label"] for it in items}
        relevant = {mid for mid, lbl in relevance.items() if lbl > 0}

        for k in k_values:
            per_req["ndcg"][f"@{k}"].append(ndcg_at_k(ranked, relevance, k))
            per_req["recall"][f"@{k}"].append(recall_at_k(ranked, relevant, k))
            per_req["mrr"][f"@{k}"].append(mrr_at_k(ranked, relevant, k))
            per_req["hit_rate"][f"@{k}"].append(hit_rate_at_k(ranked, relevant, k))
            per_req["coverage"][f"@{k}"].append(genre_coverage(ranked, genres_map, k))
            per_req["novelty"][f"@{k}"].append(novelty_score(ranked, pop_map, k))

    metrics: dict[str, dict[str, float]] = {}
    ci_95: dict[str, dict[str, float]] = {}

    for mname, k_dict in per_req.items():
        metrics[mname] = {}
        for k_label, vals in k_dict.items():
            mean, lo, hi = bootstrap_ci(vals, n_boot)
            metrics[mname][k_label] = round(mean, 4)
            if k_label == "@10":
                ci_95[f"{mname}@10"] = {"mean": round(mean, 4), "lower": round(lo, 4), "upper": round(hi, 4)}

    return {"metrics": metrics, "ci_95": ci_95}


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_markdown(
    models: dict[str, dict],
    k_values: list[int],
    dataset_info: str,
    ablation: list[tuple[str, str, str]],
) -> str:
    lines = [
        "# RecFlix Model Comparison Report",
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Dataset: {dataset_info}",
        "",
        "## Overall Metrics",
        "",
    ]

    # Main table
    k_cols = [f"NDCG@{k}" for k in k_values] + [f"Recall@{k}" for k in k_values] + ["MRR@10", "HitRate@10"]
    header = "| Model | " + " | ".join(k_cols) + " |"
    sep = "|" + "|".join(["---"] * (len(k_cols) + 1)) + "|"
    lines.append(header)
    lines.append(sep)

    for name, res in models.items():
        m = res["metrics"]
        vals = []
        for k in k_values:
            vals.append(f"{m['ndcg'].get(f'@{k}', 0):.4f}")
        for k in k_values:
            vals.append(f"{m['recall'].get(f'@{k}', 0):.4f}")
        vals.append(f"{m['mrr'].get('@10', 0):.4f}")
        vals.append(f"{m['hit_rate'].get('@10', 0):.4f}")
        lines.append(f"| {name} | " + " | ".join(vals) + " |")

    # Improvement vs baselines
    lines.extend(["", "## Improvement vs Baseline (NDCG@10)", ""])
    pop_val = models.get("Popularity", {}).get("metrics", {}).get("ndcg", {}).get("@10", 0)
    hybrid_val = models.get("Hybrid v1", {}).get("metrics", {}).get("ndcg", {}).get("@10", 0)

    lines.append("| Model | NDCG@10 | vs Popularity | vs Hybrid |")
    lines.append("|---|---|---|---|")
    for name, res in models.items():
        v = res["metrics"]["ndcg"].get("@10", 0)
        d_pop = f"{(v - pop_val) / pop_val * 100:+.1f}%" if pop_val and name != "Popularity" else "-"
        d_hyb = f"{(v - hybrid_val) / hybrid_val * 100:+.1f}%" if hybrid_val and name != "Hybrid v1" else "-"
        lines.append(f"| {name} | {v:.4f} | {d_pop} | {d_hyb} |")

    # Ablation
    lines.extend(["", "## Ablation Study", ""])
    lines.append("| Stage | NDCG@10 | vs Previous |")
    lines.append("|---|---|---|")
    for stage, val_str, delta_str in ablation:
        lines.append(f"| {stage} | {val_str} | {delta_str} |")

    # Diversity
    lines.extend(["", "## Diversity Metrics", ""])
    lines.append("| Model | Coverage@10 | Novelty@10 |")
    lines.append("|---|---|---|")
    for name, res in models.items():
        m = res["metrics"]
        lines.append(f"| {name} | {m['coverage'].get('@10', 0):.4f} | {m['novelty'].get('@10', 0):.2f} |")

    # Bootstrap CI
    lines.extend(["", "## Bootstrap 95% CI (NDCG@10)", ""])
    lines.append("| Model | Mean | Lower | Upper |")
    lines.append("|---|---|---|---|")
    for name, res in models.items():
        ci = res["ci_95"].get("ndcg@10", {})
        lines.append(f"| {name} | {ci.get('mean', 0):.4f} | {ci.get('lower', 0):.4f} | {ci.get('upper', 0):.4f} |")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Model Comparison Report")
    parser.add_argument("--test-file", required=True)
    parser.add_argument("--output-dir", default="data/offline/reports/")
    parser.add_argument("--k-values", nargs="+", type=int, default=[5, 10, 20])
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--lgbm-model", default="data/models/reranker/lgbm_v1.txt")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    test_path = Path(args.test_file)
    if not test_path.exists():
        print(f"ERROR: {test_path} not found", file=sys.stderr)
        sys.exit(1)

    records = load_jsonl(test_path)
    if not records:
        print("No data.")
        sys.exit(0)

    groups = group_by_request(records)
    users = {r.get("user_id") for r in records}
    n_pos = sum(1 for r in records if r["label"] > 0)
    dataset_info = f"{test_path} ({len(records)} samples, {len(users)} users, {len(groups)} requests)"

    if args.verbose:
        print(f"Loaded: {dataset_info}")
        print(f"Positive: {n_pos}")

    genres_map, pop_map = build_maps(records)

    # -- LGBM 모델 로드 --
    lgbm_model = None
    lgbm_path = Path(args.lgbm_model)
    if lgbm_path.exists():
        try:
            import lightgbm as lgb
            lgbm_model = lgb.Booster(model_file=str(lgbm_path))
            if args.verbose:
                print(f"LGBM model loaded: {lgbm_path}")
        except Exception as e:
            print(f"LGBM load failed: {e}, skipping TwoTower+LGBM")
    else:
        print(f"LGBM model not found at {lgbm_path}, skipping TwoTower+LGBM")

    # -- Evaluate models --
    models: dict[str, dict] = {}
    model_order = ["Popularity", "MBTI-only", "Hybrid v1", "TwoTower only"]
    rank_fns = {
        "Popularity": rank_by_popularity,
        "MBTI-only": rank_by_mbti,
        "Hybrid v1": rank_by_score,
        "TwoTower only": rank_by_tt_only,
    }

    if lgbm_model is not None:
        model_order.append("TwoTower+LGBM")
        rank_fns["TwoTower+LGBM"] = lambda items, m=lgbm_model: rank_by_lgbm(items, m)

    for i, name in enumerate(model_order):
        if args.verbose:
            print(f"[{i + 1}/{len(model_order)}] Evaluating {name}...")
        models[name] = evaluate_model(
            groups, rank_fns[name], args.k_values,
            genres_map, pop_map, args.n_bootstrap,
        )

    # -- Ablation --
    ablation_stages = ["Popularity", "MBTI-only", "Hybrid v1", "TwoTower only"]
    if lgbm_model is not None:
        ablation_stages.append("TwoTower+LGBM")

    stage_labels = {
        "Popularity": "Popularity only",
        "MBTI-only": "+ MBTI",
        "Hybrid v1": "+ 5-axis Hybrid",
        "TwoTower only": "+ Two-Tower",
        "TwoTower+LGBM": "+ LGBM Reranker",
    }

    ablation_rows: list[tuple[str, str, str]] = []
    prev_val = 0.0
    for stage in ablation_stages:
        val = models[stage]["metrics"]["ndcg"].get("@10", 0)
        delta = f"{(val - prev_val) / prev_val * 100:+.1f}%" if prev_val > 0 else "-"
        ablation_rows.append((stage_labels[stage], f"{val:.4f}", delta))
        prev_val = val

    # -- Generate report --
    md = generate_markdown(models, args.k_values, dataset_info, ablation_rows)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "comparison_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    # Full JSON
    full_json = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": dataset_info,
        "n_samples": len(records),
        "n_users": len(users),
        "n_requests": len(groups),
        "models": {name: res for name, res in models.items()},
        "ablation": [{"stage": s, "ndcg10": v, "delta": d} for s, v, d in ablation_rows],
    }
    json_path = out_dir / "comparison_full.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_json, f, ensure_ascii=False, indent=2, default=str)

    # -- Console output --
    print("=" * 70)
    print("RecFlix Model Comparison Report")
    print(f"Dataset: {dataset_info}")
    print()

    # Summary table
    print(f"{'Model':<22} ", end="")
    for k in args.k_values:
        print(f"{'NDCG@'+str(k):>10}", end="")
    print(f"{'Recall@10':>12}{'MRR@10':>10}{'HitRate@10':>12}")
    print("-" * 86)

    for name in model_order:
        m = models[name]["metrics"]
        print(f"{name:<22} ", end="")
        for k in args.k_values:
            print(f"{m['ndcg'].get(f'@{k}', 0):>10.4f}", end="")
        print(f"{m['recall'].get('@10', 0):>12.4f}{m['mrr'].get('@10', 0):>10.4f}{m['hit_rate'].get('@10', 0):>12.4f}")

    # Ablation
    print()
    print("Ablation Study (NDCG@10):")
    for stage, val_str, delta in ablation_rows:
        print(f"  {stage:<22} {val_str}  {delta}")

    # Diversity
    print()
    print(f"{'Model':<22} {'Coverage@10':>12} {'Novelty@10':>12}")
    print("-" * 48)
    for name in model_order:
        m = models[name]["metrics"]
        print(f"{name:<22} {m['coverage'].get('@10', 0):>12.4f} {m['novelty'].get('@10', 0):>12.2f}")

    print()
    print(f"Artifacts: {md_path}, {json_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
