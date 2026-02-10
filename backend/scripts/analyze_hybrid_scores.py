"""
Hybrid Recommendation Score Analyzer for RecFlix
=================================================
Simulates the hybrid scoring logic from recommendations.py for INTJ + sunny + relaxed
and outputs a detailed breakdown of each score component for the top 40 movies.

Two scenarios:
  1. New user (no personal preferences)
  2. User with simulated personal preferences (top 3 genres from popular movies)

Usage:
    python backend/scripts/analyze_hybrid_scores.py
"""

import json
import statistics
import psycopg2
import psycopg2.extras

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "recflix",
    "password": "recflix123",
    "dbname": "recflix",
}

# ---------------------------------------------------------------------------
# Constants (mirrored from backend/app/api/v1/recommendations.py)
# ---------------------------------------------------------------------------
# With mood (tuned v2)
WEIGHT_MBTI = 0.25
WEIGHT_WEATHER = 0.20
WEIGHT_MOOD = 0.30
WEIGHT_PERSONAL = 0.25

# Quality correction
QUALITY_BOOST_MIN = 0.85
QUALITY_BOOST_MAX = 1.00
QUALITY_MAX_WS = 9.0

# Without mood (legacy / fallback)
WEIGHT_MBTI_NO_MOOD = 0.35
WEIGHT_WEATHER_NO_MOOD = 0.25
WEIGHT_PERSONAL_NO_MOOD = 0.40

MOOD_EMOTION_MAPPING = {
    "relaxed":     ["healing"],
    "tense":       ["tension"],
    "excited":     ["energy"],
    "emotional":   ["romance", "deep"],
    "imaginative": ["fantasy"],
    "light":       ["light"],
}

# ---------------------------------------------------------------------------
# Simulation parameters
# ---------------------------------------------------------------------------
MBTI = "INTJ"
WEATHER = "sunny"
MOOD = "relaxed"                 # maps to emotion_tags key "healing"
MIN_WEIGHTED_SCORE = 6.0
CANDIDATE_LIMIT = 200           # same as the main endpoint
TOP_N = 40                      # top movies to display


def connect():
    """Return a psycopg2 connection with RealDictCursor factory."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Data-fetching helpers
# ---------------------------------------------------------------------------

def fetch_candidate_movies(cur, exclude_ids=None):
    """
    Fetch candidate movies exactly like the main endpoint:
    weighted_score >= 6.0, ORDER BY popularity DESC, weighted_score DESC, LIMIT 200.
    """
    exclude_ids = exclude_ids or set()
    if exclude_ids:
        cur.execute("""
            SELECT m.id, m.title, m.title_ko, m.popularity,
                   m.weighted_score, m.vote_average, m.vote_count,
                   m.mbti_scores, m.weather_scores, m.emotion_tags
            FROM movies m
            WHERE COALESCE(m.weighted_score, 0) >= %s
              AND m.id != ALL(%s)
            ORDER BY m.popularity DESC, m.weighted_score DESC
            LIMIT %s
        """, (MIN_WEIGHTED_SCORE, list(exclude_ids), CANDIDATE_LIMIT))
    else:
        cur.execute("""
            SELECT m.id, m.title, m.title_ko, m.popularity,
                   m.weighted_score, m.vote_average, m.vote_count,
                   m.mbti_scores, m.weather_scores, m.emotion_tags
            FROM movies m
            WHERE COALESCE(m.weighted_score, 0) >= %s
            ORDER BY m.popularity DESC, m.weighted_score DESC
            LIMIT %s
        """, (MIN_WEIGHTED_SCORE, CANDIDATE_LIMIT))
    return cur.fetchall()


def fetch_movie_genres(cur, movie_ids):
    """
    Return a dict {movie_id: [genre_name, ...]} for the given movie IDs.
    """
    if not movie_ids:
        return {}
    cur.execute("""
        SELECT mg.movie_id, g.name
        FROM movie_genres mg
        JOIN genres g ON g.id = mg.genre_id
        WHERE mg.movie_id = ANY(%s)
    """, (list(movie_ids),))
    result = {}
    for row in cur.fetchall():
        result.setdefault(row["movie_id"], []).append(row["name"])
    return result


def derive_top_genres_from_popular(cur, top_n_popular=30):
    """
    Simulate personal preferences by picking the top 3 genres from the
    most popular movies (as a proxy for a user who liked popular stuff).
    Returns (genre_counts_dict, top_3_genre_names_set).
    """
    cur.execute("""
        SELECT m.id
        FROM movies m
        WHERE COALESCE(m.weighted_score, 0) >= %s
        ORDER BY m.popularity DESC
        LIMIT %s
    """, (MIN_WEIGHTED_SCORE, top_n_popular))
    popular_ids = [r["id"] for r in cur.fetchall()]
    genres_map = fetch_movie_genres(cur, popular_ids)

    genre_counts = {}
    for mid in popular_ids:
        for g in genres_map.get(mid, []):
            genre_counts[g] = genre_counts.get(g, 0) + 1

    top3 = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    return genre_counts, {g[0] for g in top3}


# ---------------------------------------------------------------------------
# Scoring logic (mirrors calculate_hybrid_scores)
# ---------------------------------------------------------------------------

def calculate_scores(movie, movie_genres_list, top_genre_names, similar_ids, use_personal):
    """
    Calculate hybrid score for a single movie.
    Returns dict with all component scores and the final hybrid score.
    """
    mbti_score = 0.0
    weather_score = 0.0
    mood_score = 0.0
    personal_score = 0.0

    # --- Weights (mood is always provided in our simulation) ---
    w_mbti = WEIGHT_MBTI
    w_weather = WEIGHT_WEATHER
    w_mood = WEIGHT_MOOD
    w_personal = WEIGHT_PERSONAL

    # 1. MBTI Score
    mbti_scores = movie["mbti_scores"] or {}
    if isinstance(mbti_scores, str):
        mbti_scores = json.loads(mbti_scores)
    mbti_val = mbti_scores.get(MBTI, 0.0)
    mbti_score = float(mbti_val) if mbti_val else 0.0

    # 2. Weather Score
    weather_scores = movie["weather_scores"] or {}
    if isinstance(weather_scores, str):
        weather_scores = json.loads(weather_scores)
    weather_val = weather_scores.get(WEATHER, 0.0)
    weather_score = float(weather_val) if weather_val else 0.0

    # 3. Mood Score (emotion_tags -> "healing" for relaxed)
    emotion_tags = movie["emotion_tags"] or {}
    if isinstance(emotion_tags, str):
        emotion_tags = json.loads(emotion_tags)
    emotion_keys = MOOD_EMOTION_MAPPING.get(MOOD, [])
    if emotion_keys:
        emotion_values = []
        for key in emotion_keys:
            val = emotion_tags.get(key, 0.0)
            if val:
                emotion_values.append(float(val))
        if emotion_values:
            mood_score = sum(emotion_values) / len(emotion_values)

    # 4. Personal Score (only when use_personal is True)
    personal_detail = ""
    if use_personal:
        genre_set = set(movie_genres_list)
        matching_genres = genre_set & top_genre_names

        # Genre match bonus
        if matching_genres:
            genre_bonus = len(matching_genres) * 0.3
            personal_score += min(genre_bonus, 0.9)
            personal_detail += f"genre({','.join(matching_genres)})={min(genre_bonus, 0.9):.2f}"

        # Similar movie bonus
        if movie["id"] in similar_ids:
            personal_score += 0.4
            personal_detail += " +similar=0.40"

    # Weighted score for quality correction
    ws = movie["weighted_score"] or 0.0

    # Hybrid score
    hybrid_score = (
        (w_mbti * mbti_score) +
        (w_weather * weather_score) +
        (w_mood * mood_score) +
        (w_personal * personal_score)
    )

    # Popularity boost
    pop_boost = 0.0
    if (movie["popularity"] or 0) > 100:
        pop_boost = 0.05
        hybrid_score += pop_boost

    # Quality correction: continuous boost based on weighted_score (6.0~max → 0.85~1.0)
    quality_ratio = min(max((ws - 6.0) / (QUALITY_MAX_WS - 6.0), 0.0), 1.0)
    quality_factor = QUALITY_BOOST_MIN + (QUALITY_BOOST_MAX - QUALITY_BOOST_MIN) * quality_ratio
    hybrid_score *= quality_factor
    personal_detail += f" qf={quality_factor:.3f}"

    # Clamp to [0, 1]
    hybrid_score = min(max(hybrid_score, 0.0), 1.0)

    return {
        "id": movie["id"],
        "title_ko": movie["title_ko"] or movie["title"],
        "mbti_score": mbti_score,
        "weather_score": weather_score,
        "mood_score": mood_score,
        "personal_score": personal_score,
        "weighted_score": ws,
        "popularity": movie["popularity"] or 0,
        "pop_boost": pop_boost,
        "w_mbti_contrib": w_mbti * mbti_score,
        "w_weather_contrib": w_weather * weather_score,
        "w_mood_contrib": w_mood * mood_score,
        "w_personal_contrib": w_personal * personal_score,
        "hybrid_score": hybrid_score,
        "personal_detail": personal_detail.strip(),
        "genres": movie_genres_list,
    }


# ---------------------------------------------------------------------------
# Printing helpers
# ---------------------------------------------------------------------------

HEADER = (
    f"{'#':>3}  {'Title (KO)':<30}  "
    f"{'MBTI':>6}  {'Weath':>6}  {'Mood':>6}  {'Pers':>6}  {'WtScr':>6}  "
    f"{'M*.25':>6}  {'W*.20':>6}  {'Mo*.3':>6}  {'P*.25':>6}  {'Pop+':>5}  "
    f"{'HYBRID':>7}  {'Detail'}"
)

SEP = "-" * len(HEADER)


def print_table(scored, label):
    print()
    print("=" * len(HEADER))
    print(f"  {label}")
    print(f"  Params: MBTI={MBTI}, Weather={WEATHER}, Mood={MOOD} (-> healing)")
    print(f"  Weights: MBTI={WEIGHT_MBTI}, Weather={WEIGHT_WEATHER}, Mood={WEIGHT_MOOD}, Personal={WEIGHT_PERSONAL}")
    print("=" * len(HEADER))
    print(HEADER)
    print(SEP)

    for i, s in enumerate(scored[:TOP_N], 1):
        title_display = s["title_ko"][:28] if s["title_ko"] else "N/A"
        print(
            f"{i:>3}  {title_display:<30}  "
            f"{s['mbti_score']:>6.3f}  {s['weather_score']:>6.3f}  {s['mood_score']:>6.3f}  "
            f"{s['personal_score']:>6.3f}  {s['weighted_score']:>6.2f}  "
            f"{s['w_mbti_contrib']:>6.3f}  {s['w_weather_contrib']:>6.3f}  "
            f"{s['w_mood_contrib']:>6.3f}  {s['w_personal_contrib']:>6.3f}  "
            f"{s['pop_boost']:>5.2f}  "
            f"{s['hybrid_score']:>7.4f}  {s['personal_detail']}"
        )

    print(SEP)


def print_statistics(scored, label):
    """Print mean/min/max for each score component across ALL candidates (not just top 40)."""
    if not scored:
        print(f"\n  No data for statistics ({label})")
        return

    components = ["mbti_score", "weather_score", "mood_score", "personal_score", "hybrid_score", "weighted_score"]
    labels = ["MBTI Score", "Weather Score", "Mood Score", "Personal Score", "Hybrid Score", "Weighted Score"]

    print()
    print(f"  Statistics across ALL {len(scored)} candidates ({label})")
    print(f"  {'Component':<18} {'Mean':>8} {'Min':>8} {'Max':>8} {'StdDev':>8}")
    print(f"  {'-'*18} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for comp, lbl in zip(components, labels):
        values = [s[comp] for s in scored]
        if values:
            mean_v = statistics.mean(values)
            min_v = min(values)
            max_v = max(values)
            std_v = statistics.stdev(values) if len(values) > 1 else 0.0
            print(f"  {lbl:<18} {mean_v:>8.4f} {min_v:>8.4f} {max_v:>8.4f} {std_v:>8.4f}")

    # Distribution of hybrid scores
    hybrid_vals = [s["hybrid_score"] for s in scored]
    buckets = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.01]
    print()
    print(f"  Hybrid Score Distribution:")
    for i in range(len(buckets) - 1):
        lo, hi = buckets[i], buckets[i + 1]
        count = sum(1 for v in hybrid_vals if lo <= v < hi)
        bar = "#" * count
        label_range = f"  [{lo:.1f}, {hi:.1f})" if hi < 1.01 else f"  [{lo:.1f}, 1.0]"
        print(f"  {label_range:<14} {count:>4}  {bar}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    conn = connect()
    cur = conn.cursor()

    print("\n" + "=" * 80)
    print("  RecFlix Hybrid Recommendation Score Analyzer")
    print("  MBTI: INTJ | Weather: sunny | Mood: relaxed (-> emotion: healing)")
    print("=" * 80)

    # -----------------------------------------------------------------------
    # Fetch candidate movies
    # -----------------------------------------------------------------------
    candidates = fetch_candidate_movies(cur)
    movie_ids = [m["id"] for m in candidates]
    genres_map = fetch_movie_genres(cur, movie_ids)

    print(f"\n  Fetched {len(candidates)} candidate movies (weighted_score >= {MIN_WEIGHTED_SCORE})")

    # Quick sanity: how many have each score type?
    has_mbti = sum(1 for m in candidates if m["mbti_scores"] and (isinstance(m["mbti_scores"], dict) and MBTI in m["mbti_scores"]))
    has_weather = sum(1 for m in candidates if m["weather_scores"] and (isinstance(m["weather_scores"], dict) and WEATHER in m["weather_scores"]))
    has_mood = sum(1 for m in candidates if m["emotion_tags"] and (isinstance(m["emotion_tags"], dict) and "healing" in m["emotion_tags"]))
    print(f"  Have MBTI({MBTI}) score: {has_mbti}/{len(candidates)}")
    print(f"  Have Weather({WEATHER}) score: {has_weather}/{len(candidates)}")
    print(f"  Have Mood(healing) score: {has_mood}/{len(candidates)}")

    # -----------------------------------------------------------------------
    # SCENARIO 1: New user (no personal preferences)
    # -----------------------------------------------------------------------
    scored_no_pref = []
    for movie in candidates:
        mg = genres_map.get(movie["id"], [])
        result = calculate_scores(
            movie, mg,
            top_genre_names=set(),     # no genre preferences
            similar_ids=set(),         # no similar movies
            use_personal=False
        )
        scored_no_pref.append(result)

    scored_no_pref.sort(key=lambda x: x["hybrid_score"], reverse=True)

    print_table(scored_no_pref, "SCENARIO 1: New User (No Personal Preferences)")
    print_statistics(scored_no_pref, "New User")

    # -----------------------------------------------------------------------
    # SCENARIO 2: User with simulated personal preferences
    # -----------------------------------------------------------------------
    genre_counts, top3_genres = derive_top_genres_from_popular(cur, top_n_popular=30)

    print(f"\n  Simulated personal preferences from top 30 popular movies:")
    print(f"    Genre counts (top 10):")
    for g, c in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        marker = " <-- TOP3" if g in top3_genres else ""
        print(f"      {g:<15} {c:>3}{marker}")

    scored_with_pref = []
    for movie in candidates:
        mg = genres_map.get(movie["id"], [])
        result = calculate_scores(
            movie, mg,
            top_genre_names=top3_genres,
            similar_ids=set(),         # no similar movies (would need user data)
            use_personal=True
        )
        scored_with_pref.append(result)

    scored_with_pref.sort(key=lambda x: x["hybrid_score"], reverse=True)

    print_table(scored_with_pref, "SCENARIO 2: User with Personal Preferences (Simulated Top-3 Genres)")
    print_statistics(scored_with_pref, "User with Preferences")

    # -----------------------------------------------------------------------
    # Comparison: top 10 changes
    # -----------------------------------------------------------------------
    print()
    print("=" * 80)
    print("  COMPARISON: Top 10 score deltas (Scenario 2 vs 1)")
    print("=" * 80)

    # Build lookup by movie id for scenario 1
    s1_map = {s["id"]: s for s in scored_no_pref}

    deltas = []
    for s in scored_with_pref:
        s1 = s1_map.get(s["id"])
        if s1:
            delta = s["hybrid_score"] - s1["hybrid_score"]
            deltas.append({
                "title_ko": s["title_ko"],
                "hybrid_s1": s1["hybrid_score"],
                "hybrid_s2": s["hybrid_score"],
                "delta": delta,
                "personal_detail": s["personal_detail"],
            })

    deltas.sort(key=lambda x: x["delta"], reverse=True)

    print(f"\n  {'Title (KO)':<30}  {'S1 Score':>8}  {'S2 Score':>8}  {'Delta':>7}  {'Personal Detail'}")
    print(f"  {'-'*30}  {'-'*8}  {'-'*8}  {'-'*7}  {'-'*30}")
    for d in deltas[:10]:
        title_display = d["title_ko"][:28] if d["title_ko"] else "N/A"
        print(
            f"  {title_display:<30}  {d['hybrid_s1']:>8.4f}  {d['hybrid_s2']:>8.4f}  "
            f"{d['delta']:>+7.4f}  {d['personal_detail']}"
        )

    # -----------------------------------------------------------------------
    # Weight sensitivity summary
    # -----------------------------------------------------------------------
    print()
    print("=" * 80)
    print("  WEIGHT SENSITIVITY ANALYSIS")
    print("=" * 80)
    print(f"""
  Current weights (with mood):
    MBTI={WEIGHT_MBTI:.2f}  Weather={WEIGHT_WEATHER:.2f}  Mood={WEIGHT_MOOD:.2f}  Personal={WEIGHT_PERSONAL:.2f}

  Theoretical max hybrid score breakdown:
    MBTI (max raw=1.0):     {WEIGHT_MBTI:.2f} * 1.0 = {WEIGHT_MBTI * 1.0:.2f}
    Weather (max raw=1.0):  {WEIGHT_WEATHER:.2f} * 1.0 = {WEIGHT_WEATHER * 1.0:.2f}
    Mood (max raw=1.0):     {WEIGHT_MOOD:.2f} * 1.0 = {WEIGHT_MOOD * 1.0:.2f}
    Personal (max raw~1.3): {WEIGHT_PERSONAL:.2f} * 1.3 = {WEIGHT_PERSONAL * 1.3:.2f}
      (genre=0.9 + quality=0.2 + similar=0.4 = 1.5, but rare to get all)
    Popularity boost:       +0.05 (if popularity > 100)
    ---------------------------------------------------------
    Theoretical max:        ~{WEIGHT_MBTI + WEIGHT_WEATHER + WEIGHT_MOOD + WEIGHT_PERSONAL * 1.3 + 0.05:.2f} (clamped to 1.0)

  Note: Personal score is uncapped before weighting (genre 0.9 + similar 0.4 + quality 0.2 = 1.5 max).
  After weighting: 0.30 * 1.5 = 0.45.  Combined with other components, total can exceed 1.0
  and is then clamped.
""")

    cur.close()
    conn.close()
    print("  Done.\n")


if __name__ == "__main__":
    main()
