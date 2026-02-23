"""
TMDB 트레일러 키 수집 스크립트.

42,917편 영화의 YouTube 트레일러 키를 TMDB API에서 수집하여 DB에 저장.

사용법:
  cd backend
  python scripts/collect_trailers.py [--limit N] [--dry-run] [--batch-size 1000]

환경변수:
  DATABASE_URL  (필수)
  TMDB_API_KEY  (필수, TMDB v4 Bearer Token)
"""
import argparse
import logging
import os
import sys
import time

import httpx
from sqlalchemy import create_engine, text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

TMDB_VIDEOS_URL = "https://api.themoviedb.org/3/movie/{movie_id}/videos"
REQUEST_INTERVAL = 0.05  # 20 req/sec (TMDB allows ~40)


def get_trailer_key(client: httpx.Client, movie_id: int, api_key: str) -> str | None:
    """Fetch the best YouTube trailer key for a movie from TMDB."""
    url = TMDB_VIDEOS_URL.format(movie_id=movie_id)
    try:
        resp = client.get(
            url,
            params={"language": "ko-KR", "include_video_language": "ko,en"},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("TMDB API error for movie %d: %s", movie_id, e)
        return None

    data = resp.json()
    videos = data.get("results", [])

    # Filter: YouTube trailers only
    trailers = [
        v for v in videos
        if v.get("type") == "Trailer" and v.get("site") == "YouTube" and v.get("key")
    ]
    if not trailers:
        return None

    # Priority: official > non-official
    official = [v for v in trailers if v.get("official")]
    pool = official if official else trailers

    # Priority: Korean > English
    ko = [v for v in pool if v.get("iso_639_1") == "ko"]
    if ko:
        pool = ko

    # Pick most recent by published_at
    pool.sort(key=lambda v: v.get("published_at", ""), reverse=True)
    return pool[0]["key"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect TMDB trailer keys")
    parser.add_argument("--limit", type=int, default=0, help="Process only N movies (0=all)")
    parser.add_argument("--dry-run", action="store_true", help="API calls only, no DB writes")
    parser.add_argument("--batch-size", type=int, default=1000, help="DB commit batch size")
    args = parser.parse_args()

    database_url = os.environ.get("DATABASE_URL")
    tmdb_api_key = os.environ.get("TMDB_API_KEY")

    if not database_url:
        logger.error("DATABASE_URL environment variable is required")
        sys.exit(1)
    if not tmdb_api_key:
        logger.error("TMDB_API_KEY environment variable is required")
        sys.exit(1)

    engine = create_engine(database_url)

    # Get movies without trailer_key
    with engine.connect() as conn:
        query = "SELECT id FROM movies WHERE trailer_key IS NULL ORDER BY popularity DESC"
        if args.limit > 0:
            query += f" LIMIT {args.limit}"
        rows = conn.execute(text(query)).fetchall()

    movie_ids = [row[0] for row in rows]
    total = len(movie_ids)
    logger.info("Movies to process: %d (dry_run=%s)", total, args.dry_run)

    if total == 0:
        logger.info("No movies to process. Done.")
        return

    found = 0
    not_found = 0
    errors = 0
    batch_updates: list[tuple[str, int]] = []  # (key, movie_id)

    with httpx.Client() as client:
        for i, movie_id in enumerate(movie_ids):
            key = get_trailer_key(client, movie_id, tmdb_api_key)

            if key:
                found += 1
                batch_updates.append((key, movie_id))
            else:
                not_found += 1

            # Batch commit
            if len(batch_updates) >= args.batch_size:
                if not args.dry_run:
                    _flush_batch(engine, batch_updates)
                batch_updates.clear()

            # Progress log every 1000 items
            processed = i + 1
            if processed % 1000 == 0 or processed == total:
                logger.info(
                    "Progress: %d/%d (%.1f%%) — found=%d, not_found=%d, errors=%d",
                    processed, total, processed / total * 100,
                    found, not_found, errors,
                )

            time.sleep(REQUEST_INTERVAL)

    # Flush remaining
    if batch_updates and not args.dry_run:
        _flush_batch(engine, batch_updates)

    logger.info(
        "Done. total=%d, found=%d, not_found=%d, errors=%d",
        total, found, not_found, errors,
    )


def _flush_batch(engine, updates: list[tuple[str, int]]) -> None:
    """Bulk update trailer_key for a batch of movies."""
    with engine.begin() as conn:
        for key, movie_id in updates:
            conn.execute(
                text("UPDATE movies SET trailer_key = :key WHERE id = :id"),
                {"key": key, "id": movie_id},
            )
    logger.info("Committed batch of %d updates", len(updates))


if __name__ == "__main__":
    main()
