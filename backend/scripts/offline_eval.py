# ruff: noqa: T201
"""
RecFlix Offline Evaluation

test.jsonl을 로드하여 Popularity / MBTI-only / Current Model 3종의
오프라인 성능을 NDCG, Recall, MRR, HitRate, Coverage, Novelty로 평가합니다.

Usage:
    python backend/scripts/offline_eval.py \
        --test-file data/offline/test.jsonl \
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
# Metric functions
# ---------------------------------------------------------------------------

def ndcg_at_k(ranked_movie_ids: list[int], relevance: dict[int, float], k: int) -> float:
    """Normalized Discounted Cumulative Gain."""
    dcg = sum(
        relevance.get(mid, 0) / math.log2(i + 2)
        for i, mid in enumerate(ranked_movie_ids[:k])
    )
    ideal = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def recall_at_k(ranked_movie_ids: list[int], relevant_set: set[int], k: int) -> float:
    """Top-K에 positive(label>0) 영화가 얼마나 들어왔는가."""
    if not relevant_set:
        return 0.0
    hits = len(set(ranked_movie_ids[:k]) & relevant_set)
    return hits / min(len(relevant_set), k)


def mrr_at_k(ranked_movie_ids: list[int], relevant_set: set[int], k: int) -> float:
    """첫 번째 positive의 역순위."""
    for i, mid in enumerate(ranked_movie_ids[:k]):
        if mid in relevant_set:
            return 1.0 / (i + 1)
    return 0.0


def hit_rate_at_k(ranked_movie_ids: list[int], relevant_set: set[int], k: int) -> float:
    """Top-K에 positive가 1개라도 있으면 1, 없으면 0."""
    return 1.0 if set(ranked_movie_ids[:k]) & relevant_set else 0.0


def genre_coverage(
    ranked_movie_ids: list[int],
    movie_genres: dict[int, list[str]],
    k: int,
    total_genres: int = 19,
) -> float:
    """추천된 영화가 커버하는 장르 비율."""
    genres: set[str] = set()
    for mid in ranked_movie_ids[:k]:
        genres.update(movie_genres.get(mid, []))
    return len(genres) / total_genres


def novelty(ranked_movie_ids: list[int], popularity: dict[int, float], k: int) -> float:
    """덜 인기 있는 영화를 추천할수록 높은 점수."""
    scores = [
        -math.log2(max(popularity.get(mid, 1e-6), 1e-6))
        for mid in ranked_movie_ids[:k]
    ]
    return sum(scores) / len(scores) if scores else 0.0


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------

def bootstrap_ci(
    values: list[float],
    n_bootstrap: int = 1000,
    ci: float = 0.95,
) -> tuple[float, float, float]:
    """유저/request 단위 metric 리스트로 95% CI 계산.

    Returns: (mean, ci_lower, ci_upper)
    """
    arr = np.array(values)
    if len(arr) <= 1:
        mean_val = float(np.mean(arr)) if len(arr) == 1 else 0.0
        return mean_val, mean_val, mean_val

    rng = np.random.default_rng(42)
    means = sorted(
        float(np.mean(rng.choice(arr, size=len(arr), replace=True)))
        for _ in range(n_bootstrap)
    )
    alpha = (1 - ci) / 2
    lower = means[int(alpha * n_bootstrap)]
    upper = means[min(int((1 - alpha) * n_bootstrap), len(means) - 1)]
    return float(np.mean(arr)), lower, upper


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_test_data(path: Path) -> list[dict]:
    """test.jsonl 로드."""
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def group_by_request(records: list[dict]) -> dict[str, list[dict]]:
    """request_id별 그룹핑."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        groups[rec["request_id"]].append(rec)
    return dict(groups)


# ---------------------------------------------------------------------------
# Ranking strategies
# ---------------------------------------------------------------------------

def rank_by_score(items: list[dict]) -> list[int]:
    """score 내림차순 정렬 (현재 모델)."""
    sorted_items = sorted(items, key=lambda x: (x.get("score") or 0), reverse=True)
    return [item["movie_id"] for item in sorted_items]


def rank_by_popularity(items: list[dict]) -> list[int]:
    """weighted_score 내림차순 정렬 (Popularity 베이스라인)."""
    sorted_items = sorted(
        items,
        key=lambda x: (x.get("features", {}).get("weighted_score") or 0),
        reverse=True,
    )
    return [item["movie_id"] for item in sorted_items]


def rank_by_mbti(items: list[dict]) -> list[int]:
    """mbti_score 내림차순 정렬 (MBTI-only 베이스라인).

    context.mbti가 없으면 Popularity fallback.
    """
    ctx = items[0].get("context") or {} if items else {}
    if not ctx.get("mbti"):
        return rank_by_popularity(items)
    sorted_items = sorted(
        items,
        key=lambda x: (x.get("features", {}).get("mbti_score") or 0),
        reverse=True,
    )
    return [item["movie_id"] for item in sorted_items]


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate_model(
    request_groups: dict[str, list[dict]],
    rank_fn,
    k_values: list[int],
    movie_genres: dict[int, list[str]],
    movie_popularity: dict[int, float],
    n_bootstrap: int = 1000,
) -> dict:
    """하나의 랭킹 전략에 대해 모든 지표를 계산합니다."""
    # request_id별 지표 수집
    per_request: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for _req_id, items in request_groups.items():
        ranked = rank_fn(items)
        relevance = {item["movie_id"]: item["label"] for item in items}
        relevant_set = {mid for mid, lbl in relevance.items() if lbl > 0}

        for k in k_values:
            per_request["ndcg"][f"@{k}"].append(ndcg_at_k(ranked, relevance, k))
            per_request["recall"][f"@{k}"].append(recall_at_k(ranked, relevant_set, k))
            per_request["mrr"][f"@{k}"].append(mrr_at_k(ranked, relevant_set, k))
            per_request["hit_rate"][f"@{k}"].append(hit_rate_at_k(ranked, relevant_set, k))
            per_request["coverage"][f"@{k}"].append(genre_coverage(ranked, movie_genres, k))
            per_request["novelty"][f"@{k}"].append(novelty(ranked, movie_popularity, k))

    # 집계
    metrics: dict[str, dict[str, float]] = {}
    ci_95: dict[str, list[float]] = {}

    for metric_name, k_dict in per_request.items():
        metrics[metric_name] = {}
        for k_label, values in k_dict.items():
            mean, lower, upper = bootstrap_ci(values, n_bootstrap=n_bootstrap)
            metrics[metric_name][k_label] = round(mean, 4)
            if k_label == "@10":
                ci_95[f"{metric_name}{k_label}"] = [round(lower, 4), round(upper, 4)]

    return {"metrics": metrics, "ci_95": ci_95}


def evaluate_per_group(
    request_groups: dict[str, list[dict]],
    rank_fn,
    k_values: list[int],
    movie_genres: dict[int, list[str]],
    movie_popularity: dict[int, float],
) -> dict[str, dict[str, float]]:
    """experiment_group별 NDCG@10, Recall@10 집계."""
    group_metrics: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for _req_id, items in request_groups.items():
        exp_group = items[0].get("experiment_group", "unknown")
        ranked = rank_fn(items)
        relevance = {item["movie_id"]: item["label"] for item in items}
        relevant_set = {mid for mid, lbl in relevance.items() if lbl > 0}

        k = 10
        group_metrics[exp_group]["ndcg@10"].append(ndcg_at_k(ranked, relevance, k))
        group_metrics[exp_group]["recall@10"].append(recall_at_k(ranked, relevant_set, k))

    result: dict[str, dict[str, float]] = {}
    for grp, m_dict in group_metrics.items():
        result[grp] = {
            metric: round(float(np.mean(vals)), 4)
            for metric, vals in m_dict.items()
        }
    return result


# ---------------------------------------------------------------------------
# Build auxiliary maps from test data
# ---------------------------------------------------------------------------

def build_movie_maps(records: list[dict]) -> tuple[dict[int, list[str]], dict[int, float]]:
    """test.jsonl에서 movie_genres 및 popularity 맵을 추출합니다."""
    movie_genres: dict[int, list[str]] = {}
    movie_popularity: dict[int, float] = {}

    for rec in records:
        mid = rec["movie_id"]
        feat = rec.get("features") or {}
        if mid not in movie_genres:
            movie_genres[mid] = feat.get("genres", [])
        if mid not in movie_popularity:
            ws = feat.get("weighted_score")
            if ws is not None:
                # popularity를 0~1 범위로 정규화 (novelty 계산용)
                movie_popularity[mid] = max(ws / 10.0, 1e-6)

    return movie_genres, movie_popularity


# ---------------------------------------------------------------------------
# Report printing
# ---------------------------------------------------------------------------

METRIC_ORDER = ["ndcg", "recall", "mrr", "hit_rate", "coverage", "novelty"]
METRIC_DISPLAY = {
    "ndcg": "NDCG",
    "recall": "Recall",
    "mrr": "MRR",
    "hit_rate": "HitRate",
    "coverage": "Coverage",
    "novelty": "Novelty",
}


def print_model_table(title: str, result: dict, k_values: list[int]) -> None:
    """단일 모델 지표 테이블 출력."""
    metrics = result["metrics"]
    ci_95 = result["ci_95"]

    k_headers = [f"@{k}" for k in k_values]
    col_w = 10
    header = f"{'Metric':<{col_w}}" + "".join(f"{h:>{col_w}}" for h in k_headers) + f"{'95% CI(@10)':>14}"
    sep = "─" * len(header)

    print(f"\n{title}")
    print(f"┌{sep}┐")
    print(f"│{header}│")
    print(f"├{sep}┤")

    for metric in METRIC_ORDER:
        if metric not in metrics:
            continue
        display = METRIC_DISPLAY.get(metric, metric)
        vals = [f"{metrics[metric].get(f'@{k}', 0):.3f}" for k in k_values]
        ci_key = f"{metric}@10"
        if ci_key in ci_95:
            ci_lo, ci_hi = ci_95[ci_key]
            ci_str = f"±{(ci_hi - ci_lo) / 2:.3f}"
        else:
            ci_str = "-"
        row = f"{display:<{col_w}}" + "".join(f"{v:>{col_w}}" for v in vals) + f"{ci_str:>14}"
        print(f"│{row}│")

    print(f"└{sep}┘")


def print_comparison_table(results: dict[str, dict], reference: str) -> None:
    """NDCG@10 기준 비교 테이블 출력."""
    ref_val = results[reference]["metrics"]["ndcg"]["@10"]

    print("\n" + "=" * 60)
    print("Comparison vs Current Model (NDCG@10)")
    col_w = 18
    header = f"{'Model':<{col_w}}{'NDCG@10':>10}{'Δ':>10}{'Δ%':>10}"
    sep = "─" * len(header)
    print(f"┌{sep}┐")
    print(f"│{header}│")
    print(f"├{sep}┤")

    for name, res in results.items():
        val = res["metrics"]["ndcg"]["@10"]
        if name == reference:
            delta, delta_pct = "-", "-"
        else:
            d = val - ref_val
            dp = (d / ref_val * 100) if ref_val else 0
            delta = f"{d:+.3f}"
            delta_pct = f"{dp:+.1f}%"
        row = f"{name:<{col_w}}{val:>10.3f}{delta:>10}{delta_pct:>10}"
        print(f"│{row}│")

    print(f"└{sep}┘")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="RecFlix Offline Evaluation")
    parser.add_argument("--test-file", required=True, help="Path to test.jsonl")
    parser.add_argument("--output-dir", default="data/offline/reports/", help="Output directory for JSON reports")
    parser.add_argument("--k-values", nargs="+", type=int, default=[5, 10, 20], help="K values for @K metrics")
    parser.add_argument("--n-bootstrap", type=int, default=1000, help="Number of bootstrap samples")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    test_path = Path(args.test_file)
    if not test_path.exists():
        print(f"ERROR: File not found: {test_path}", file=sys.stderr)
        sys.exit(1)

    # 1. Load data
    records = load_test_data(test_path)
    if not records:
        print("No test data found.")
        sys.exit(0)

    request_groups = group_by_request(records)
    unique_users = {r.get("user_id") or r.get("session_id") for r in records}
    n_positive = sum(1 for r in records if r["label"] > 0)

    if args.verbose:
        print(f"Loaded {len(records)} samples, {len(unique_users)} users, {len(request_groups)} requests")
        print(f"Positive samples (label>0): {n_positive}")

    if n_positive == 0:
        print("WARNING: No positive labels (label>0) found. All metrics will be 0.")

    # 2. Build auxiliary maps
    movie_genres, movie_popularity = build_movie_maps(records)

    # 3. Evaluate models
    print("=" * 60)
    print("RecFlix Offline Evaluation Report")
    print(f"Dataset: {test_path} ({len(records)} samples, {len(unique_users)} users, {len(request_groups)} requests)")
    print(f"Generated: {datetime.now(UTC).isoformat()}")

    models: dict[str, dict] = {}

    # Popularity baseline
    if args.verbose:
        print("\n[1/3] Evaluating Popularity baseline...")
    pop_result = evaluate_model(
        request_groups, rank_by_popularity, args.k_values,
        movie_genres, movie_popularity, args.n_bootstrap,
    )
    models["Popularity"] = pop_result
    print_model_table("[1/3] Popularity Baseline (weighted_score ordering)", pop_result, args.k_values)

    # MBTI-only baseline
    if args.verbose:
        print("\n[2/3] Evaluating MBTI-only baseline...")
    mbti_result = evaluate_model(
        request_groups, rank_by_mbti, args.k_values,
        movie_genres, movie_popularity, args.n_bootstrap,
    )
    models["MBTI-only"] = mbti_result
    print_model_table("[2/3] MBTI-only Baseline (mbti_score ordering)", mbti_result, args.k_values)

    # Current model
    if args.verbose:
        print("\n[3/3] Evaluating Current model...")
    current_result = evaluate_model(
        request_groups, rank_by_score, args.k_values,
        movie_genres, movie_popularity, args.n_bootstrap,
    )
    per_group = evaluate_per_group(
        request_groups, rank_by_score, args.k_values,
        movie_genres, movie_popularity,
    )
    current_result["per_group"] = per_group
    models["Current (hybrid)"] = current_result
    print_model_table("[3/3] Current Model (score ordering = hybrid)", current_result, args.k_values)

    # Comparison
    print_comparison_table(models, reference="Current (hybrid)")

    # 4. Write JSON reports
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(UTC).strftime("%Y%m%d")

    for name, result in models.items():
        safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        report = {
            "model_name": name,
            "dataset": str(test_path),
            "generated_at": datetime.now(UTC).isoformat(),
            "n_samples": len(records),
            "n_users": len(unique_users),
            "n_requests": len(request_groups),
            "metrics": result["metrics"],
            "ci_95": result["ci_95"],
        }
        if "per_group" in result:
            report["per_group"] = result["per_group"]

        report_path = out_dir / f"eval_{safe_name}_{date_str}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    print(f"\nJSON reports written to {out_dir}/")


if __name__ == "__main__":
    main()
