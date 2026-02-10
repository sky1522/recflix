"""
Test new LLM prompt with 20 movies: compare old vs new emotion_tags scores.
Dry-run only - does NOT update DB.
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv()

import psycopg2
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
MODEL = "claude-sonnet-4-20250514"
BATCH_SIZE = 10

# 20 target movie IDs
TARGET_IDS = [
    # 4 required
    27205, 155, 157336, 24428,
    # 13 movies with 2x 1.0 scores
    572802, 8966, 68726, 141052, 13494, 117263, 299536, 791373,
    1018, 181812, 140607, 246655, 823464,
    # 3 movies with 3x 0.8+ scores
    4922, 383498, 137113,
]

SYSTEM_PROMPT = """You are a movie emotion analyst. For each movie, analyze its plot and genres to score 7 emotion clusters from 0.0 to 1.0.

CLUSTERS:
- healing (힐링): Family bonds, friendship, growth, warmth, comfort, heartwarming stories
- tension (긴장감): Plot twists, mystery, suspense, psychological thriller, mind games
- energy (에너지): Action, explosions, chase scenes, revenge, superheroes, intense combat
- romance (로맨스): Love stories, first love, breakups, destiny, emotional relationships
- deep (깊이): Life philosophy, solitude, true stories, social issues, existential themes
- fantasy (판타지): Magic, space, superpowers, time travel, mythical creatures, sci-fi worlds
- light (라이트): Comedy, humor, everyday life, parody, feel-good, lighthearted fun

SCORING RULES (CRITICAL - follow strictly):
- 0.0: No relation to this cluster at all
- 0.1~0.2: Faint trace, barely noticeable elements
- 0.3~0.4: Minor subplot or secondary elements
- 0.5~0.6: Notable presence but NOT the main focus
- 0.7~0.8: Major theme, one of the film's defining aspects
- 0.9: Dominant theme that defines the entire film's identity
- 1.0: RESERVED for the single most iconic example of this cluster (e.g., "The Notebook" for romance, "Inception" for tension). Give 1.0 to at most 1 cluster per movie, and only if the movie is a genre-defining masterpiece for that cluster. Most movies should have 0 clusters at 1.0.

DISTRIBUTION GUIDELINES:
- Most scores should fall in the 0.2~0.7 range
- A typical movie should have 1-2 clusters at 0.6~0.8 and the rest below 0.5
- Having 3+ clusters above 0.7 should be very rare (only for genre-blending blockbusters)
- Use the full range of decimal values (0.35, 0.55, 0.72, etc.), not just round numbers

Return ONLY a JSON object with movie IDs as keys and score objects as values.
Example: {"12345": {"healing": 0.2, "tension": 0.75, "energy": 0.45, "romance": 0.1, "deep": 0.3, "fantasy": 0.0, "light": 0.05}}"""


def analyze_batch(movies):
    movies_text = []
    for m in movies:
        genres_str = ", ".join(m['genres']) if m['genres'] else "Unknown"
        overview = m['overview'] or "No description available"
        if len(overview) > 500:
            overview = overview[:500] + "..."
        movies_text.append(f"ID: {m['id']}\nTitle: {m['title']}\nGenres: {genres_str}\nPlot: {overview}")

    user_prompt = f"""Analyze these {len(movies)} movies and return emotion cluster scores (0.0-1.0) for each:

{chr(10).join(movies_text)}

Return ONLY valid JSON with movie IDs as keys. No explanation needed."""

    response = client.messages.create(
        model=MODEL, max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )
    content = response.content[0].text.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()
    return {int(k): v for k, v in json.loads(content).items()}


def main():
    print("=" * 80)
    print("LLM Prompt Test: 20 Movies (Dry Run)")
    print("=" * 80)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # Fetch movie data
    ids_str = ','.join(str(i) for i in TARGET_IDS)
    cur.execute(f"""
        SELECT m.id, m.title, m.title_ko, m.overview, m.emotion_tags,
               ARRAY_AGG(DISTINCT g.name) FILTER (WHERE g.name IS NOT NULL) as genres
        FROM movies m
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE m.id IN ({ids_str})
        GROUP BY m.id, m.title, m.title_ko, m.overview, m.emotion_tags
    """)
    rows = cur.fetchall()
    movies_map = {}
    old_scores = {}
    for r in rows:
        movies_map[r[0]] = {
            'id': r[0], 'title': r[1], 'title_ko': r[2],
            'overview': r[3], 'genres': r[5] or []
        }
        old_scores[r[0]] = r[4] or {}

    print(f"Fetched {len(movies_map)} movies from DB\n")

    # Process in 2 batches of 10
    movies_list = [movies_map[mid] for mid in TARGET_IDS if mid in movies_map]
    new_scores = {}

    for i in range(0, len(movies_list), BATCH_SIZE):
        batch = movies_list[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        print(f"Batch {batch_num}/2: Analyzing {len(batch)} movies...")
        for m in batch:
            print(f"  - {m['title_ko']} ({m['title']})")
        result = analyze_batch(batch)
        new_scores.update(result)
        print(f"  Got {len(result)} results\n")
        if i + BATCH_SIZE < len(movies_list):
            time.sleep(1)

    # Comparison table
    clusters = ['healing', 'tension', 'energy', 'romance', 'deep', 'fantasy', 'light']

    print("=" * 80)
    print("COMPARISON: Old vs New Scores")
    print("=" * 80)

    for mid in TARGET_IDS:
        if mid not in movies_map or mid not in new_scores:
            continue
        m = movies_map[mid]
        old = old_scores.get(mid, {})
        new = new_scores.get(mid, {})

        print(f"\n{'─'*70}")
        print(f"  {m['title_ko']} ({m['title']})")
        print(f"  {'Cluster':10s} {'Old':>6s} {'New':>6s} {'Diff':>7s}  Change")
        print(f"  {'─'*55}")
        for c in clusters:
            o = float(old.get(c, 0))
            n = float(new.get(c, 0))
            diff = n - o
            arrow = "→" if abs(diff) < 0.05 else ("↓" if diff < 0 else "↑")
            bar_old = "█" * int(o * 10)
            bar_new = "█" * int(n * 10)
            print(f"  {c:10s} {o:5.2f}  {n:5.2f}  {diff:+5.2f}  {arrow}  {bar_old} → {bar_new}")

    # Summary stats
    print(f"\n{'='*80}")
    print("SUMMARY STATISTICS")
    print(f"{'='*80}")

    for label, scores in [("Old", old_scores), ("New", new_scores)]:
        cnt_10 = sum(1 for mid in new_scores for c in clusters if float(scores.get(mid, {}).get(c, 0)) == 1.0)
        cnt_09 = sum(1 for mid in new_scores for c in clusters if 0.85 <= float(scores.get(mid, {}).get(c, 0)) < 1.0)
        cnt_08 = sum(1 for mid in new_scores for c in clusters if 0.75 <= float(scores.get(mid, {}).get(c, 0)) < 0.85)
        cnt_mid = sum(1 for mid in new_scores for c in clusters if 0.3 <= float(scores.get(mid, {}).get(c, 0)) < 0.75)
        cnt_low = sum(1 for mid in new_scores for c in clusters if 0 < float(scores.get(mid, {}).get(c, 0)) < 0.3)
        cnt_zero = sum(1 for mid in new_scores for c in clusters if float(scores.get(mid, {}).get(c, 0)) == 0.0)
        total = len(new_scores) * 7
        print(f"\n{label} Distribution (across {len(new_scores)} movies x 7 clusters = {total} scores):")
        print(f"  1.0 (만점):    {cnt_10:3d} ({cnt_10/total*100:5.1f}%)")
        print(f"  0.85~0.99:    {cnt_09:3d} ({cnt_09/total*100:5.1f}%)")
        print(f"  0.75~0.84:    {cnt_08:3d} ({cnt_08/total*100:5.1f}%)")
        print(f"  0.3~0.74:     {cnt_mid:3d} ({cnt_mid/total*100:5.1f}%)")
        print(f"  0.01~0.29:    {cnt_low:3d} ({cnt_low/total*100:5.1f}%)")
        print(f"  0.0 (무관):    {cnt_zero:3d} ({cnt_zero/total*100:5.1f}%)")

    cur.close()
    conn.close()
    print("\nDone! (Dry run - DB not updated)")


if __name__ == "__main__":
    main()
