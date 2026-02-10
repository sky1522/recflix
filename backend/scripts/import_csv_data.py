"""
Step 2: Import new CSV data into movies DB
- Backs up LLM emotion_tags before deletion
- Clears all movie-related data
- Imports 42,917 movies from MOVIE_total_FINAL_FINAL_2010.csv
- Restores emotion_tags for overlapping movies
- Rebuilds all relationships (genres, cast, keywords, countries, similar)

Usage:
  cd backend
  ./venv/Scripts/python.exe scripts/import_csv_data.py
"""
import csv
import sys
import os
import io
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy import text
from app.database import engine

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "raw", "MOVIE_total_FINAL_FINAL_2010.csv"
)

BATCH_SIZE = 1000


def parse_float(val, default=0.0):
    if not val or val.strip() == '':
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def parse_int(val, default=0):
    if not val or val.strip() == '':
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def parse_bool(val):
    if not val:
        return False
    return val.strip().upper() == 'TRUE'


def parse_date(val):
    if not val or val.strip() == '':
        return None
    try:
        return datetime.strptime(val.strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def parse_list(val):
    """Parse comma-separated string into list of stripped, non-empty strings."""
    if not val or val.strip() == '':
        return []
    return [item.strip() for item in val.split(',') if item.strip()]


def run_import():
    print("=" * 60)
    print("Step 2: Import CSV Data into Movies DB")
    print("=" * 60)

    # ── 1. Read CSV ──
    print("\n[1/7] Reading CSV file...")
    rows = []
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    print(f"  CSV rows: {len(rows)}")

    with engine.connect() as conn:
        # ── 2. Backup emotion_tags ──
        print("\n[2/7] Backing up LLM emotion_tags...")
        result = conn.execute(text("""
            SELECT id, emotion_tags FROM movies
            WHERE emotion_tags IS NOT NULL AND emotion_tags != '{}'::jsonb
        """))
        emotion_backup = {}
        for row in result:
            movie_id, tags = row
            if tags:
                emotion_backup[movie_id] = tags
        print(f"  Backed up emotion_tags for {len(emotion_backup)} movies")

        # Also backup mbti_scores and weather_scores
        print("  Backing up mbti_scores and weather_scores...")
        result = conn.execute(text("""
            SELECT id, mbti_scores, weather_scores FROM movies
            WHERE (mbti_scores IS NOT NULL AND mbti_scores != '{}'::jsonb)
               OR (weather_scores IS NOT NULL AND weather_scores != '{}'::jsonb)
        """))
        mbti_backup = {}
        weather_backup = {}
        for row in result:
            mid, mbti, weather = row
            if mbti:
                mbti_backup[mid] = mbti
            if weather:
                weather_backup[mid] = weather
        print(f"  Backed up mbti_scores for {len(mbti_backup)} movies")
        print(f"  Backed up weather_scores for {len(weather_backup)} movies")

        # ── 3. Clear existing data ──
        print("\n[3/7] Clearing existing data...")
        conn.execute(text("DELETE FROM similar_movies"))
        print("  Cleared similar_movies")
        conn.execute(text("DELETE FROM movie_keywords"))
        print("  Cleared movie_keywords")
        conn.execute(text("DELETE FROM movie_countries"))
        print("  Cleared movie_countries")
        conn.execute(text("DELETE FROM movie_cast"))
        print("  Cleared movie_cast")
        conn.execute(text("DELETE FROM movie_genres"))
        print("  Cleared movie_genres")
        conn.execute(text("DELETE FROM movies"))
        print("  Cleared movies")
        conn.execute(text("DELETE FROM persons"))
        print("  Cleared persons")
        conn.execute(text("DELETE FROM keywords"))
        print("  Cleared keywords")
        conn.execute(text("DELETE FROM countries"))
        print("  Cleared countries")
        # Keep genres table (predefined 19 genres)
        conn.commit()

        # ── 4. Build lookup tables ──
        print("\n[4/7] Building lookup tables...")

        # Genre lookup (existing)
        result = conn.execute(text("SELECT id, name FROM genres"))
        genre_map = {row[1]: row[0] for row in result}
        print(f"  Genres in DB: {len(genre_map)}")

        # Check if any CSV genres are missing from DB
        csv_genres = set()
        for row in rows:
            for g in parse_list(row.get('genres', '')):
                csv_genres.add(g)
        missing_genres = csv_genres - set(genre_map.keys())
        if missing_genres:
            print(f"  Adding missing genres: {missing_genres}")
            for g in missing_genres:
                conn.execute(text("INSERT INTO genres (name, name_ko) VALUES (:name, :name_ko)"),
                             {"name": g, "name_ko": g})
            conn.commit()
            result = conn.execute(text("SELECT id, name FROM genres"))
            genre_map = {row[1]: row[0] for row in result}

        # Collect all unique persons (cast + directors)
        print("  Collecting unique persons...")
        all_persons = set()
        for row in rows:
            for name in parse_list(row.get('cast', '')):
                all_persons.add(name)
            director = row.get('director', '').strip()
            if director:
                all_persons.add(director)
        print(f"  Unique persons: {len(all_persons)}")

        # Bulk insert persons
        print("  Inserting persons...")
        person_list = sorted(all_persons)
        for i in range(0, len(person_list), BATCH_SIZE):
            batch = person_list[i:i+BATCH_SIZE]
            values = ", ".join(
                conn.execute(text("SELECT format('(%L)', :name)"), {"name": n}).scalar()
                for n in batch
            )
            # Use a simpler approach: individual parameterized inserts in batch
            for name in batch:
                conn.execute(text("INSERT INTO persons (name) VALUES (:name)"), {"name": name})
            if (i // BATCH_SIZE) % 10 == 0:
                print(f"    {i + len(batch)}/{len(person_list)} persons...")
        conn.commit()

        result = conn.execute(text("SELECT id, name FROM persons"))
        person_map = {row[1]: row[0] for row in result}
        print(f"  Persons in DB: {len(person_map)}")

        # Collect all unique keywords
        print("  Collecting unique keywords...")
        all_keywords = set()
        for row in rows:
            for kw in parse_list(row.get('keywords', '')):
                all_keywords.add(kw)
        print(f"  Unique keywords: {len(all_keywords)}")

        print("  Inserting keywords...")
        kw_list = sorted(all_keywords)
        for name in kw_list:
            conn.execute(text("INSERT INTO keywords (name) VALUES (:name)"), {"name": name})
        conn.commit()

        result = conn.execute(text("SELECT id, name FROM keywords"))
        keyword_map = {row[1]: row[0] for row in result}
        print(f"  Keywords in DB: {len(keyword_map)}")

        # Collect all unique countries
        print("  Collecting unique countries...")
        all_countries = set()
        for row in rows:
            for c in parse_list(row.get('production_countries', '')):
                all_countries.add(c)
        print(f"  Unique countries: {len(all_countries)}")

        for name in sorted(all_countries):
            conn.execute(text("INSERT INTO countries (name) VALUES (:name)"), {"name": name})
        conn.commit()

        result = conn.execute(text("SELECT id, name FROM countries"))
        country_map = {row[1]: row[0] for row in result}
        print(f"  Countries in DB: {len(country_map)}")

        # ── 5. Insert movies ──
        print("\n[5/7] Inserting movies...")
        movie_ids_set = set()

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i+BATCH_SIZE]
            for row in batch:
                movie_id = int(row['id'])
                movie_ids_set.add(movie_id)

                # CSV title = Korean, CSV title_ko_en = English/original
                title_en = row.get('title_ko_en', '').strip() or row.get('title', '').strip()
                title_ko = row.get('title', '').strip()

                overview = row.get('overview', '').strip() or None
                director = row.get('director', '').strip() or None
                director_ko = row.get('director_ko', '').strip() or None
                cast_ko = row.get('cast_ko', '').strip() or None
                countries_ko = row.get('production_countries_ko', '').strip() or None
                release_season = row.get('release_season', '').strip() or None

                # Restore backed-up scores
                emotion = emotion_backup.get(movie_id)
                mbti = mbti_backup.get(movie_id)
                weather = weather_backup.get(movie_id)

                conn.execute(text("""
                    INSERT INTO movies (
                        id, title, title_ko, certification, runtime,
                        vote_average, vote_count, overview, popularity,
                        poster_path, release_date, is_adult,
                        director, director_ko, cast_ko,
                        production_countries_ko, release_season, weighted_score,
                        emotion_tags, mbti_scores, weather_scores
                    ) VALUES (
                        :id, :title, :title_ko, :cert, :runtime,
                        :vote_avg, :vote_cnt, :overview, :popularity,
                        :poster, :release_date, :is_adult,
                        :director, :director_ko, :cast_ko,
                        :countries_ko, :release_season, :weighted_score,
                        :emotion_tags, :mbti_scores, :weather_scores
                    )
                """), {
                    "id": movie_id,
                    "title": title_en,
                    "title_ko": title_ko,
                    "cert": row.get('certification', '').strip() or None,
                    "runtime": parse_int(row.get('runtime', '')),
                    "vote_avg": parse_float(row.get('vote_average', '')),
                    "vote_cnt": parse_int(row.get('vote_count', '')),
                    "overview": overview,
                    "popularity": parse_float(row.get('popularity', '')),
                    "poster": row.get('poster_path', '').strip() or None,
                    "release_date": parse_date(row.get('release_date', '')),
                    "is_adult": parse_bool(row.get('is_adult', '')),
                    "director": director,
                    "director_ko": director_ko,
                    "cast_ko": cast_ko,
                    "countries_ko": countries_ko,
                    "release_season": release_season,
                    "weighted_score": parse_float(row.get('weighted_score', '')),
                    "emotion_tags": json.dumps(emotion) if emotion else None,
                    "mbti_scores": json.dumps(mbti) if mbti else None,
                    "weather_scores": json.dumps(weather) if weather else None,
                })

            conn.commit()
            print(f"  {min(i + BATCH_SIZE, len(rows))}/{len(rows)} movies...")

        # ── 6. Insert relationships ──
        print("\n[6/7] Inserting relationships...")

        # movie_genres
        print("  Inserting movie_genres...")
        count = 0
        for i, row in enumerate(rows):
            movie_id = int(row['id'])
            for genre_name in parse_list(row.get('genres', '')):
                genre_id = genre_map.get(genre_name)
                if genre_id:
                    conn.execute(text(
                        "INSERT INTO movie_genres (movie_id, genre_id) VALUES (:mid, :gid) ON CONFLICT DO NOTHING"
                    ), {"mid": movie_id, "gid": genre_id})
                    count += 1
            if (i + 1) % BATCH_SIZE == 0:
                conn.commit()
        conn.commit()
        print(f"    {count} genre links")

        # movie_cast (actors + directors)
        print("  Inserting movie_cast...")
        count = 0
        for i, row in enumerate(rows):
            movie_id = int(row['id'])
            # Actors
            for name in parse_list(row.get('cast', '')):
                pid = person_map.get(name)
                if pid:
                    conn.execute(text(
                        "INSERT INTO movie_cast (movie_id, person_id, role) VALUES (:mid, :pid, 'actor') ON CONFLICT DO NOTHING"
                    ), {"mid": movie_id, "pid": pid})
                    count += 1
            # Director
            director = row.get('director', '').strip()
            if director:
                pid = person_map.get(director)
                if pid:
                    conn.execute(text(
                        "INSERT INTO movie_cast (movie_id, person_id, role) VALUES (:mid, :pid, 'director') ON CONFLICT DO NOTHING"
                    ), {"mid": movie_id, "pid": pid})
                    count += 1
            if (i + 1) % BATCH_SIZE == 0:
                conn.commit()
        conn.commit()
        print(f"    {count} cast links")

        # movie_keywords
        print("  Inserting movie_keywords...")
        count = 0
        for i, row in enumerate(rows):
            movie_id = int(row['id'])
            for kw in parse_list(row.get('keywords', '')):
                kid = keyword_map.get(kw)
                if kid:
                    conn.execute(text(
                        "INSERT INTO movie_keywords (movie_id, keyword_id) VALUES (:mid, :kid) ON CONFLICT DO NOTHING"
                    ), {"mid": movie_id, "kid": kid})
                    count += 1
            if (i + 1) % BATCH_SIZE == 0:
                conn.commit()
        conn.commit()
        print(f"    {count} keyword links")

        # movie_countries
        print("  Inserting movie_countries...")
        count = 0
        for i, row in enumerate(rows):
            movie_id = int(row['id'])
            for c in parse_list(row.get('production_countries', '')):
                cid = country_map.get(c)
                if cid:
                    conn.execute(text(
                        "INSERT INTO movie_countries (movie_id, country_id) VALUES (:mid, :cid) ON CONFLICT DO NOTHING"
                    ), {"mid": movie_id, "cid": cid})
                    count += 1
            if (i + 1) % BATCH_SIZE == 0:
                conn.commit()
        conn.commit()
        print(f"    {count} country links")

        # similar_movies
        print("  Inserting similar_movies...")
        count = 0
        skipped = 0
        for i, row in enumerate(rows):
            movie_id = int(row['id'])
            similar_ids_str = row.get('similar_movie_ids', '').strip()
            if not similar_ids_str:
                continue
            for sid_str in similar_ids_str.split(','):
                sid_str = sid_str.strip()
                if not sid_str:
                    continue
                try:
                    sid = int(float(sid_str))
                except ValueError:
                    continue
                if sid in movie_ids_set and sid != movie_id:
                    conn.execute(text(
                        "INSERT INTO similar_movies (movie_id, similar_movie_id) VALUES (:mid, :sid) ON CONFLICT DO NOTHING"
                    ), {"mid": movie_id, "sid": sid})
                    count += 1
                else:
                    skipped += 1
            if (i + 1) % BATCH_SIZE == 0:
                conn.commit()
        conn.commit()
        print(f"    {count} similar links ({skipped} skipped - not in dataset)")

        # ── 7. Verify ──
        print("\n[7/7] Verification...")
        checks = [
            ("movies", "SELECT COUNT(*) FROM movies"),
            ("genres", "SELECT COUNT(*) FROM genres"),
            ("persons", "SELECT COUNT(*) FROM persons"),
            ("keywords", "SELECT COUNT(*) FROM keywords"),
            ("countries", "SELECT COUNT(*) FROM countries"),
            ("movie_genres", "SELECT COUNT(*) FROM movie_genres"),
            ("movie_cast", "SELECT COUNT(*) FROM movie_cast"),
            ("movie_keywords", "SELECT COUNT(*) FROM movie_keywords"),
            ("movie_countries", "SELECT COUNT(*) FROM movie_countries"),
            ("similar_movies", "SELECT COUNT(*) FROM similar_movies"),
            ("emotion_tags (restored)", "SELECT COUNT(*) FROM movies WHERE emotion_tags IS NOT NULL AND emotion_tags != '{}'::jsonb"),
            ("mbti_scores (restored)", "SELECT COUNT(*) FROM movies WHERE mbti_scores IS NOT NULL AND mbti_scores != '{}'::jsonb"),
            ("weather_scores (restored)", "SELECT COUNT(*) FROM movies WHERE weather_scores IS NOT NULL AND weather_scores != '{}'::jsonb"),
        ]
        for label, query in checks:
            result = conn.execute(text(query)).scalar()
            print(f"  {label}: {result:,}")

    print("\n" + "=" * 60)
    print("Import complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_import()
