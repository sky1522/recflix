"""
42,917편 영화 임베딩 생성 스크립트.
Voyage AI voyage-multilingual-2 모델 사용 (1,024차원).

사용법:
  cd backend
  python scripts/generate_embeddings.py [--batch-size 100] [--resume]

출력:
  data/embeddings/movie_embeddings.npy    (N, 1024) float32
  data/embeddings/movie_id_index.json     {"0": movie_id, ...}
  data/embeddings/embedding_metadata.json  메타 정보
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import httpx
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
VOYAGE_MODEL = "voyage-multilingual-2"
EMBEDDING_DIM = 1024
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "embeddings"
PROGRESS_FILE = OUTPUT_DIR / "progress.json"

EMOTION_LABELS = {
    "healing": "힐링/치유",
    "tension": "긴장/스릴",
    "energy": "활기/에너지",
    "romance": "로맨스/감성",
    "deep": "깊은/철학적",
    "fantasy": "판타지/상상",
    "light": "가벼운/유쾌",
}
WEATHER_LABELS = {
    "sunny": "맑은 날",
    "rainy": "비 오는 날",
    "cloudy": "흐린 날",
    "snowy": "눈 오는 날",
}


def build_embedding_text(movie: dict) -> str:
    """영화 1편의 임베딩용 텍스트 생성."""
    parts: list[str] = []

    # 1. 제목
    title_ko = movie.get("title_ko") or movie.get("title") or ""
    parts.append(f"제목: {title_ko}")
    title_en = movie.get("title") or ""
    if title_en and title_en != title_ko:
        parts.append(f"영어 제목: {title_en}")

    # 2. 장르
    if movie.get("genres"):
        parts.append(f"장르: {movie['genres']}")

    # 3. 줄거리 (최대 500자)
    if movie.get("overview"):
        parts.append(f"줄거리: {movie['overview'][:500]}")

    # 4. 감성 태그 (>= 0.5만)
    if movie.get("emotion_tags"):
        tags = movie["emotion_tags"]
        if isinstance(tags, str):
            tags = json.loads(tags)
        high = [
            EMOTION_LABELS[k]
            for k, v in tags.items()
            if k in EMOTION_LABELS and isinstance(v, (int, float)) and v >= 0.5
        ]
        if high:
            parts.append(f"분위기: {', '.join(high)}")

    # 5. 날씨 적합도 (>= 0.3만)
    if movie.get("weather_scores"):
        ws = movie["weather_scores"]
        if isinstance(ws, str):
            ws = json.loads(ws)
        high_w = [
            WEATHER_LABELS[k]
            for k, v in ws.items()
            if k in WEATHER_LABELS and isinstance(v, (int, float)) and v >= 0.3
        ]
        if high_w:
            parts.append(f"어울리는 날씨: {', '.join(high_w)}")

    # 6. MBTI 상위 3개 (>= 0.2)
    if movie.get("mbti_scores"):
        ms = movie["mbti_scores"]
        if isinstance(ms, str):
            ms = json.loads(ms)
        sorted_mbti = sorted(
            ms.items(),
            key=lambda x: float(x[1]) if x[1] else 0,
            reverse=True,
        )[:3]
        high_mbti = [k for k, v in sorted_mbti if float(v) >= 0.2]
        if high_mbti:
            parts.append(f"MBTI 추천: {', '.join(high_mbti)}")

    # 7. 키워드
    if movie.get("keywords"):
        parts.append(f"키워드: {movie['keywords']}")

    # 8. 감독
    if movie.get("director_ko"):
        parts.append(f"감독: {movie['director_ko']}")

    return "\n".join(parts)


def embed_batch(texts: list[str], api_key: str) -> list[list[float]]:
    """Voyage AI API로 배치 임베딩 (최대 128개)."""
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            VOYAGE_API_URL,
            json={
                "input": texts,
                "model": VOYAGE_MODEL,
                "input_type": "document",
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return [item["embedding"] for item in data["data"]]


def _save_progress(
    completed: int,
    embeddings: list[list[float]],
    total: int,
) -> None:
    """중간 진행 저장 (원자적 쓰기)."""
    progress_tmp = OUTPUT_DIR / "progress.tmp.json"
    with open(progress_tmp, "w") as f:
        json.dump({"completed": completed}, f)
    progress_tmp.replace(PROGRESS_FILE)

    if embeddings:
        partial = np.array(embeddings, dtype=np.float32)
        partial_tmp = OUTPUT_DIR / "movie_embeddings_partial.tmp.npy"
        np.save(str(partial_tmp), partial)
        partial_tmp.replace(OUTPUT_DIR / "movie_embeddings_partial.npy")

    logger.info("진행 저장: %d/%d", completed, total)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate movie embeddings via Voyage AI")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--resume", action="store_true", help="이전 진행 이어서")
    args = parser.parse_args()

    # .env 파일 로드 (dotenv 가용 시)
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        load_dotenv(env_path)
    except ImportError:
        pass

    api_key = os.environ.get("VOYAGE_API_KEY", "")
    if not api_key:
        logger.error("VOYAGE_API_KEY 환경변수 필요")
        sys.exit(1)

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://recflix:recflix123@localhost:5432/recflix",
    )
    engine = create_engine(db_url)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 영화 데이터 로드
    logger.info("DB에서 영화 데이터 로드 중...")
    with Session(engine) as session:
        rows = session.execute(
            text("""
                SELECT m.id, m.title, m.title_ko, m.overview, m.director_ko,
                       m.emotion_tags::text, m.weather_scores::text, m.mbti_scores::text,
                       (SELECT string_agg(g.name, ', ')
                        FROM movie_genres mg JOIN genres g ON g.id = mg.genre_id
                        WHERE mg.movie_id = m.id) as genres,
                       (SELECT string_agg(k.name, ', ')
                        FROM movie_keywords mk JOIN keywords k ON k.id = mk.keyword_id
                        WHERE mk.movie_id = m.id) as keywords
                FROM movies m
                ORDER BY m.id
            """)
        ).fetchall()

    columns = [
        "id", "title", "title_ko", "overview", "director_ko",
        "emotion_tags", "weather_scores", "mbti_scores", "genres", "keywords",
    ]
    movies = [dict(zip(columns, row, strict=False)) for row in rows]

    # JSONB 문자열 파싱
    for m in movies:
        for field in ("emotion_tags", "weather_scores", "mbti_scores"):
            if m[field] and isinstance(m[field], str):
                try:
                    m[field] = json.loads(m[field])
                except json.JSONDecodeError:
                    m[field] = {}

    total = len(movies)
    logger.info("총 %d편 영화 로드 완료", total)

    # 진행 상태 로드 (resume 모드)
    start_idx = 0
    all_embeddings: list[list[float]] = []

    if args.resume and PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
        start_idx = progress.get("completed", 0)

        partial_path = OUTPUT_DIR / "movie_embeddings_partial.npy"
        if partial_path.exists():
            all_embeddings = np.load(str(partial_path)).tolist()

        logger.info("이전 진행에서 재개: %d/%d", start_idx, total)
    else:
        logger.info("처음부터 시작 (batch_size=%d)", args.batch_size)

    # 배치 임베딩 생성
    batch_size = args.batch_size
    t_start = time.time()

    for i in range(start_idx, total, batch_size):
        batch = movies[i : i + batch_size]
        texts = [build_embedding_text(m) for m in batch]

        try:
            embeddings = embed_batch(texts, api_key)
            all_embeddings.extend(embeddings)
        except httpx.HTTPStatusError as e:
            logger.error(
                "배치 %d HTTP 에러 %d: %s",
                i, e.response.status_code, e.response.text[:200],
            )
            _save_progress(i, all_embeddings, total)
            sys.exit(1)
        except Exception as e:
            logger.error("배치 %d 실패: %s", i, e)
            _save_progress(i, all_embeddings, total)
            sys.exit(1)

        done = i + len(batch)
        elapsed = time.time() - t_start
        eta = (elapsed / (done - start_idx)) * (total - done) if done > start_idx else 0
        logger.info(
            "[%d/%d] %.1f%% | %.0fs elapsed | ETA %.0fs",
            done, total, done / total * 100, elapsed, eta,
        )

        # 1000개마다 중간 저장
        if done % 1000 == 0:
            _save_progress(done, all_embeddings, total)

        # Rate limit: Voyage AI 300 RPM
        time.sleep(0.25)

    # 최종 저장
    embeddings_array = np.array(all_embeddings, dtype=np.float32)
    np.save(str(OUTPUT_DIR / "movie_embeddings.npy"), embeddings_array)

    movie_id_index = {str(i): movies[i]["id"] for i in range(len(movies))}
    with open(OUTPUT_DIR / "movie_id_index.json", "w") as f:
        json.dump(movie_id_index, f)

    metadata = {
        "model": VOYAGE_MODEL,
        "dims": EMBEDDING_DIM,
        "count": len(movies),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "file_size_mb": round(embeddings_array.nbytes / 1024 / 1024, 1),
    }
    with open(OUTPUT_DIR / "embedding_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # 임시 파일 정리
    for tmp in (PROGRESS_FILE, OUTPUT_DIR / "movie_embeddings_partial.npy"):
        if tmp.exists():
            tmp.unlink()

    logger.info(
        "완료! %d편, %d차원, %.1f MB",
        embeddings_array.shape[0],
        embeddings_array.shape[1],
        embeddings_array.nbytes / 1024 / 1024,
    )


if __name__ == "__main__":
    main()
