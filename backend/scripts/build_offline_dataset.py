# ruff: noqa: T201
"""
RecFlix Offline Dataset Builder

reco_impressions + reco_interactions + reco_judgments를 조인하여
ML 학습/오프라인 평가용 JSONL 데이터셋을 생성합니다.

Usage:
    python backend/scripts/build_offline_dataset.py \
        --db-url "$DATABASE_URL" \
        --output-dir data/offline/ \
        --split temporal \
        --min-impressions 1 \
        --verbose
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Label computation
# ---------------------------------------------------------------------------

def compute_label(
    interactions: list[dict],
    judgments: list[dict],
) -> int:
    """하나의 impression(노출)에 대한 라벨 결정.

    판정 우선순위: judgment > favorite > dwell > click > none
    """
    # judgment가 있으면 최우선
    if judgments:
        ratings = [
            j["label_value"]
            for j in judgments
            if j["label_type"] == "rating"
        ]
        if ratings:
            rating = max(ratings)
            if rating >= 4.0:
                return 3  # strong positive
            if rating >= 3.0:
                return 2  # positive
            return 1  # weak positive (평점을 남긴 것 자체가 관심)

    # favorite
    if any(i["event_type"] == "favorite_add" for i in interactions):
        return 3  # strong positive

    # dwell time (상세 페이지 체류)
    dwell_values = [
        i["dwell_ms"]
        for i in interactions
        if i["event_type"] == "movie_detail_leave" and i.get("dwell_ms")
    ]
    if dwell_values and max(dwell_values) >= 30000:
        return 2  # positive (30초 이상 체류)

    # click
    click_types = {"movie_click", "movie_detail_view"}
    if any(i["event_type"] in click_types for i in interactions):
        return 1  # weak positive

    # 노출만 되고 반응 없음
    return 0  # negative


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def extract_features(movie: dict | None, context: dict | None) -> dict:
    """영화 메타데이터에서 피처를 추출합니다."""
    if movie is None:
        return {}

    ctx = context or {}
    mbti = ctx.get("mbti", "")
    weather = ctx.get("weather", "")

    mbti_scores = movie.get("mbti_scores") or {}
    weather_scores = movie.get("weather_scores") or {}
    emotion_tags = movie.get("emotion_tags") or {}

    return {
        "genres": movie.get("genres", []),
        "weighted_score": movie.get("weighted_score"),
        "emotion_tags": emotion_tags,
        "mbti_score": mbti_scores.get(mbti, 0) if mbti else 0,
        "weather_score": weather_scores.get(weather, 0) if weather else 0,
    }


# ---------------------------------------------------------------------------
# DB queries
# ---------------------------------------------------------------------------

def load_impressions(engine, verbose: bool = False) -> list[dict]:
    """reco_impressions 전체 로드 (served_at 순)."""
    query = text("""
        SELECT id, request_id::text, user_id, session_id,
               experiment_group, algorithm_version, section,
               movie_id, rank, score, context, served_at
        FROM reco_impressions
        ORDER BY served_at
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    if verbose:
        print(f"  Loaded {len(rows)} impressions")
    return [dict(r) for r in rows]


def load_interactions(engine, verbose: bool = False) -> dict[tuple, list[dict]]:
    """reco_interactions를 (request_id, movie_id) 기준으로 그룹화."""
    query = text("""
        SELECT request_id::text, movie_id, event_type,
               dwell_ms, interacted_at
        FROM reco_interactions
        WHERE request_id IS NOT NULL
    """)
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    for r in rows:
        key = (r["request_id"], r["movie_id"])
        grouped[key].append(dict(r))
    if verbose:
        print(f"  Loaded {sum(len(v) for v in grouped.values())} interactions ({len(grouped)} groups)")
    return grouped


def load_judgments(engine, verbose: bool = False) -> dict[tuple, list[dict]]:
    """reco_judgments를 (request_id, movie_id) 기준으로 그룹화."""
    query = text("""
        SELECT request_id::text, movie_id, label_type,
               label_value, judged_at
        FROM reco_judgments
        WHERE request_id IS NOT NULL
    """)
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    for r in rows:
        key = (r["request_id"], r["movie_id"])
        grouped[key].append(dict(r))
    if verbose:
        print(f"  Loaded {sum(len(v) for v in grouped.values())} judgments ({len(grouped)} groups)")
    return grouped


def load_movie_metadata(engine, movie_ids: set[int], verbose: bool = False) -> dict[int, dict]:
    """movies 테이블에서 필요한 메타데이터를 벌크 조회."""
    if not movie_ids:
        return {}

    query = text("""
        SELECT m.id, m.weighted_score, m.mbti_scores,
               m.weather_scores, m.emotion_tags,
               COALESCE(
                   (SELECT array_agg(g.name)
                    FROM movie_genres mg
                    JOIN genres g ON g.id = mg.genre_id
                    WHERE mg.movie_id = m.id),
                   '{}'
               ) AS genres
        FROM movies m
        WHERE m.id = ANY(:ids)
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"ids": list(movie_ids)}).mappings().all()
    result = {}
    for r in rows:
        genres_raw = r["genres"]
        if isinstance(genres_raw, str):
            genres_raw = [g.strip() for g in genres_raw.strip("{}").split(",") if g.strip()]
        result[r["id"]] = {
            "weighted_score": r["weighted_score"],
            "mbti_scores": r["mbti_scores"] or {},
            "weather_scores": r["weather_scores"] or {},
            "emotion_tags": r["emotion_tags"] or {},
            "genres": list(genres_raw) if genres_raw else [],
        }
    if verbose:
        print(f"  Loaded metadata for {len(result)} movies")
    return result


# ---------------------------------------------------------------------------
# Merge & label
# ---------------------------------------------------------------------------

def merge_and_label(
    impressions: list[dict],
    interactions: dict[tuple, list[dict]],
    judgments: dict[tuple, list[dict]],
    movie_map: dict[int, dict],
    min_impressions: int = 1,
    verbose: bool = False,
) -> list[dict]:
    """impression별로 interaction/judgment를 조인하여 라벨/피처 부여."""
    # min_impressions 필터용: 유저별 impression 수 집계
    if min_impressions > 1:
        user_counts: dict = defaultdict(int)
        for imp in impressions:
            uid = imp["user_id"] or imp["session_id"] or "anon"
            user_counts[uid] += 1
        valid_users = {u for u, c in user_counts.items() if c >= min_impressions}
    else:
        valid_users = None

    labeled: list[dict] = []
    for imp in impressions:
        uid = imp["user_id"] or imp["session_id"] or "anon"
        if valid_users is not None and uid not in valid_users:
            continue

        key = (imp["request_id"], imp["movie_id"])
        imp_interactions = interactions.get(key, [])
        imp_judgments = judgments.get(key, [])

        label = compute_label(imp_interactions, imp_judgments)

        # interacted_at: 가장 마지막 상호작용 시각
        all_times = []
        for i in imp_interactions:
            if i.get("interacted_at"):
                all_times.append(i["interacted_at"])
        for j in imp_judgments:
            if j.get("judged_at"):
                all_times.append(j["judged_at"])
        interacted_at = max(all_times) if all_times else None

        movie = movie_map.get(imp["movie_id"])
        context = imp.get("context")
        features = extract_features(movie, context)

        record = {
            "request_id": imp["request_id"],
            "user_id": imp["user_id"],
            "session_id": imp["session_id"],
            "movie_id": imp["movie_id"],
            "rank": imp["rank"],
            "score": imp["score"],
            "section": imp["section"],
            "label": label,
            "algorithm_version": imp["algorithm_version"],
            "experiment_group": imp["experiment_group"],
            "context": context,
            "features": features,
            "served_at": _iso(imp["served_at"]),
            "interacted_at": _iso(interacted_at) if interacted_at else None,
        }
        labeled.append(record)

    if verbose:
        print(f"  Merged: {len(labeled)} labeled events")
    return labeled


def _iso(dt) -> str | None:
    """datetime → ISO 8601 문자열."""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


# ---------------------------------------------------------------------------
# Temporal split
# ---------------------------------------------------------------------------

def temporal_split(
    events: list[dict],
    mode: str = "temporal",
) -> tuple[list[dict], list[dict], list[dict]]:
    """시간 기준 또는 비율 기준으로 train/valid/test 분리."""
    if not events:
        return [], [], []

    # events는 이미 served_at 순 정렬
    n = len(events)

    if mode == "ratio":
        t1 = int(n * 0.70)
        t2 = int(n * 0.85)
        return events[:t1], events[t1:t2], events[t2:]

    # temporal: 시간 기준 분리
    max_time = _parse_dt(events[-1]["served_at"])
    train_cutoff = max_time - timedelta(days=14)
    valid_cutoff = max_time - timedelta(days=7)

    train, valid, test = [], [], []
    for e in events:
        t = _parse_dt(e["served_at"])
        if t < train_cutoff:
            train.append(e)
        elif t < valid_cutoff:
            valid.append(e)
        else:
            test.append(e)

    # 최소 보장: train 50건 미만이면 비율 fallback
    if len(train) < 50:
        t1 = int(n * 0.70)
        t2 = int(n * 0.85)
        return events[:t1], events[t1:t2], events[t2:]

    return train, valid, test


def _parse_dt(dt_str: str | datetime) -> datetime:
    """ISO 문자열 또는 datetime을 tz-aware datetime으로 변환."""
    if isinstance(dt_str, datetime):
        if dt_str.tzinfo is None:
            return dt_str.replace(tzinfo=UTC)
        return dt_str
    # ISO 문자열 파싱
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_jsonl(path: Path, records: list[dict]) -> None:
    """JSONL 파일 작성."""
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def build_stats(
    all_events: list[dict],
    train: list[dict],
    valid: list[dict],
    test: list[dict],
) -> dict:
    """통계 리포트용 딕셔너리."""
    n = len(all_events)
    label_dist = defaultdict(int)
    users = set()
    movies = set()
    sections = defaultdict(int)
    algorithms = defaultdict(int)

    for e in all_events:
        label_dist[e["label"]] += 1
        uid = e["user_id"] or e["session_id"]
        if uid:
            users.add(uid)
        movies.add(e["movie_id"])
        sections[e["section"]] += 1
        algorithms[e["algorithm_version"]] += 1

    with_interaction = sum(cnt for lbl, cnt in label_dist.items() if lbl > 0)

    def _date_range(events: list[dict]) -> str:
        if not events:
            return "N/A"
        first = events[0]["served_at"][:10] if events else "?"
        last = events[-1]["served_at"][:10] if events else "?"
        return f"{first} ~ {last}"

    return {
        "generated": datetime.now(UTC).isoformat(),
        "total_impressions": n,
        "with_interaction": with_interaction,
        "interaction_rate": round(with_interaction / n * 100, 1) if n else 0,
        "label_distribution": {
            "0_negative": label_dist.get(0, 0),
            "1_weak_positive": label_dist.get(1, 0),
            "2_positive": label_dist.get(2, 0),
            "3_strong_positive": label_dist.get(3, 0),
        },
        "split": {
            "train": {"count": len(train), "pct": round(len(train) / n * 100, 1) if n else 0, "range": _date_range(train)},
            "valid": {"count": len(valid), "pct": round(len(valid) / n * 100, 1) if n else 0, "range": _date_range(valid)},
            "test": {"count": len(test), "pct": round(len(test) / n * 100, 1) if n else 0, "range": _date_range(test)},
        },
        "unique_users": len(users),
        "unique_movies": len(movies),
        "sections": dict(sorted(sections.items(), key=lambda x: -x[1])),
        "algorithms": dict(sorted(algorithms.items(), key=lambda x: -x[1])),
    }


def print_report(stats: dict) -> None:
    """통계 리포트를 stdout으로 출력."""
    n = stats["total_impressions"]
    ld = stats["label_distribution"]
    sp = stats["split"]

    print("=" * 60)
    print("RecFlix Offline Dataset Builder")
    print(f"Generated: {stats['generated']}")
    print(f"Total impressions: {n:,}")
    print(f"With interaction (label>0): {stats['with_interaction']:,} ({stats['interaction_rate']}%)")
    print("Label distribution:")
    label_names = {
        "0_negative": "0 (negative)",
        "1_weak_positive": "1 (weak positive)",
        "2_positive": "2 (positive)",
        "3_strong_positive": "3 (strong positive)",
    }
    for key, name in label_names.items():
        count = ld[key]
        pct = round(count / n * 100, 1) if n else 0
        print(f"  {name:25s} {count:>6,} ({pct}%)")
    print("Split:")
    for name in ["train", "valid", "test"]:
        s = sp[name]
        print(f"  {name.capitalize():6s}: {s['count']:>6,} ({s['pct']}%)  [{s['range']}]")
    print(f"Users: {stats['unique_users']} unique")
    print(f"Movies: {stats['unique_movies']} unique")
    sec_parts = [f"{k}({v})" for k, v in stats["sections"].items()]
    print(f"Sections: {', '.join(sec_parts)}")
    algo_parts = [f"{k}({v})" for k, v in stats["algorithms"].items()]
    print(f"Algorithms: {', '.join(algo_parts)}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Temporal split validation
# ---------------------------------------------------------------------------

def validate_split(train: list[dict], valid: list[dict], test: list[dict]) -> bool:
    """test의 min(served_at) > train의 max(served_at) 검증."""
    if not train or not test:
        return True
    train_max = _parse_dt(train[-1]["served_at"])
    test_min = _parse_dt(test[0]["served_at"])
    valid_ok = True
    if valid:
        valid_min = _parse_dt(valid[0]["served_at"])
        valid_ok = valid_min >= train_max
    return test_min >= train_max and valid_ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="RecFlix Offline Dataset Builder")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="PostgreSQL connection URL")
    parser.add_argument("--output-dir", default="data/offline/", help="Output directory")
    parser.add_argument("--split", choices=["temporal", "ratio"], default="temporal", help="Split strategy")
    parser.add_argument("--min-impressions", type=int, default=1, help="Min impressions per user")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    if not args.db_url:
        print("ERROR: --db-url or DATABASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(args.db_url)

    # 1. Load data
    if args.verbose:
        print("[1/5] Loading impressions...")
    impressions = load_impressions(engine, verbose=args.verbose)

    if not impressions:
        print("No impressions found. Run the service and collect data first.")
        sys.exit(0)

    if args.verbose:
        print("[2/5] Loading interactions & judgments...")
    interactions = load_interactions(engine, verbose=args.verbose)
    judgments = load_judgments(engine, verbose=args.verbose)

    # 2. Load movie metadata
    if args.verbose:
        print("[3/5] Loading movie metadata...")
    movie_ids = {imp["movie_id"] for imp in impressions}
    movie_map = load_movie_metadata(engine, movie_ids, verbose=args.verbose)

    # 3. Merge & label
    if args.verbose:
        print("[4/5] Merging and labeling...")
    labeled = merge_and_label(
        impressions, interactions, judgments, movie_map,
        min_impressions=args.min_impressions,
        verbose=args.verbose,
    )

    if not labeled:
        print("No events after filtering. Try lowering --min-impressions.")
        sys.exit(0)

    # 4. Split
    if args.verbose:
        print("[5/5] Splitting dataset...")
    train, valid, test = temporal_split(labeled, mode=args.split)

    # Validate temporal ordering
    if not validate_split(train, valid, test):
        print("WARNING: Temporal split validation failed — test data overlaps with train.", file=sys.stderr)

    # 5. Write output
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(out_dir / "train.jsonl", train)
    write_jsonl(out_dir / "valid.jsonl", valid)
    write_jsonl(out_dir / "test.jsonl", test)

    stats = build_stats(labeled, train, valid, test)
    with open(out_dir / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, default=str)

    print_report(stats)
    print(f"\nFiles written to {out_dir}/")
    print(f"  train.jsonl  ({len(train):,} records)")
    print(f"  valid.jsonl  ({len(valid):,} records)")
    print(f"  test.jsonl   ({len(test):,} records)")
    print("  stats.json")


if __name__ == "__main__":
    main()
