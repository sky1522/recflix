"""
LLM-based emotion_tags generation using Claude API
Analyzes top 1,000 popular movies with Claude for precise emotion scoring

Clusters:
- healing: 가족애/우정/성장/힐링
- tension: 반전/추리/서스펜스/심리전
- energy: 폭발/추격전/복수/히어로
- romance: 첫사랑/이별/연인/운명
- deep: 인생/고독/실화/철학
- fantasy: 마법/우주/초능력/타임루프
- light: 유머/일상/친구/패러디
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import execute_batch
import anthropic

# Initialize Claude client
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

BATCH_SIZE = 10  # Movies per API call
MODEL = "claude-sonnet-4-20250514"  # Fast and cost-effective

SYSTEM_PROMPT = """You are a movie emotion analyst. For each movie, analyze its plot and genres to score 7 emotion clusters from 0.0 to 1.0.

CLUSTERS:
- healing (힐링): Family bonds, friendship, growth, warmth, comfort, heartwarming stories
- tension (긴장감): Plot twists, mystery, suspense, psychological thriller, mind games
- energy (에너지): Action, explosions, chase scenes, revenge, superheroes, intense combat
- romance (로맨스): Love stories, first love, breakups, destiny, emotional relationships
- deep (깊이): Life philosophy, solitude, true stories, social issues, existential themes
- fantasy (판타지): Magic, space, superpowers, time travel, mythical creatures, sci-fi worlds
- light (라이트): Comedy, humor, everyday life, parody, feel-good, lighthearted fun

SCORING GUIDE:
- 0.0: No relation to this cluster
- 0.3: Minor elements present
- 0.5: Moderate presence
- 0.7: Strong presence
- 1.0: Core theme of the movie

Return ONLY a JSON object with movie IDs as keys and score objects as values.
Example: {"12345": {"healing": 0.3, "tension": 0.8, "energy": 0.5, "romance": 0.1, "deep": 0.2, "fantasy": 0.0, "light": 0.0}}"""


def analyze_movies_batch(movies: List[Dict]) -> Dict[int, Dict[str, float]]:
    """Send a batch of movies to Claude for analysis"""

    # Build the prompt with movie details
    movies_text = []
    for m in movies:
        genres_str = ", ".join(m['genres']) if m['genres'] else "Unknown"
        overview = m['overview_ko'] or m['overview'] or "No description available"
        # Truncate long overviews
        if len(overview) > 500:
            overview = overview[:500] + "..."
        movies_text.append(f"ID: {m['id']}\nTitle: {m['title']}\nGenres: {genres_str}\nPlot: {overview}")

    user_prompt = f"""Analyze these {len(movies)} movies and return emotion cluster scores (0.0-1.0) for each:

{chr(10).join(movies_text)}

Return ONLY valid JSON with movie IDs as keys. No explanation needed."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}]
        )

        # Parse response
        content = response.content[0].text.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        # Convert string keys to int
        return {int(k): v for k, v in result.items()}

    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  Response: {content[:200]}...")
        return {}
    except Exception as e:
        print(f"  API error: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description='Generate emotion_tags using Claude API')
    parser.add_argument('--limit', type=int, default=1000, help='Number of movies to process')
    parser.add_argument('--test', action='store_true', help='Test mode with specific movies')
    parser.add_argument('--dry-run', action='store_true', help='Do not update database')
    args = parser.parse_args()

    print("=" * 60)
    print(f"LLM Emotion Tags Generator (limit={args.limit})")
    print("=" * 60)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # Get top movies by popularity
    if args.test:
        # Test mode: include specific movies
        print("\nTest mode: Including specific movies...")
        cur.execute('''
            SELECT m.id, m.title, m.overview, m.overview_ko,
                   ARRAY_AGG(DISTINCT g.name) FILTER (WHERE g.name IS NOT NULL) as genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE m.id IN (27205, 155, 157336, 24428)  -- Inception, Dark Knight, Interstellar, Avengers
               OR (m.vote_count >= 50 AND m.popularity > 0)
            GROUP BY m.id, m.title, m.overview, m.overview_ko
            ORDER BY
                CASE WHEN m.id IN (27205, 155, 157336, 24428) THEN 0 ELSE 1 END,
                m.popularity DESC
            LIMIT %s
        ''', (args.limit,))
    else:
        print(f"\nFetching top {args.limit} popular movies...")
        cur.execute('''
            SELECT m.id, m.title, m.overview, m.overview_ko,
                   ARRAY_AGG(DISTINCT g.name) FILTER (WHERE g.name IS NOT NULL) as genres
            FROM movies m
            LEFT JOIN movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN genres g ON mg.genre_id = g.id
            WHERE m.vote_count >= 50
            GROUP BY m.id, m.title, m.overview, m.overview_ko
            ORDER BY m.popularity DESC
            LIMIT %s
        ''', (args.limit,))

    rows = cur.fetchall()
    movies = [
        {'id': r[0], 'title': r[1], 'overview': r[2], 'overview_ko': r[3], 'genres': r[4]}
        for r in rows
    ]

    print(f"Found {len(movies)} movies to process")

    # Process in batches
    all_results = {}
    total_batches = (len(movies) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(movies), BATCH_SIZE):
        batch = movies[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        print(f"\nBatch {batch_num}/{total_batches}: Processing {len(batch)} movies...")
        for m in batch:
            # Handle encoding issues with non-ASCII titles
            try:
                print(f"  - {m['title']}")
            except UnicodeEncodeError:
                print(f"  - [ID: {m['id']}]")

        results = analyze_movies_batch(batch)
        all_results.update(results)

        print(f"  Got {len(results)} results")

        # Rate limiting
        if i + BATCH_SIZE < len(movies):
            time.sleep(1)  # 1 second between batches

    print(f"\n{'=' * 60}")
    print(f"Total processed: {len(all_results)} movies")
    print("=" * 60)

    # Show results for specific movies
    target_movies = {27205: 'Inception', 155: 'The Dark Knight', 157336: 'Interstellar', 24428: 'The Avengers'}
    print("\nSpecific Movie Results:")
    for mid, name in target_movies.items():
        if mid in all_results:
            print(f"\n{name}:")
            scores = all_results[mid]
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for k, v in sorted_scores:
                bar = "#" * int(v * 10)
                print(f"  {k:10}: {v:.2f} {bar}")

    # Update database
    if not args.dry_run and all_results:
        print(f"\nUpdating database...")
        updates = [(json.dumps(scores), mid) for mid, scores in all_results.items()]
        execute_batch(
            cur,
            "UPDATE movies SET emotion_tags = %s::jsonb WHERE id = %s",
            updates,
            page_size=100
        )
        conn.commit()
        print(f"Updated {len(updates)} movies")
    elif args.dry_run:
        print("\nDry run mode - database not updated")

    # Statistics
    if not args.dry_run:
        print("\n" + "=" * 60)
        print("Statistics (LLM-processed movies, score > 0.3):")
        print("=" * 60)

        movie_ids = list(all_results.keys())
        if movie_ids:
            placeholders = ','.join(['%s'] * len(movie_ids))
            for cluster in ['healing', 'tension', 'energy', 'romance', 'deep', 'fantasy', 'light']:
                cur.execute(f'''
                    SELECT COUNT(*) FROM movies
                    WHERE id IN ({placeholders})
                    AND (emotion_tags->>'{cluster}')::float > 0.3
                ''', movie_ids)
                count = cur.fetchone()[0]
                print(f"{cluster}: {count} movies")

    cur.close()
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
