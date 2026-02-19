"""
MovieLens 25M → RecFlix 매핑 스크립트

MovieLens의 tmdbId와 RecFlix의 Movie.id(=TMDB PK)를 매핑하여
RecFlix에 존재하는 영화의 평점만 추출한다.

실행: cd backend && python scripts/movielens_mapper.py

출력:
  data/movielens/mapped_ratings.csv  - RecFlix 영화와 매핑된 평점
  data/movielens/mapping_stats.json  - 매핑 통계
"""

import json
import logging
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import select

# backend/ 기준 import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.database import SessionLocal
from app.models.movie import Movie

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "movielens"
ML_DIR = DATA_DIR / "ml-25m"


def get_recflix_movie_ids() -> set[int]:
    """RecFlix DB에서 모든 movie.id(=TMDB ID) 조회"""
    db = SessionLocal()
    try:
        result = db.execute(select(Movie.id))
        return {row[0] for row in result.fetchall()}
    finally:
        db.close()


def run_mapping(recflix_ids: set[int]) -> dict:
    """MovieLens tmdbId → RecFlix movie.id 매핑 + 평점 추출"""
    # 1. links.csv: movieId → tmdbId 매핑
    logger.info("  links.csv 로드...")
    links = pd.read_csv(ML_DIR / "links.csv")
    links = links.dropna(subset=["tmdbId"])
    links["tmdbId"] = links["tmdbId"].astype(int)

    # 2. RecFlix에 존재하는 tmdbId만 필터
    mapped_links = links[links["tmdbId"].isin(recflix_ids)].copy()
    ml_to_recflix = dict(
        zip(mapped_links["movieId"], mapped_links["tmdbId"])
    )

    logger.info(
        "  MovieLens %d편 중 %d편 RecFlix 매핑 (%.1f%%)",
        len(links),
        len(mapped_links),
        len(mapped_links) / len(links) * 100,
    )

    # 3. ratings.csv 로드 + 매핑
    logger.info("  ratings.csv 로드 (대용량, 잠시 대기)...")
    ratings = pd.read_csv(ML_DIR / "ratings.csv")
    total_ratings = len(ratings)

    ratings["recflix_movie_id"] = ratings["movieId"].map(ml_to_recflix)
    mapped_ratings = ratings.dropna(subset=["recflix_movie_id"]).copy()
    mapped_ratings["recflix_movie_id"] = mapped_ratings["recflix_movie_id"].astype(int)

    # 4. 통계
    stats = {
        "movielens_total_movies": int(len(links)),
        "recflix_total_movies": len(recflix_ids),
        "mapped_movies": int(len(mapped_links)),
        "mapping_rate_movielens": f"{len(mapped_links) / len(links) * 100:.1f}%",
        "mapping_rate_recflix": f"{len(mapped_links) / len(recflix_ids) * 100:.1f}%",
        "total_ratings": int(total_ratings),
        "mapped_ratings": int(len(mapped_ratings)),
        "mapped_users": int(mapped_ratings["userId"].nunique()),
        "ratings_per_user_avg": f"{len(mapped_ratings) / mapped_ratings['userId'].nunique():.1f}",
    }

    # 5. 저장
    output_path = DATA_DIR / "mapped_ratings.csv"
    mapped_ratings[["userId", "recflix_movie_id", "rating", "timestamp"]].to_csv(
        output_path, index=False
    )
    logger.info("  mapped_ratings.csv 저장: %d행", len(mapped_ratings))

    stats_path = DATA_DIR / "mapping_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    return stats


def main() -> None:
    logger.info("=== MovieLens 25M → RecFlix 매핑 ===\n")

    logger.info("1. RecFlix DB에서 movie ID 조회...")
    recflix_ids = get_recflix_movie_ids()
    logger.info("   RecFlix 영화 %d편\n", len(recflix_ids))

    logger.info("2. MovieLens 매핑 중...")
    stats = run_mapping(recflix_ids)

    logger.info("\n=== 매핑 결과 ===")
    for k, v in stats.items():
        logger.info("  %s: %s", k, v)

    logger.info("\n저장 완료: data/movielens/mapped_ratings.csv")
    logger.info("통계 저장: data/movielens/mapping_stats.json")


if __name__ == "__main__":
    main()
