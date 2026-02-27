# ruff: noqa: T201
"""
오프라인 Interleaving 시뮬레이션.

test.jsonl 기반으로 두 모델의 Team Draft Interleaving 비교를 수행합니다.

Usage:
    python backend/scripts/run_interleaving.py \
        --test-file data/synthetic/test.jsonl \
        --model-a-name "Hybrid v1" \
        --model-b-name "TwoTower+LGBM" \
        --lgbm-model data/models/reranker/lgbm_v1.txt \
        --k 20 \
        --output-dir data/offline/reports/
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

# LGBM 피처 상수
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


def extract_features(rec: dict) -> np.ndarray:
    """JSONL 레코드 → 76dim float 벡터."""
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


# ---------------------------------------------------------------------------
# Interleaving (인라인 — app/services/interleaving.py와 동일 로직)
# ---------------------------------------------------------------------------

def team_draft_interleave(
    list_a: list[int],
    list_b: list[int],
    k: int = 20,
) -> tuple[list[int], set[int], set[int]]:
    interleaved: list[int] = []
    team_a: set[int] = set()
    team_b: set[int] = set()
    seen: set[int] = set()
    ptr_a = 0
    ptr_b = 0

    while len(interleaved) < k and (ptr_a < len(list_a) or ptr_b < len(list_b)):
        a_turn = len(team_a) < len(team_b) or (
            len(team_a) == len(team_b) and random.random() < 0.5
        )
        if a_turn:
            while ptr_a < len(list_a) and list_a[ptr_a] in seen:
                ptr_a += 1
            if ptr_a < len(list_a):
                interleaved.append(list_a[ptr_a])
                team_a.add(list_a[ptr_a])
                seen.add(list_a[ptr_a])
                ptr_a += 1
            else:
                while ptr_b < len(list_b) and list_b[ptr_b] in seen:
                    ptr_b += 1
                if ptr_b < len(list_b):
                    interleaved.append(list_b[ptr_b])
                    team_b.add(list_b[ptr_b])
                    seen.add(list_b[ptr_b])
                    ptr_b += 1
        else:
            while ptr_b < len(list_b) and list_b[ptr_b] in seen:
                ptr_b += 1
            if ptr_b < len(list_b):
                interleaved.append(list_b[ptr_b])
                team_b.add(list_b[ptr_b])
                seen.add(list_b[ptr_b])
                ptr_b += 1
            else:
                while ptr_a < len(list_a) and list_a[ptr_a] in seen:
                    ptr_a += 1
                if ptr_a < len(list_a):
                    interleaved.append(list_a[ptr_a])
                    team_a.add(list_a[ptr_a])
                    seen.add(list_a[ptr_a])
                    ptr_a += 1

    return interleaved, team_a, team_b


def compute_result(team_a: set[int], team_b: set[int], clicked: set[int]) -> str:
    sa = len(clicked & team_a)
    sb = len(clicked & team_b)
    if sa > sb:
        return "A"
    if sb > sa:
        return "B"
    return "tie"


def wilson_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval."""
    if n == 0:
        return 0.0, 1.0
    denom = 1 + z * z / n
    import math
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Offline Interleaving Simulation")
    parser.add_argument("--test-file", required=True)
    parser.add_argument("--model-a-name", default="Hybrid v1")
    parser.add_argument("--model-b-name", default="TwoTower+LGBM")
    parser.add_argument("--lgbm-model", default="data/models/reranker/lgbm_v1.txt")
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument("--output-dir", default="data/offline/reports/")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    test_path = Path(args.test_file)
    if not test_path.exists():
        print(f"ERROR: {test_path} not found", file=sys.stderr)
        sys.exit(1)

    # Load data
    records: list[dict] = []
    with open(test_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        print("No data.")
        sys.exit(0)

    groups: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        groups[rec["request_id"]].append(rec)

    # Load LGBM
    lgbm_model = None
    lgbm_path = Path(args.lgbm_model)
    if lgbm_path.exists():
        try:
            import lightgbm as lgb
            lgbm_model = lgb.Booster(model_file=str(lgbm_path))
        except Exception as e:
            print(f"LGBM load failed: {e}")
            sys.exit(1)
    else:
        print(f"LGBM model not found: {lgbm_path}")
        sys.exit(1)

    # Run interleaving
    session_results: list[str] = []
    per_session: list[dict] = []

    for req_id, items in groups.items():
        # Model A: score 내림차순 (Hybrid)
        list_a = [it["movie_id"] for it in sorted(items, key=lambda x: (x.get("score") or 0), reverse=True)]

        # Model B: LGBM predict 내림차순
        x = np.array([extract_features(it) for it in items], dtype=np.float32)
        lgbm_scores = lgbm_model.predict(x)
        indexed = sorted(zip(items, lgbm_scores, strict=True), key=lambda t: t[1], reverse=True)
        list_b = [it["movie_id"] for it, _ in indexed]

        interleaved, team_a, team_b = team_draft_interleave(list_a, list_b, k=args.k)

        clicked = {it["movie_id"] for it in items if it.get("label", 0) > 0}
        result = compute_result(team_a, team_b, clicked)
        session_results.append(result)

        per_session.append({
            "request_id": req_id,
            "result": result,
            "a_clicks": len(clicked & team_a),
            "b_clicks": len(clicked & team_b),
            "interleaved_size": len(interleaved),
        })

    # Compute stats
    a_wins = session_results.count("A")
    b_wins = session_results.count("B")
    ties = session_results.count("tie")
    total = len(session_results)
    contested = a_wins + b_wins

    b_rate = b_wins / contested if contested > 0 else 0.5
    ci_lo, ci_hi = wilson_ci(b_rate, contested)

    # Output
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "generated_at": datetime.now(UTC).isoformat(),
        "dataset": str(test_path),
        "model_a": args.model_a_name,
        "model_b": args.model_b_name,
        "k": args.k,
        "sessions": total,
        "a_wins": a_wins,
        "b_wins": b_wins,
        "ties": ties,
        "b_win_rate": round(b_rate, 4),
        "ci_lower": round(ci_lo, 4),
        "ci_upper": round(ci_hi, 4),
        "per_session": per_session,
    }

    json_path = out_dir / "interleaving_result.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Console
    print("=" * 60)
    print(f"Interleaving Comparison: {args.model_a_name} vs {args.model_b_name}")
    print(f"Sessions: {total}, K={args.k}")
    print(f"Model A ({args.model_a_name}):     wins={a_wins} ({a_wins / total * 100:.1f}%)")
    print(f"Model B ({args.model_b_name}): wins={b_wins} ({b_wins / total * 100:.1f}%)")
    print(f"Ties:                    {ties} ({ties / total * 100:.1f}%)")
    if contested > 0:
        print(f"Win rate (B, excl ties): {b_rate * 100:.1f}% [95% CI: {ci_lo * 100:.1f}% - {ci_hi * 100:.1f}%]")
        if ci_lo > 0.5:
            print(f"Verdict: {args.model_b_name} significantly outperforms {args.model_a_name}")
        elif ci_hi < 0.5:
            print(f"Verdict: {args.model_a_name} significantly outperforms {args.model_b_name}")
        else:
            print("Verdict: No significant difference (CI overlaps 50%)")
    else:
        print("Verdict: All ties — no clear winner")
    print(f"\nJSON: {json_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
