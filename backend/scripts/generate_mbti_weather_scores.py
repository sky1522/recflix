"""
Generate mbti_scores and weather_scores for movies that don't have them.
Uses genre-based mapping + emotion_tags correlation.

- mbti_scores: 16 MBTI types, each 0.0~1.0
- weather_scores: 4 weather types (sunny/rainy/cloudy/snowy), each 0.0~1.0
- Only processes movies with NULL/empty scores
- Existing scores are preserved

Usage:
  cd backend
  ./venv/Scripts/python.exe scripts/generate_mbti_weather_scores.py
"""
import os
import sys
import json
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import execute_batch


# ============================================================
# MBTI → Genre Preference Mapping
# Each MBTI type has primary (weight 1.0) and secondary (weight 0.6) genres
# ============================================================

MBTI_GENRE_MAP = {
    # Analysts (NT) - intellectual, strategic
    "INTJ": {"primary": ["SF", "스릴러", "미스터리"], "secondary": ["다큐멘터리", "범죄", "드라마"]},
    "INTP": {"primary": ["SF", "미스터리", "다큐멘터리"], "secondary": ["판타지", "스릴러", "애니메이션"]},
    "ENTJ": {"primary": ["액션", "스릴러", "드라마"], "secondary": ["전쟁", "범죄", "SF"]},
    "ENTP": {"primary": ["SF", "코미디", "모험"], "secondary": ["미스터리", "판타지", "액션"]},

    # Diplomats (NF) - idealistic, empathetic
    "INFJ": {"primary": ["드라마", "판타지", "미스터리"], "secondary": ["역사", "SF", "애니메이션"]},
    "INFP": {"primary": ["판타지", "로맨스", "드라마"], "secondary": ["애니메이션", "음악", "모험"]},
    "ENFJ": {"primary": ["드라마", "로맨스", "가족"], "secondary": ["역사", "코미디", "전쟁"]},
    "ENFP": {"primary": ["코미디", "모험", "판타지"], "secondary": ["로맨스", "애니메이션", "음악"]},

    # Sentinels (SJ) - structured, dependable
    "ISTJ": {"primary": ["역사", "스릴러", "전쟁"], "secondary": ["범죄", "드라마", "다큐멘터리"]},
    "ISFJ": {"primary": ["가족", "드라마", "로맨스"], "secondary": ["역사", "애니메이션", "음악"]},
    "ESTJ": {"primary": ["액션", "전쟁", "스릴러"], "secondary": ["범죄", "드라마", "역사"]},
    "ESFJ": {"primary": ["로맨스", "코미디", "가족"], "secondary": ["드라마", "음악", "애니메이션"]},

    # Explorers (SP) - spontaneous, energetic
    "ISTP": {"primary": ["액션", "SF", "스릴러"], "secondary": ["모험", "범죄", "전쟁"]},
    "ISFP": {"primary": ["로맨스", "음악", "드라마"], "secondary": ["애니메이션", "판타지", "가족"]},
    "ESTP": {"primary": ["액션", "코미디", "모험"], "secondary": ["스릴러", "범죄", "SF"]},
    "ESFP": {"primary": ["코미디", "음악", "모험"], "secondary": ["로맨스", "가족", "애니메이션"]},
}

# MBTI → emotion_tags correlation (boost from emotion_tags)
MBTI_EMOTION_BOOST = {
    "INTJ": {"tension": 0.15, "deep": 0.10, "fantasy": 0.10},
    "INTP": {"fantasy": 0.15, "deep": 0.10, "tension": 0.10},
    "ENTJ": {"energy": 0.15, "tension": 0.10, "deep": 0.05},
    "ENTP": {"light": 0.10, "fantasy": 0.10, "energy": 0.10},
    "INFJ": {"deep": 0.15, "fantasy": 0.10, "healing": 0.10},
    "INFP": {"fantasy": 0.15, "romance": 0.10, "healing": 0.10},
    "ENFJ": {"healing": 0.15, "romance": 0.10, "deep": 0.10},
    "ENFP": {"light": 0.15, "fantasy": 0.10, "romance": 0.05},
    "ISTJ": {"tension": 0.10, "deep": 0.15, "energy": 0.05},
    "ISFJ": {"healing": 0.15, "romance": 0.10, "deep": 0.05},
    "ESTJ": {"energy": 0.15, "tension": 0.10, "deep": 0.05},
    "ESFJ": {"romance": 0.10, "light": 0.15, "healing": 0.10},
    "ISTP": {"energy": 0.15, "tension": 0.10, "fantasy": 0.05},
    "ISFP": {"romance": 0.15, "healing": 0.10, "fantasy": 0.05},
    "ESTP": {"energy": 0.15, "light": 0.10, "tension": 0.05},
    "ESFP": {"light": 0.15, "energy": 0.10, "romance": 0.05},
}

# ============================================================
# Weather → Genre/Mood Mapping
# ============================================================

WEATHER_GENRE_MAP = {
    "sunny":  {"primary": ["액션", "모험", "코미디"], "secondary": ["가족", "애니메이션", "음악"]},
    "rainy":  {"primary": ["로맨스", "드라마", "미스터리"], "secondary": ["음악", "범죄", "스릴러"]},
    "cloudy": {"primary": ["스릴러", "미스터리", "드라마"], "secondary": ["SF", "범죄", "다큐멘터리"]},
    "snowy":  {"primary": ["가족", "로맨스", "판타지"], "secondary": ["애니메이션", "코미디", "드라마"]},
}

# Weather → emotion_tags correlation
WEATHER_EMOTION_BOOST = {
    "sunny":  {"energy": 0.20, "light": 0.20, "fantasy": 0.05},
    "rainy":  {"romance": 0.20, "deep": 0.15, "tension": 0.10},
    "cloudy": {"tension": 0.20, "deep": 0.15, "fantasy": 0.05},
    "snowy":  {"healing": 0.25, "romance": 0.15, "light": 0.05},
}

# Weather negative emotion (penalty)
WEATHER_EMOTION_PENALTY = {
    "sunny":  {"tension": -0.10, "deep": -0.05},
    "rainy":  {"energy": -0.10, "light": -0.05},
    "cloudy": {"light": -0.10, "healing": -0.05},
    "snowy":  {"tension": -0.10, "energy": -0.05},
}


def calc_mbti_scores(genres, emotion_tags):
    """Calculate MBTI scores for a movie based on genres + emotion_tags."""
    genres_set = set(genres) if genres else set()
    scores = {}

    for mbti, genre_map in MBTI_GENRE_MAP.items():
        score = 0.0

        # Genre matching
        primary_matches = len(genres_set & set(genre_map["primary"]))
        secondary_matches = len(genres_set & set(genre_map["secondary"]))
        genre_score = (primary_matches * 0.20) + (secondary_matches * 0.10)
        score += min(genre_score, 0.60)

        # Emotion tags boost
        if emotion_tags:
            boosts = MBTI_EMOTION_BOOST.get(mbti, {})
            for emotion_key, boost_val in boosts.items():
                emotion_score = emotion_tags.get(emotion_key, 0.0)
                if isinstance(emotion_score, (int, float)):
                    score += emotion_score * boost_val

        scores[mbti] = round(min(max(score, 0.0), 1.0), 2)

    return scores


def calc_weather_scores(genres, emotion_tags):
    """Calculate weather scores for a movie based on genres + emotion_tags."""
    genres_set = set(genres) if genres else set()
    scores = {}

    for weather, genre_map in WEATHER_GENRE_MAP.items():
        score = 0.0

        # Genre matching
        primary_matches = len(genres_set & set(genre_map["primary"]))
        secondary_matches = len(genres_set & set(genre_map["secondary"]))
        genre_score = (primary_matches * 0.20) + (secondary_matches * 0.10)
        score += min(genre_score, 0.60)

        # Emotion tags boost
        if emotion_tags:
            boosts = WEATHER_EMOTION_BOOST.get(weather, {})
            for emotion_key, boost_val in boosts.items():
                emotion_score = emotion_tags.get(emotion_key, 0.0)
                if isinstance(emotion_score, (int, float)):
                    score += emotion_score * boost_val

            # Emotion penalty
            penalties = WEATHER_EMOTION_PENALTY.get(weather, {})
            for emotion_key, penalty_val in penalties.items():
                emotion_score = emotion_tags.get(emotion_key, 0.0)
                if isinstance(emotion_score, (int, float)):
                    score += emotion_score * penalty_val  # penalty_val is negative

        scores[weather] = round(min(max(score, 0.0), 1.0), 2)

    return scores


def main():
    print("=" * 60)
    print("Generating mbti_scores & weather_scores")
    print("(Genre + emotion_tags based, skipping existing)")
    print("=" * 60)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # Current status
    cur.execute("SELECT COUNT(*) FROM movies")
    total_movies = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM movies WHERE mbti_scores IS NOT NULL AND mbti_scores != '{}'::jsonb")
    has_mbti = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM movies WHERE weather_scores IS NOT NULL AND weather_scores != '{}'::jsonb")
    has_weather = cur.fetchone()[0]

    print(f"\nTotal movies: {total_movies}")
    print(f"Already have mbti_scores: {has_mbti}")
    print(f"Already have weather_scores: {has_weather}")
    print(f"Need mbti_scores: {total_movies - has_mbti}")
    print(f"Need weather_scores: {total_movies - has_weather}")

    # Fetch movies that need scores (NULL or empty for EITHER mbti or weather)
    print("\nFetching movies needing scores...")
    cur.execute("""
        SELECT m.id, m.emotion_tags,
               ARRAY_AGG(DISTINCT g.name) FILTER (WHERE g.name IS NOT NULL) as genres,
               m.mbti_scores, m.weather_scores
        FROM movies m
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE (m.mbti_scores IS NULL OR m.mbti_scores = '{}'::jsonb)
           OR (m.weather_scores IS NULL OR m.weather_scores = '{}'::jsonb)
        GROUP BY m.id, m.emotion_tags, m.mbti_scores, m.weather_scores
    """)

    movies = cur.fetchall()
    print(f"Found {len(movies)} movies to process")

    mbti_updates = []
    weather_updates = []
    processed = 0

    for movie_id, emotion_tags, genres, existing_mbti, existing_weather in movies:
        et = emotion_tags if isinstance(emotion_tags, dict) else {}

        # Only generate if missing
        need_mbti = not existing_mbti or existing_mbti == {}
        need_weather = not existing_weather or existing_weather == {}

        if need_mbti:
            mbti = calc_mbti_scores(genres or [], et)
            mbti_updates.append((json.dumps(mbti), movie_id))

        if need_weather:
            weather = calc_weather_scores(genres or [], et)
            weather_updates.append((json.dumps(weather), movie_id))

        processed += 1
        if processed % 5000 == 0:
            print(f"  Processed {processed}/{len(movies)}...")

    print(f"\nProcessed {processed} movies")
    print(f"  mbti_scores to update: {len(mbti_updates)}")
    print(f"  weather_scores to update: {len(weather_updates)}")

    # Batch update
    if mbti_updates:
        print("\nUpdating mbti_scores...")
        execute_batch(
            cur,
            "UPDATE movies SET mbti_scores = %s::jsonb WHERE id = %s",
            mbti_updates,
            page_size=1000
        )
        print(f"  Updated {len(mbti_updates)} movies")

    if weather_updates:
        print("Updating weather_scores...")
        execute_batch(
            cur,
            "UPDATE movies SET weather_scores = %s::jsonb WHERE id = %s",
            weather_updates,
            page_size=1000
        )
        print(f"  Updated {len(weather_updates)} movies")

    conn.commit()

    # ── Verification ──
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)

    cur.execute("SELECT COUNT(*) FROM movies")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM movies WHERE mbti_scores IS NOT NULL AND mbti_scores != '{}'::jsonb")
    final_mbti = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM movies WHERE weather_scores IS NOT NULL AND weather_scores != '{}'::jsonb")
    final_weather = cur.fetchone()[0]

    print(f"\nTotal movies: {total}")
    print(f"mbti_scores:   {final_mbti}/{total} ({final_mbti*100/total:.1f}%)")
    print(f"weather_scores: {final_weather}/{total} ({final_weather*100/total:.1f}%)")

    # Sample movies
    print("\n--- Sample: The Shawshank Redemption ---")
    cur.execute("SELECT mbti_scores, weather_scores FROM movies WHERE id = 278")
    row = cur.fetchone()
    if row:
        print(f"  mbti:    {row[0]}")
        print(f"  weather: {row[1]}")

    print("\n--- Sample: Spirited Away ---")
    cur.execute("SELECT mbti_scores, weather_scores FROM movies WHERE id = 129")
    row = cur.fetchone()
    if row:
        print(f"  mbti:    {row[0]}")
        print(f"  weather: {row[1]}")

    # MBTI score distribution
    print("\n--- MBTI Score Distribution (avg across all movies) ---")
    for mbti in ["INTJ", "INFP", "ESTP", "ESFJ"]:
        cur.execute(f"""
            SELECT AVG((mbti_scores->>'{mbti}')::float)
            FROM movies WHERE mbti_scores IS NOT NULL AND mbti_scores != '{{}}'::jsonb
        """)
        avg = cur.fetchone()[0]
        print(f"  {mbti}: avg={avg:.3f}" if avg else f"  {mbti}: N/A")

    # Weather score distribution
    print("\n--- Weather Score Distribution (avg) ---")
    for w in ["sunny", "rainy", "cloudy", "snowy"]:
        cur.execute(f"""
            SELECT AVG((weather_scores->>'{w}')::float)
            FROM movies WHERE weather_scores IS NOT NULL AND weather_scores != '{{}}'::jsonb
        """)
        avg = cur.fetchone()[0]
        print(f"  {w}: avg={avg:.3f}" if avg else f"  {w}: N/A")

    cur.close()
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
