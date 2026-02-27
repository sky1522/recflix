# ruff: noqa: T201
"""
RecFlix Synthetic Interaction Data Generator

42,917편의 영화 메타데이터를 활용하여 가상 사용자 상호작용을 생성합니다.
Two-Tower 사전학습 및 파이프라인 검증용.

Usage:
    python backend/scripts/generate_synthetic_data.py \
        --db-url "$DATABASE_URL" \
        --n-users 500 \
        --output-dir data/synthetic/ \
        --seed 42 --verbose
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP",
]
WEATHER_TYPES = ["sunny", "rainy", "cloudy", "snowy"]
MOOD_TYPES = ["happy", "sad", "excited", "calm", "tired", "emotional"]
SECTIONS = ["hybrid_row", "popular", "mbti_picks", "weather_picks", "mood_picks"]

# Synthetic 데이터 기간 (30일)
BASE_DATE = datetime(2026, 1, 1, tzinfo=UTC)
DATE_SPAN_DAYS = 30


# ---------------------------------------------------------------------------
# DB loading
# ---------------------------------------------------------------------------

def load_movies(engine, verbose: bool = False) -> list[dict]:
    """movies 테이블에서 필요한 메타데이터를 로드합니다."""
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
            "mbti_scores": r["mbti_scores"] or {},
            "weather_scores": r["weather_scores"] or {},
            "emotion_tags": r["emotion_tags"] or {},
            "genres": list(genres_raw) if genres_raw else [],
        })

    if verbose:
        print(f"  Loaded {len(movies)} movies from DB")
    return movies


def get_all_genres(movies: list[dict]) -> list[str]:
    """전체 장르 목록 추출."""
    genres: set[str] = set()
    for m in movies:
        genres.update(m["genres"])
    return sorted(genres)


# ---------------------------------------------------------------------------
# Synthetic user generation
# ---------------------------------------------------------------------------

def generate_users(n_users: int, all_genres: list[str]) -> list[dict]:
    """가상 사용자 생성."""
    users = []
    for idx in range(n_users):
        users.append({
            "user_id": f"synthetic_{idx}",
            "mbti": random.choice(MBTI_TYPES),
            "preferred_genres": random.sample(all_genres, k=min(random.randint(2, 5), len(all_genres))),
            "weather": random.choice(WEATHER_TYPES),
            "mood": random.choice(MOOD_TYPES),
        })
    return users


# ---------------------------------------------------------------------------
# Interaction simulation
# ---------------------------------------------------------------------------

def click_probability(movie: dict, user: dict) -> float:
    """영화-사용자 조합의 클릭 확률 계산."""
    mbti_score = movie["mbti_scores"].get(user["mbti"], 0)
    weather_score = movie["weather_scores"].get(user["weather"], 0)
    genre_match = (
        len(set(movie["genres"]) & set(user["preferred_genres"]))
        / max(len(user["preferred_genres"]), 1)
    )
    quality = movie["weighted_score"] / 10.0

    prob = 0.3 * mbti_score + 0.2 * weather_score + 0.3 * genre_match + 0.2 * quality
    return min(prob, 0.95)


def determine_label(prob: float) -> int:
    """확률 기반 라벨 결정."""
    rand = random.random()
    if rand < prob * 0.15:
        return 3  # strong positive
    if rand < prob * 0.35:
        return 2  # positive
    if rand < prob * 0.60:
        return 1  # weak positive
    return 0  # negative


def select_candidates(
    all_movies: list[dict],
    user: dict,
    n_candidates: int,
) -> list[dict]:
    """노출 후보 영화 선택 (MBTI 상위 + 랜덤 혼합)."""
    # MBTI 점수 상위 영화
    mbti_key = user["mbti"]
    high_score = [m for m in all_movies if m["mbti_scores"].get(mbti_key, 0) > 0.3]
    high_score.sort(key=lambda m: m["mbti_scores"].get(mbti_key, 0), reverse=True)
    top_mbti = high_score[:30]

    # 랜덤 풀
    random_pool = random.sample(all_movies, min(50, len(all_movies)))

    # 합치고 중복 제거
    seen: set[int] = set()
    candidates: list[dict] = []
    for m in top_mbti + random_pool:
        if m["id"] not in seen:
            seen.add(m["id"])
            candidates.append(m)
        if len(candidates) >= n_candidates:
            break

    # 부족하면 추가 랜덤
    if len(candidates) < n_candidates:
        remaining = [m for m in all_movies if m["id"] not in seen]
        extra = random.sample(remaining, min(n_candidates - len(candidates), len(remaining)))
        candidates.extend(extra)

    return candidates[:n_candidates]


def generate_session(
    user: dict,
    candidates: list[dict],
    session_idx: int,
    session_time: datetime,
) -> list[dict]:
    """하나의 추천 세션에 대한 상호작용 레코드를 생성합니다."""
    # 결정론적 UUID: seed 기반 재현성을 위해 random 모듈 사용
    request_id = str(uuid.UUID(int=random.getrandbits(128), version=4))
    session_id = f"synthetic_session_{user['user_id'].split('_')[1]}_{session_idx}"

    # score 기반 정렬 (click_probability를 score로 사용)
    scored = [(m, click_probability(m, user)) for m in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)

    records: list[dict] = []
    for rank, (movie, prob) in enumerate(scored):
        label = determine_label(prob)

        # interacted_at: label > 0이면 served_at + 10~120초
        interacted_at = None
        if label > 0:
            delta_sec = random.randint(10, 120)
            interacted_at = (session_time + timedelta(seconds=delta_sec)).isoformat()

        records.append({
            "request_id": request_id,
            "user_id": user["user_id"],
            "session_id": session_id,
            "movie_id": movie["id"],
            "rank": rank,
            "score": round(prob, 4),
            "section": random.choice(SECTIONS),
            "label": label,
            "algorithm_version": "synthetic_v1",
            "experiment_group": "synthetic",
            "context": {
                "weather": user["weather"],
                "mood": user["mood"],
                "mbti": user["mbti"],
            },
            "features": {
                "genres": movie["genres"],
                "weighted_score": movie["weighted_score"],
                "emotion_tags": movie["emotion_tags"],
                "mbti_score": movie["mbti_scores"].get(user["mbti"], 0),
                "weather_score": movie["weather_scores"].get(user["weather"], 0),
            },
            "served_at": session_time.isoformat(),
            "interacted_at": interacted_at,
        })

    return records


# ---------------------------------------------------------------------------
# Temporal split (Step 02A 호환)
# ---------------------------------------------------------------------------

def temporal_split(events: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """시간순 70/15/15 분리."""
    n = len(events)
    t1 = int(n * 0.70)
    t2 = int(n * 0.85)
    return events[:t1], events[t1:t2], events[t2:]


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
    users: list[dict],
    train: list[dict],
    valid: list[dict],
    test: list[dict],
) -> dict:
    """통계 딕셔너리."""
    n = len(all_events)
    label_dist = defaultdict(int)
    movies_seen: set[int] = set()
    sessions: set[str] = set()
    mbti_dist: dict[str, int] = defaultdict(int)

    for e in all_events:
        label_dist[e["label"]] += 1
        movies_seen.add(e["movie_id"])
        sessions.add(e["request_id"])

    for u in users:
        mbti_dist[u["mbti"]] += 1

    all_genres: set[str] = set()
    for e in all_events:
        all_genres.update(e.get("features", {}).get("genres", []))

    return {
        "generated": datetime.now(UTC).isoformat(),
        "n_users": len(users),
        "n_sessions": len(sessions),
        "total_impressions": n,
        "label_distribution": {
            "0_negative": label_dist.get(0, 0),
            "1_weak_positive": label_dist.get(1, 0),
            "2_positive": label_dist.get(2, 0),
            "3_strong_positive": label_dist.get(3, 0),
        },
        "positive_rate": round(sum(c for lbl, c in label_dist.items() if lbl > 0) / n * 100, 1) if n else 0,
        "mbti_distribution": dict(sorted(mbti_dist.items())),
        "genre_coverage": len(all_genres),
        "movie_coverage": len(movies_seen),
        "split": {
            "train": len(train),
            "valid": len(valid),
            "test": len(test),
        },
    }


def print_report(stats: dict, total_movies: int) -> None:
    """통계 리포트 출력."""
    n = stats["total_impressions"]
    ld = stats["label_distribution"]

    print("=" * 60)
    print("RecFlix Synthetic Data Generator")
    print(f"Generated: {stats['generated']}")
    print(f"Users: {stats['n_users']} synthetic")
    print(f"Sessions: {stats['n_sessions']:,}")
    print(f"Total impressions: {n:,}")

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
        print(f"  {name:25s} {count:>8,} ({pct}%)")

    print(f"Positive rate (label>0): {stats['positive_rate']}%")

    mbti = stats["mbti_distribution"]
    mbti_str = ", ".join(f"{k}({v})" for k, v in list(mbti.items())[:8])
    print(f"MBTI distribution: {mbti_str}, ...")
    print(f"Genre coverage: {stats['genre_coverage']} genres")
    print(f"Movie coverage: {stats['movie_coverage']:,}/{total_movies:,} ({stats['movie_coverage'] / total_movies * 100:.1f}%)")

    sp = stats["split"]
    print("Split:")
    for name in ["train", "valid", "test"]:
        cnt = sp[name]
        pct = round(cnt / n * 100, 1) if n else 0
        print(f"  {name.capitalize():6s}: {cnt:>8,} ({pct}%)")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="RecFlix Synthetic Data Generator")
    parser.add_argument("--db-url", default=os.getenv("DATABASE_URL"), help="PostgreSQL connection URL")
    parser.add_argument("--n-users", type=int, default=500, help="Number of synthetic users")
    parser.add_argument("--sessions-per-user", type=int, default=2, help="Max sessions per user")
    parser.add_argument("--candidates-per-session", type=int, default=80, help="Candidates per session")
    parser.add_argument("--output-dir", default="data/synthetic/", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    if not args.db_url:
        print("ERROR: --db-url or DATABASE_URL environment variable required.", file=sys.stderr)
        sys.exit(1)

    random.seed(args.seed)

    engine = create_engine(args.db_url)

    # 1. Load movies
    if args.verbose:
        print("[1/5] Loading movies from DB...")
    all_movies = load_movies(engine, verbose=args.verbose)

    if not all_movies:
        print("ERROR: No movies found in DB.", file=sys.stderr)
        sys.exit(1)

    all_genres = get_all_genres(all_movies)
    if args.verbose:
        print(f"  {len(all_genres)} genres found")

    # 2. Generate users
    if args.verbose:
        print(f"[2/5] Generating {args.n_users} synthetic users...")
    users = generate_users(args.n_users, all_genres)

    # 3. Generate interactions
    if args.verbose:
        print("[3/5] Generating interactions...")
    all_records: list[dict] = []

    for user in users:
        n_sessions = random.randint(1, args.sessions_per_user)
        for session_idx in range(n_sessions):
            # 세션 시간: 30일 기간에 걸쳐 분산
            day_offset = random.uniform(0, DATE_SPAN_DAYS)
            hour_offset = random.uniform(0, 24)
            session_time = BASE_DATE + timedelta(days=day_offset, hours=hour_offset)

            candidates = select_candidates(all_movies, user, args.candidates_per_session)
            records = generate_session(user, candidates, session_idx, session_time)
            all_records.extend(records)

    # 시간순 정렬
    all_records.sort(key=lambda x: x["served_at"])

    if args.verbose:
        print(f"  Generated {len(all_records):,} records")

    # 4. Split
    if args.verbose:
        print("[4/5] Splitting dataset...")
    train, valid, test = temporal_split(all_records)

    # 5. Write output
    if args.verbose:
        print("[5/5] Writing output files...")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(out_dir / "train.jsonl", train)
    write_jsonl(out_dir / "valid.jsonl", valid)
    write_jsonl(out_dir / "test.jsonl", test)

    stats = build_stats(all_records, users, train, valid, test)
    with open(out_dir / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2, default=str)

    print_report(stats, total_movies=len(all_movies))
    print(f"\nFiles written to {out_dir}/")
    print(f"  train.jsonl  ({len(train):,} records)")
    print(f"  valid.jsonl  ({len(valid):,} records)")
    print(f"  test.jsonl   ({len(test):,} records)")
    print("  stats.json")


if __name__ == "__main__":
    main()
