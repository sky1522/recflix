"""
Production-optimized CSV import using psycopg2 execute_values (bulk insert).
Designed for remote DB with high network latency.

Usage:
  cd backend
  DATABASE_URL="postgresql://..." ./venv/Scripts/python.exe scripts/import_production.py
"""
import csv
import sys
import os
import io
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import execute_values

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "raw", "MOVIE_total_FINAL_FINAL_2010.csv"
)
BULK_SIZE = 2000


def pf(val, default=0.0):
    if not val or val.strip() == '': return default
    try: return float(val)
    except: return default

def pi(val, default=0):
    if not val or val.strip() == '': return default
    try: return int(float(val))
    except: return default

def pb(val):
    if not val: return False
    return val.strip().upper() == 'TRUE'

def pd(val):
    if not val or val.strip() == '': return None
    try: return datetime.strptime(val.strip(), '%Y-%m-%d').date()
    except: return None

def pl(val):
    if not val or val.strip() == '': return []
    return [x.strip() for x in val.split(',') if x.strip()]


def run():
    db_url = os.environ.get('DATABASE_URL', '')
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    print("=" * 60)
    print("Production Import (bulk optimized)")
    print("=" * 60)

    # Read CSV
    print("\n[1/8] Reading CSV...")
    rows = []
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    print(f"  {len(rows)} rows")
    movie_ids_set = {int(r['id']) for r in rows}

    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    # ── 2. Backup emotion_tags ──
    print("\n[2/8] Backing up existing scores...")
    cur.execute("SELECT id, emotion_tags, mbti_scores, weather_scores FROM movies WHERE emotion_tags IS NOT NULL AND emotion_tags != '{}'::jsonb")
    emotion_backup, mbti_backup, weather_backup = {}, {}, {}
    for mid, et, mb, ws in cur.fetchall():
        if et: emotion_backup[mid] = et
        if mb: mbti_backup[mid] = mb
        if ws: weather_backup[mid] = ws
    print(f"  emotion: {len(emotion_backup)}, mbti: {len(mbti_backup)}, weather: {len(weather_backup)}")

    # ── 3. Clear tables ──
    print("\n[3/8] Clearing tables...")
    for t in ['similar_movies','movie_keywords','movie_countries','movie_cast','movie_genres','movies','persons','keywords','countries']:
        cur.execute(f"DELETE FROM {t}")
        print(f"  {t} cleared")
    conn.commit()

    # ── 4. Genres check ──
    print("\n[4/8] Checking genres...")
    cur.execute("SELECT id, name FROM genres")
    genre_map = {r[1]: r[0] for r in cur.fetchall()}
    csv_genres = set()
    for r in rows:
        for g in pl(r.get('genres','')):
            csv_genres.add(g)
    missing = csv_genres - set(genre_map.keys())
    if missing:
        for g in missing:
            cur.execute("INSERT INTO genres (name, name_ko) VALUES (%s, %s)", (g, g))
        conn.commit()
        cur.execute("SELECT id, name FROM genres")
        genre_map = {r[1]: r[0] for r in cur.fetchall()}
    print(f"  {len(genre_map)} genres")

    # ── 5. Bulk insert persons, keywords, countries ──
    print("\n[5/8] Bulk inserting lookup tables...")

    # Persons
    all_persons = set()
    for r in rows:
        for n in pl(r.get('cast','')): all_persons.add(n)
        d = r.get('director','').strip()
        if d: all_persons.add(d)
    person_list = sorted(all_persons)
    print(f"  Inserting {len(person_list)} persons...", end=" ", flush=True)
    for i in range(0, len(person_list), BULK_SIZE):
        batch = [(n,) for n in person_list[i:i+BULK_SIZE]]
        execute_values(cur, "INSERT INTO persons (name) VALUES %s", batch)
    conn.commit()
    cur.execute("SELECT id, name FROM persons")
    person_map = {r[1]: r[0] for r in cur.fetchall()}
    print(f"OK ({len(person_map)})")

    # Keywords
    all_kw = set()
    for r in rows:
        for k in pl(r.get('keywords','')): all_kw.add(k)
    kw_list = sorted(all_kw)
    print(f"  Inserting {len(kw_list)} keywords...", end=" ", flush=True)
    execute_values(cur, "INSERT INTO keywords (name) VALUES %s", [(k,) for k in kw_list])
    conn.commit()
    cur.execute("SELECT id, name FROM keywords")
    keyword_map = {r[1]: r[0] for r in cur.fetchall()}
    print(f"OK ({len(keyword_map)})")

    # Countries
    all_c = set()
    for r in rows:
        for c in pl(r.get('production_countries','')): all_c.add(c)
    c_list = sorted(all_c)
    print(f"  Inserting {len(c_list)} countries...", end=" ", flush=True)
    execute_values(cur, "INSERT INTO countries (name) VALUES %s", [(c,) for c in c_list])
    conn.commit()
    cur.execute("SELECT id, name FROM countries")
    country_map = {r[1]: r[0] for r in cur.fetchall()}
    print(f"OK ({len(country_map)})")

    # ── 6. Bulk insert movies ──
    print("\n[6/8] Bulk inserting movies...")
    for i in range(0, len(rows), BULK_SIZE):
        batch = rows[i:i+BULK_SIZE]
        values = []
        for r in batch:
            mid = int(r['id'])
            title_en = r.get('title_ko_en','').strip() or r.get('title','').strip()
            title_ko = r.get('title','').strip()
            et = emotion_backup.get(mid)
            mb = mbti_backup.get(mid)
            ws = weather_backup.get(mid)
            values.append((
                mid, title_en, title_ko,
                r.get('certification','').strip() or None,
                pi(r.get('runtime','')),
                pf(r.get('vote_average','')),
                pi(r.get('vote_count','')),
                r.get('overview','').strip() or None,
                pf(r.get('popularity','')),
                r.get('poster_path','').strip() or None,
                pd(r.get('release_date','')),
                pb(r.get('is_adult','')),
                r.get('director','').strip() or None,
                r.get('director_ko','').strip() or None,
                r.get('cast_ko','').strip() or None,
                r.get('production_countries_ko','').strip() or None,
                r.get('release_season','').strip() or None,
                pf(r.get('weighted_score','')),
                json.dumps(et) if et else None,
                json.dumps(mb) if mb else None,
                json.dumps(ws) if ws else None,
            ))
        execute_values(cur, """
            INSERT INTO movies (
                id, title, title_ko, certification, runtime,
                vote_average, vote_count, overview, popularity,
                poster_path, release_date, is_adult,
                director, director_ko, cast_ko,
                production_countries_ko, release_season, weighted_score,
                emotion_tags, mbti_scores, weather_scores
            ) VALUES %s
        """, values, template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb)")
        conn.commit()
        print(f"  {min(i+BULK_SIZE, len(rows))}/{len(rows)} movies")

    # ── 7. Bulk insert relationships ──
    print("\n[7/8] Bulk inserting relationships...")

    # movie_genres
    print("  movie_genres...", end=" ", flush=True)
    mg_vals = []
    for r in rows:
        mid = int(r['id'])
        seen = set()
        for g in pl(r.get('genres','')):
            gid = genre_map.get(g)
            if gid and gid not in seen:
                seen.add(gid)
                mg_vals.append((mid, gid))
    for i in range(0, len(mg_vals), BULK_SIZE):
        execute_values(cur, "INSERT INTO movie_genres (movie_id, genre_id) VALUES %s", mg_vals[i:i+BULK_SIZE])
    conn.commit()
    print(f"{len(mg_vals)}")

    # movie_cast
    print("  movie_cast...", end=" ", flush=True)
    mc_vals = []
    for r in rows:
        mid = int(r['id'])
        seen = set()
        for n in pl(r.get('cast','')):
            pid = person_map.get(n)
            if pid and pid not in seen:
                seen.add(pid)
                mc_vals.append((mid, pid, 'actor'))
        d = r.get('director','').strip()
        if d:
            pid = person_map.get(d)
            if pid and pid not in seen:
                seen.add(pid)
                mc_vals.append((mid, pid, 'director'))
    for i in range(0, len(mc_vals), BULK_SIZE):
        execute_values(cur, "INSERT INTO movie_cast (movie_id, person_id, role) VALUES %s", mc_vals[i:i+BULK_SIZE])
    conn.commit()
    print(f"{len(mc_vals)}")

    # movie_keywords
    print("  movie_keywords...", end=" ", flush=True)
    mk_vals = []
    for r in rows:
        mid = int(r['id'])
        seen = set()
        for k in pl(r.get('keywords','')):
            kid = keyword_map.get(k)
            if kid and kid not in seen:
                seen.add(kid)
                mk_vals.append((mid, kid))
    for i in range(0, len(mk_vals), BULK_SIZE):
        execute_values(cur, "INSERT INTO movie_keywords (movie_id, keyword_id) VALUES %s", mk_vals[i:i+BULK_SIZE])
    conn.commit()
    print(f"{len(mk_vals)}")

    # movie_countries
    print("  movie_countries...", end=" ", flush=True)
    mco_vals = []
    for r in rows:
        mid = int(r['id'])
        seen = set()
        for c in pl(r.get('production_countries','')):
            cid = country_map.get(c)
            if cid and cid not in seen:
                seen.add(cid)
                mco_vals.append((mid, cid))
    for i in range(0, len(mco_vals), BULK_SIZE):
        execute_values(cur, "INSERT INTO movie_countries (movie_id, country_id) VALUES %s", mco_vals[i:i+BULK_SIZE])
    conn.commit()
    print(f"{len(mco_vals)}")

    # similar_movies
    print("  similar_movies...", end=" ", flush=True)
    sm_vals = []
    for r in rows:
        mid = int(r['id'])
        sids = r.get('similar_movie_ids','').strip()
        if not sids: continue
        seen = set()
        for s in sids.split(','):
            s = s.strip()
            if not s: continue
            try: sid = int(float(s))
            except: continue
            if sid in movie_ids_set and sid != mid and sid not in seen:
                seen.add(sid)
                sm_vals.append((mid, sid))
    for i in range(0, len(sm_vals), BULK_SIZE):
        execute_values(cur, "INSERT INTO similar_movies (movie_id, similar_movie_id) VALUES %s ON CONFLICT DO NOTHING", sm_vals[i:i+BULK_SIZE])
    conn.commit()
    print(f"{len(sm_vals)}")

    # ── 8. Verify ──
    print("\n[8/8] Verification...")
    for t in ['movies','genres','persons','keywords','countries','movie_genres','movie_cast','movie_keywords','movie_countries','similar_movies']:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t}: {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(*) FROM movies WHERE emotion_tags IS NOT NULL AND emotion_tags != '{}'::jsonb")
    print(f"  emotion_tags restored: {cur.fetchone()[0]:,}")
    cur.execute("SELECT COUNT(*) FROM movies WHERE mbti_scores IS NOT NULL AND mbti_scores != '{}'::jsonb")
    print(f"  mbti_scores restored: {cur.fetchone()[0]:,}")

    cur.close()
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    run()
