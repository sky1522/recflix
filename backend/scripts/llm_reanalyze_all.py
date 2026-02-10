"""
Full LLM emotion_tags re-analysis with resume support:
1) Re-analyze existing ~915 LLM movies with improved prompt
2) Analyze new top 1,000 movies (by weighted_score/popularity)
3) Update DB after each batch (safe to interrupt & resume)
4) Show cluster statistics and cost

Usage:
  cd backend
  ./venv/Scripts/python.exe scripts/llm_reanalyze_all.py
  ./venv/Scripts/python.exe scripts/llm_reanalyze_all.py --resume   # skip already done
"""
import os, sys, json, time, io, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import execute_batch
import anthropic

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
MODEL = "claude-sonnet-4-20250514"
BATCH_SIZE = 10
NEW_MOVIE_LIMIT = 1000

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

CLUSTERS = ['healing', 'tension', 'energy', 'romance', 'deep', 'fantasy', 'light']


def analyze_batch(movies, retry=0):
    """Send a batch of movies to Claude for analysis"""
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

    try:
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

        result = json.loads(content)
        parsed = {}
        for k, v in result.items():
            mid = int(k)
            # Validate: all 7 clusters present, values 0-1
            scores = {}
            for c in CLUSTERS:
                val = float(v.get(c, 0.0))
                scores[c] = max(0.0, min(1.0, round(val, 2)))
            parsed[mid] = scores

        # Track token usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        return parsed, input_tokens, output_tokens

    except json.JSONDecodeError as e:
        if retry < 2:
            print(f"    JSON error, retrying ({retry+1}/2)...")
            time.sleep(2)
            return analyze_batch(movies, retry + 1)
        print(f"    JSON parse error after retries: {e}")
        return {}, 0, 0
    except anthropic.RateLimitError:
        wait = 30 * (retry + 1)
        print(f"    Rate limited, waiting {wait}s...")
        time.sleep(wait)
        if retry < 3:
            return analyze_batch(movies, retry + 1)
        return {}, 0, 0
    except Exception as e:
        if retry < 2:
            print(f"    Error: {e}, retrying ({retry+1}/2)...")
            time.sleep(3)
            return analyze_batch(movies, retry + 1)
        print(f"    API error after retries: {e}")
        return {}, 0, 0


def is_new_prompt_analyzed(tags):
    """Check if emotion_tags were analyzed with new prompt:
    Must have at least one score > 0.7 (LLM-tier) AND granular decimals (e.g. 0.35, 0.72)"""
    has_high = any(float(v) > 0.7 for v in tags.values())
    if not has_high:
        return False
    for k, v in tags.items():
        val = float(v)
        if val > 0 and round(val * 10) != val * 10:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true', default=True,
                        help='Skip movies already analyzed with new prompt (default: True)')
    parser.add_argument('--no-resume', dest='resume', action='store_false',
                        help='Re-analyze all movies from scratch')
    args = parser.parse_args()

    print("=" * 70)
    print("LLM Emotion Tags: Full Re-analysis (~1,915 movies)")
    print(f"  Resume mode: {'ON' if args.resume else 'OFF'}")
    print("=" * 70)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # ── 1. Get existing LLM movie IDs ──
    print("\n[1/6] Finding existing LLM movies...")
    cur.execute("""
        SELECT id FROM movies
        WHERE emotion_tags IS NOT NULL
        AND EXISTS (
            SELECT 1 FROM jsonb_each_text(emotion_tags) kv
            WHERE kv.value::float > 0.7
        )
    """)
    existing_llm_ids = [r[0] for r in cur.fetchall()]
    print(f"  Existing LLM movies: {len(existing_llm_ids)}")

    # ── 2. Get new top 1,000 movies ──
    print("\n[2/6] Finding new top movies to analyze...")
    existing_set = set(existing_llm_ids)
    placeholders = ','.join(['%s'] * len(existing_llm_ids))
    cur.execute(f"""
        SELECT id FROM movies
        WHERE id NOT IN ({placeholders})
        AND vote_count >= 30
        ORDER BY weighted_score DESC, popularity DESC
        LIMIT %s
    """, existing_llm_ids + [NEW_MOVIE_LIMIT])
    new_ids = [r[0] for r in cur.fetchall()]
    print(f"  New movies to analyze: {len(new_ids)}")

    # ── 2.5 Resume: filter out already-done movies ──
    all_ids = existing_llm_ids + new_ids
    already_done_ids = set()
    if args.resume:
        # Check which movies already have granular (new prompt) scores
        for i in range(0, len(all_ids), 500):
            chunk = all_ids[i:i+500]
            ph = ','.join(['%s'] * len(chunk))
            cur.execute(f"""
                SELECT id, emotion_tags FROM movies
                WHERE id IN ({ph}) AND emotion_tags IS NOT NULL
            """, chunk)
            for r in cur.fetchall():
                if r[1] and is_new_prompt_analyzed(r[1]):
                    already_done_ids.add(r[0])

        if already_done_ids:
            all_ids = [mid for mid in all_ids if mid not in already_done_ids]
            print(f"\n  [Resume] Already done with new prompt: {len(already_done_ids)}")
            print(f"  [Resume] Remaining to process: {len(all_ids)}")

    total = len(all_ids)
    if total == 0:
        print("\n  All movies already analyzed! Nothing to do.")
        cur.close()
        conn.close()
        return

    # ── 3. Fetch all movie data ──
    print(f"\n[3/6] Fetching data for {total} movies...")

    all_movies = {}
    # Fetch in chunks to avoid query size limits
    for i in range(0, len(all_ids), 500):
        chunk = all_ids[i:i+500]
        ph = ','.join(['%s'] * len(chunk))
        cur.execute(f"""
            SELECT m.id, m.title, m.title_ko, m.overview,
                   ARRAY_AGG(DISTINCT g.name) FILTER (WHERE g.name IS NOT NULL) as genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE m.id IN ({ph})
            GROUP BY m.id, m.title, m.title_ko, m.overview
        """, chunk)
        for r in cur.fetchall():
            all_movies[r[0]] = {
                'id': r[0], 'title': r[1], 'title_ko': r[2],
                'overview': r[3], 'genres': r[4] or []
            }
    print(f"  Fetched: {len(all_movies)} movies")

    # ── 4. Process with LLM ──
    print(f"\n[4/6] Running LLM analysis ({total} movies in {(total+BATCH_SIZE-1)//BATCH_SIZE} batches)...")

    movies_list = [all_movies[mid] for mid in all_ids if mid in all_movies]
    total_batches = (len(movies_list) + BATCH_SIZE - 1) // BATCH_SIZE

    all_results = {}
    total_input_tokens = 0
    total_output_tokens = 0
    failed_count = 0
    start_time = time.time()

    for i in range(0, len(movies_list), BATCH_SIZE):
        batch = movies_list[i:i+BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        elapsed = time.time() - start_time

        # Progress with ETA
        if batch_num > 1:
            avg_per_batch = elapsed / (batch_num - 1)
            remaining = avg_per_batch * (total_batches - batch_num + 1)
            eta_min = int(remaining // 60)
            eta_sec = int(remaining % 60)
            eta_str = f"ETA {eta_min}m{eta_sec}s"
        else:
            eta_str = "calculating..."

        # Print progress every 10 batches or first 5
        if batch_num <= 5 or batch_num % 10 == 0 or batch_num == total_batches:
            print(f"  Batch {batch_num:3d}/{total_batches} ({len(all_results):4d} done, {failed_count} failed) [{eta_str}]")

        results, inp_tok, out_tok = analyze_batch(batch)
        all_results.update(results)
        total_input_tokens += inp_tok
        total_output_tokens += out_tok

        if len(results) < len(batch):
            failed_count += len(batch) - len(results)

        # ── Immediate DB save after each batch ──
        if results:
            batch_updates = [(json.dumps(scores), mid) for mid, scores in results.items()]
            execute_batch(
                cur,
                "UPDATE movies SET emotion_tags = %s::jsonb WHERE id = %s",
                batch_updates,
                page_size=100
            )
            conn.commit()

        # Rate limiting: 1s between calls
        if i + BATCH_SIZE < len(movies_list):
            time.sleep(1)

    elapsed_total = time.time() - start_time
    print(f"\n  Completed in {int(elapsed_total//60)}m {int(elapsed_total%60)}s")
    print(f"  Success: {len(all_results)}/{len(movies_list)} movies")
    print(f"  Failed: {failed_count}")

    # ── 5. Summary ──
    print(f"\n[5/6] DB updates already saved (batch-by-batch)")
    print(f"  Total updated: {len(all_results)} movies")

    # ── 6. Statistics ──
    print(f"\n[6/6] Final Statistics")
    print("=" * 70)

    # Overall counts
    cur.execute("SELECT COUNT(*) FROM movies WHERE emotion_tags IS NOT NULL AND emotion_tags != '{}'::jsonb")
    total_with_tags = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM movies
        WHERE emotion_tags IS NOT NULL
        AND EXISTS (SELECT 1 FROM jsonb_each_text(emotion_tags) kv WHERE kv.value::float > 0.7)
    """)
    llm_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM movies")
    total_movies = cur.fetchone()[0]

    print(f"\n  Total movies:        {total_movies:,}")
    print(f"  With emotion_tags:   {total_with_tags:,} ({total_with_tags/total_movies*100:.1f}%)")
    print(f"  LLM analyzed (>0.7): {llm_count:,}")
    print(f"  Keyword-based:       {total_with_tags - llm_count:,}")

    # Per-cluster distribution for LLM movies
    print(f"\n  Cluster Score Distribution (LLM movies only):")
    print(f"  {'Cluster':10s} {'1.0':>5s} {'0.8-0.9':>8s} {'0.5-0.7':>8s} {'0.1-0.4':>8s} {'0.0':>5s}")
    print(f"  {'─'*50}")

    for c in CLUSTERS:
        cur.execute(f"""
            SELECT
                COUNT(*) FILTER (WHERE (emotion_tags->>'{c}')::float = 1.0),
                COUNT(*) FILTER (WHERE (emotion_tags->>'{c}')::float >= 0.8 AND (emotion_tags->>'{c}')::float < 1.0),
                COUNT(*) FILTER (WHERE (emotion_tags->>'{c}')::float >= 0.5 AND (emotion_tags->>'{c}')::float < 0.8),
                COUNT(*) FILTER (WHERE (emotion_tags->>'{c}')::float > 0 AND (emotion_tags->>'{c}')::float < 0.5),
                COUNT(*) FILTER (WHERE (emotion_tags->>'{c}')::float = 0 OR emotion_tags->>'{c}' IS NULL)
            FROM movies
            WHERE emotion_tags IS NOT NULL
            AND EXISTS (SELECT 1 FROM jsonb_each_text(emotion_tags) kv WHERE kv.value::float > 0.7)
        """)
        r = cur.fetchone()
        print(f"  {c:10s} {r[0]:5d} {r[1]:8d} {r[2]:8d} {r[3]:8d} {r[4]:5d}")

    # Cost calculation
    # Claude Sonnet pricing: $3/M input, $15/M output
    input_cost = total_input_tokens * 3.0 / 1_000_000
    output_cost = total_output_tokens * 15.0 / 1_000_000
    total_cost = input_cost + output_cost

    print(f"\n  API Cost:")
    print(f"  Input tokens:  {total_input_tokens:>10,} (${input_cost:.3f})")
    print(f"  Output tokens: {total_output_tokens:>10,} (${output_cost:.3f})")
    print(f"  Total cost:    ${total_cost:.3f}")
    print(f"  Time elapsed:  {int(elapsed_total//60)}m {int(elapsed_total%60)}s")

    cur.close()
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
