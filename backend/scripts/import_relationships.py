"""
Import relationships only (genres, cast, keywords, countries, similar_movies)
Run after movies are already imported.
"""
import csv
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from sqlalchemy import text
from app.database import engine

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "raw", "MOVIE_total_FINAL_FINAL_2010.csv"
)
BATCH_SIZE = 1000


def parse_list(val):
    if not val or val.strip() == '':
        return []
    return [item.strip() for item in val.split(',') if item.strip()]


def run():
    print("Reading CSV...")
    rows = []
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            rows.append(row)
    print(f"  {len(rows)} rows")

    movie_ids_set = {int(r['id']) for r in rows}

    with engine.connect() as conn:
        # Clear existing relationship data
        print("\nClearing relationship tables...")
        for t in ['similar_movies', 'movie_keywords', 'movie_countries', 'movie_cast', 'movie_genres']:
            conn.execute(text(f"DELETE FROM {t}"))
            print(f"  Cleared {t}")
        conn.commit()

        # Load lookups
        genre_map = {r[1]: r[0] for r in conn.execute(text("SELECT id, name FROM genres"))}
        person_map = {r[1]: r[0] for r in conn.execute(text("SELECT id, name FROM persons"))}
        keyword_map = {r[1]: r[0] for r in conn.execute(text("SELECT id, name FROM keywords"))}
        country_map = {r[1]: r[0] for r in conn.execute(text("SELECT id, name FROM countries"))}
        print(f"\nLookups: {len(genre_map)} genres, {len(person_map)} persons, {len(keyword_map)} keywords, {len(country_map)} countries")

        # ── movie_genres ──
        print("\nInserting movie_genres...")
        count = 0
        for i, row in enumerate(rows):
            mid = int(row['id'])
            seen = set()
            for g in parse_list(row.get('genres', '')):
                gid = genre_map.get(g)
                if gid and gid not in seen:
                    seen.add(gid)
                    conn.execute(text(
                        "INSERT INTO movie_genres (movie_id, genre_id) VALUES (:mid, :gid)"
                    ), {"mid": mid, "gid": gid})
                    count += 1
            if (i + 1) % 5000 == 0:
                conn.commit()
                print(f"  {i+1}/{len(rows)} movies processed...")
        conn.commit()
        print(f"  Total: {count} genre links")

        # ── movie_cast ──
        print("\nInserting movie_cast...")
        count = 0
        for i, row in enumerate(rows):
            mid = int(row['id'])
            seen_pids = set()
            # Actors
            for name in parse_list(row.get('cast', '')):
                pid = person_map.get(name)
                if pid and pid not in seen_pids:
                    seen_pids.add(pid)
                    conn.execute(text(
                        "INSERT INTO movie_cast (movie_id, person_id, role) VALUES (:mid, :pid, 'actor')"
                    ), {"mid": mid, "pid": pid})
                    count += 1
            # Director
            director = row.get('director', '').strip()
            if director:
                pid = person_map.get(director)
                if pid and pid not in seen_pids:
                    seen_pids.add(pid)
                    conn.execute(text(
                        "INSERT INTO movie_cast (movie_id, person_id, role) VALUES (:mid, :pid, 'director')"
                    ), {"mid": mid, "pid": pid})
                    count += 1
            if (i + 1) % 5000 == 0:
                conn.commit()
                print(f"  {i+1}/{len(rows)} movies processed...")
        conn.commit()
        print(f"  Total: {count} cast links")

        # ── movie_keywords ──
        print("\nInserting movie_keywords...")
        count = 0
        for i, row in enumerate(rows):
            mid = int(row['id'])
            seen = set()
            for kw in parse_list(row.get('keywords', '')):
                kid = keyword_map.get(kw)
                if kid and kid not in seen:
                    seen.add(kid)
                    conn.execute(text(
                        "INSERT INTO movie_keywords (movie_id, keyword_id) VALUES (:mid, :kid)"
                    ), {"mid": mid, "kid": kid})
                    count += 1
            if (i + 1) % 10000 == 0:
                conn.commit()
        conn.commit()
        print(f"  Total: {count} keyword links")

        # ── movie_countries ──
        print("\nInserting movie_countries...")
        count = 0
        for i, row in enumerate(rows):
            mid = int(row['id'])
            seen = set()
            for c in parse_list(row.get('production_countries', '')):
                cid = country_map.get(c)
                if cid and cid not in seen:
                    seen.add(cid)
                    conn.execute(text(
                        "INSERT INTO movie_countries (movie_id, country_id) VALUES (:mid, :cid)"
                    ), {"mid": mid, "cid": cid})
                    count += 1
            if (i + 1) % 10000 == 0:
                conn.commit()
        conn.commit()
        print(f"  Total: {count} country links")

        # ── similar_movies ──
        print("\nInserting similar_movies...")
        count = 0
        skipped = 0
        for i, row in enumerate(rows):
            mid = int(row['id'])
            sids_str = row.get('similar_movie_ids', '').strip()
            if not sids_str:
                continue
            seen = set()
            for s in sids_str.split(','):
                s = s.strip()
                if not s:
                    continue
                try:
                    sid = int(float(s))
                except ValueError:
                    continue
                if sid in movie_ids_set and sid != mid and sid not in seen:
                    seen.add(sid)
                    conn.execute(text(
                        "INSERT INTO similar_movies (movie_id, similar_movie_id) VALUES (:mid, :sid) ON CONFLICT DO NOTHING"
                    ), {"mid": mid, "sid": sid})
                    count += 1
                else:
                    skipped += 1
            if (i + 1) % 10000 == 0:
                conn.commit()
        conn.commit()
        print(f"  Total: {count} similar links ({skipped} skipped)")

        # ── Verification ──
        print("\n=== Verification ===")
        for t in ['movies', 'genres', 'persons', 'keywords', 'countries',
                   'movie_genres', 'movie_cast', 'movie_keywords', 'movie_countries', 'similar_movies']:
            r = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
            print(f"  {t}: {r:,}")

        r = conn.execute(text("SELECT COUNT(*) FROM movies WHERE emotion_tags IS NOT NULL AND emotion_tags != '{}'::jsonb")).scalar()
        print(f"  emotion_tags (restored): {r:,}")
        r = conn.execute(text("SELECT COUNT(*) FROM movies WHERE mbti_scores IS NOT NULL AND mbti_scores != '{}'::jsonb")).scalar()
        print(f"  mbti_scores (restored): {r:,}")

    print("\nDone!")


if __name__ == "__main__":
    run()
