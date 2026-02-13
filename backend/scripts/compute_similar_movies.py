#!/usr/bin/env python3
"""
RecFlix 자체 유사 영화 계산 스크립트

유사도 = (0.5 × emotion_tags 코사인 유사도) + (0.3 × mbti_scores 코사인 유사도) + (0.2 × 장르 Jaccard 유사도)
효율화: 같은 장르가 1개 이상 겹치는 영화 쌍만 비교
결과: similar_movies 테이블에 영화별 Top 10 저장

Usage:
    python compute_similar_movies.py --dry-run     # 유명 영화 5편만 미리보기
    python compute_similar_movies.py               # 전체 계산 + DB 업데이트
"""

import argparse
import sys
import time
import numpy as np
from collections import defaultdict
from sqlalchemy import create_engine, text

# Windows 콘솔 UTF-8 출력
sys.stdout.reconfigure(encoding="utf-8")

DATABASE_URL = "postgresql://recflix:recflix123@localhost:5432/recflix"

EMOTION_KEYS = ["healing", "tension", "energy", "romance", "deep", "fantasy", "light"]
MBTI_KEYS = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP",
]

TOP_K = 10
MIN_WEIGHTED_SCORE = 6.0  # 유사 영화 후보 품질 필터
LLM_BONUS = 0.05          # LLM 분석 영화 우대 보너스

SAMPLE_MOVIES = {
    278: "쇼생크 탈출",
    157336: "인터스텔라",
    550: "파이트 클럽",
    238: "대부",
    27205: "인셉션",
}


def load_movies(engine):
    """DB에서 전체 영화의 emotion_tags, mbti_scores, 장르 로드"""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT id, title_ko, title, emotion_tags, mbti_scores, weighted_score
            FROM movies
            WHERE emotion_tags IS NOT NULL
              AND mbti_scores IS NOT NULL
              AND emotion_tags != '{}'::jsonb
              AND mbti_scores != '{}'::jsonb
        """)).fetchall()

        genre_rows = conn.execute(text("""
            SELECT mg.movie_id, g.name
            FROM movie_genres mg
            JOIN genres g ON g.id = mg.genre_id
        """)).fetchall()

    movie_genres = defaultdict(set)
    for mid, gname in genre_rows:
        movie_genres[mid].add(gname)

    movies = {}
    for row in rows:
        mid = row[0]
        genres = movie_genres.get(mid, set())
        if not genres:
            continue
        et = row[3] or {}
        is_llm = any(v > 0.7 for v in et.values())
        movies[mid] = {
            "title_ko": row[1] or row[2],
            "emotion_tags": et,
            "mbti_scores": row[4] or {},
            "genres": genres,
            "weighted_score": row[5] or 0.0,
            "is_llm": is_llm,
        }
    return movies


def build_vectors(movies):
    """emotion/mbti 벡터 행렬 생성 및 L2 정규화"""
    movie_ids = sorted(movies.keys())
    n = len(movie_ids)
    id_to_idx = {mid: i for i, mid in enumerate(movie_ids)}

    emotion_mat = np.zeros((n, len(EMOTION_KEYS)), dtype=np.float32)
    mbti_mat = np.zeros((n, len(MBTI_KEYS)), dtype=np.float32)

    for mid, data in movies.items():
        idx = id_to_idx[mid]
        for j, key in enumerate(EMOTION_KEYS):
            emotion_mat[idx, j] = data["emotion_tags"].get(key, 0.0)
        for j, key in enumerate(MBTI_KEYS):
            mbti_mat[idx, j] = data["mbti_scores"].get(key, 0.0)

    # L2 normalize (cosine sim = dot product of unit vectors)
    def normalize(mat):
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return mat / norms

    return movie_ids, id_to_idx, normalize(emotion_mat), normalize(mbti_mat)


def build_genre_index(movies):
    """장르 → 영화 ID set 인덱스"""
    genre_to_movies = defaultdict(set)
    for mid, data in movies.items():
        for g in data["genres"]:
            genre_to_movies[g].add(mid)
    return genre_to_movies


def compute_similar(movies, movie_ids, id_to_idx, emotion_norm, mbti_norm,
                    genre_index, target_ids=None):
    """영화별 Top-K 유사 영화 계산 (장르 겹침 필터링)"""
    results = {}
    targets = target_ids if target_ids else movie_ids
    total = len(targets)

    for progress, mid in enumerate(targets):
        if mid not in id_to_idx:
            continue

        idx = id_to_idx[mid]
        genres_a = movies[mid]["genres"]

        # 후보: 장르 1개 이상 겹치는 + weighted_score >= 6.0인 영화만
        candidates = set()
        for g in genres_a:
            candidates.update(genre_index[g])
        candidates.discard(mid)
        candidates = {c for c in candidates
                      if movies[c]["weighted_score"] >= MIN_WEIGHTED_SCORE}

        if not candidates:
            continue

        cand_ids = np.array([c for c in candidates if c in id_to_idx])
        if len(cand_ids) == 0:
            continue
        cand_indices = np.array([id_to_idx[c] for c in cand_ids])

        # 코사인 유사도 (정규화된 벡터의 내적)
        emotion_sim = emotion_norm[idx] @ emotion_norm[cand_indices].T
        mbti_sim = mbti_norm[idx] @ mbti_norm[cand_indices].T

        # 장르 Jaccard 유사도
        genre_sims = np.array([
            len(genres_a & movies[c]["genres"]) / len(genres_a | movies[c]["genres"])
            for c in cand_ids
        ], dtype=np.float32)

        # LLM 분석 영화 보너스
        llm_bonus = np.array([
            LLM_BONUS if movies[c]["is_llm"] else 0.0
            for c in cand_ids
        ], dtype=np.float32)

        # 종합 유사도
        scores = 0.5 * emotion_sim + 0.3 * mbti_sim + 0.2 * genre_sims + llm_bonus

        # Top K 추출
        if len(scores) <= TOP_K:
            top_idx = np.argsort(scores)[::-1]
        else:
            top_idx = np.argpartition(scores, -TOP_K)[-TOP_K:]
            top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

        results[mid] = [(int(cand_ids[i]), float(scores[i])) for i in top_idx]

        if (progress + 1) % 5000 == 0 or (progress + 1) == total:
            print(f"  진행: {progress + 1:,}/{total:,} ({(progress+1)/total*100:.1f}%)")

    return results


def update_db(engine, results):
    """similar_movies 테이블 갱신"""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM similar_movies"))
        print("  기존 similar_movies 테이블 초기화 완료")

        batch = []
        count = 0
        for mid, similar_list in results.items():
            for sid, _ in similar_list:
                batch.append({"mid": mid, "sid": sid})
                if len(batch) >= 5000:
                    conn.execute(text(
                        "INSERT INTO similar_movies (movie_id, similar_movie_id) "
                        "VALUES (:mid, :sid) ON CONFLICT DO NOTHING"
                    ), batch)
                    count += len(batch)
                    batch = []
        if batch:
            conn.execute(text(
                "INSERT INTO similar_movies (movie_id, similar_movie_id) "
                "VALUES (:mid, :sid) ON CONFLICT DO NOTHING"
            ), batch)
            count += len(batch)

        print(f"  {len(results):,}편 x Top {TOP_K} = {count:,}개 유사 관계 저장 완료")


def print_results(movies, results, sample_ids):
    """샘플 영화의 유사 영화 결과 출력"""
    for mid in sample_ids:
        if mid not in results:
            print(f"\n  ID {mid}: 데이터 없음")
            continue
        title = movies[mid]["title_ko"]
        genres = ", ".join(sorted(movies[mid]["genres"]))
        print(f"\n{'='*70}")
        print(f"  {title} (ID: {mid})")
        print(f"  장르: {genres}")
        et = movies[mid]["emotion_tags"]
        top_emotions = sorted(et.items(), key=lambda x: -x[1])[:3]
        print(f"  감성: {', '.join(f'{k}={v:.2f}' for k,v in top_emotions)}")
        print(f"  {'순위':<4} {'유사도':<8} {'WS':<5} {'LLM':<4} {'제목':<26} {'장르':<22} {'주요 감성'}")
        print(f"  {'-'*74}")
        for rank, (sid, score) in enumerate(results[mid], 1):
            s_title = movies[sid]["title_ko"]
            if len(s_title) > 24:
                s_title = s_title[:23] + ".."
            s_genres = ", ".join(sorted(movies[sid]["genres"]))
            if len(s_genres) > 20:
                s_genres = s_genres[:19] + ".."
            s_et = movies[sid]["emotion_tags"]
            s_top = sorted(s_et.items(), key=lambda x: -x[1])[:2]
            s_emo = ", ".join(f"{k}={v:.2f}" for k, v in s_top)
            ws = movies[sid]["weighted_score"]
            llm = "O" if movies[sid]["is_llm"] else ""
            print(f"  {rank:<4} {score:.4f}   {ws:<5.1f} {llm:<4} {s_title:<26} {s_genres:<22} {s_emo}")


def main():
    parser = argparse.ArgumentParser(description="RecFlix 유사 영화 계산")
    parser.add_argument("--dry-run", action="store_true",
                        help="유명 영화 5편만 미리보기 (DB 변경 없음)")
    args = parser.parse_args()

    print("RecFlix 유사 영화 계산 스크립트")
    print("=" * 40)
    print(f"유사도 = 0.5*emotion + 0.3*mbti + 0.2*genre + LLM보너스({LLM_BONUS})")
    print(f"Top-K = {TOP_K}, 장르겹침 + 품질필터(ws>={MIN_WEIGHTED_SCORE})")

    engine = create_engine(DATABASE_URL)

    # 1. 데이터 로드
    print(f"\n[1/4] 영화 데이터 로드 중...")
    t0 = time.time()
    movies = load_movies(engine)
    quality_count = sum(1 for m in movies.values() if m["weighted_score"] >= MIN_WEIGHTED_SCORE)
    llm_count = sum(1 for m in movies.values() if m["is_llm"])
    print(f"  {len(movies):,}편 로드 완료 ({time.time()-t0:.1f}초)")
    print(f"  품질 필터(ws>={MIN_WEIGHTED_SCORE}) 통과: {quality_count:,}편, LLM 분석: {llm_count:,}편")

    # 2. 벡터 생성
    print(f"\n[2/4] 벡터 생성 중...")
    t0 = time.time()
    movie_ids, id_to_idx, emotion_norm, mbti_norm = build_vectors(movies)
    genre_index = build_genre_index(movies)
    print(f"  emotion {emotion_norm.shape}, mbti {mbti_norm.shape} ({time.time()-t0:.1f}초)")
    avg_per_genre = np.mean([len(v) for v in genre_index.values()])
    print(f"  장르 {len(genre_index)}개, 장르별 평균 {avg_per_genre:.0f}편")

    # 3. 유사도 계산
    if args.dry_run:
        print(f"\n[3/4] Dry-run: 샘플 {len(SAMPLE_MOVIES)}편 계산 중...")
        target_ids = [mid for mid in SAMPLE_MOVIES if mid in id_to_idx]
        missing = [f"{v}(ID:{k})" for k, v in SAMPLE_MOVIES.items() if k not in id_to_idx]
        if missing:
            print(f"  DB에 없는 영화: {', '.join(missing)}")
        t0 = time.time()
        results = compute_similar(
            movies, movie_ids, id_to_idx, emotion_norm, mbti_norm,
            genre_index, target_ids
        )
        print(f"  계산 완료 ({time.time()-t0:.1f}초)")
        print_results(movies, results, target_ids)
        print(f"\n[Dry-run 완료] 전체 적용: --dry-run 제거 후 실행")
    else:
        print(f"\n[3/4] 전체 {len(movie_ids):,}편 유사도 계산 중...")
        t0 = time.time()
        results = compute_similar(
            movies, movie_ids, id_to_idx, emotion_norm, mbti_norm, genre_index
        )
        elapsed = time.time() - t0
        print(f"  계산 완료 ({elapsed:.1f}초)")

        # 4. DB 업데이트
        print(f"\n[4/4] similar_movies 테이블 업데이트 중...")
        t0 = time.time()
        update_db(engine, results)
        print(f"  DB 업데이트 완료 ({time.time()-t0:.1f}초)")

        # 샘플 출력
        sample_ids = [mid for mid in SAMPLE_MOVIES if mid in results]
        if sample_ids:
            print(f"\n--- 샘플 결과 ---")
            print_results(movies, results, sample_ids)

        print(f"\n전체 유사 영화 계산 + DB 저장 완료!")


if __name__ == "__main__":
    main()
