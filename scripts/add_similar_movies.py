"""
Add similar movie relationships
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

import ast
import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import SessionLocal
from app.models import Movie
from app.models.movie import similar_movies


def parse_list_string(value):
    """Parse string representation of list"""
    if pd.isna(value) or value == '[]' or value == '':
        return []
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []


def add_similar_movies(csv_path: str):
    """Add similar movie relationships"""
    print(f"Loading similar movies from {csv_path}...")

    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    session = SessionLocal()

    try:
        # Get all existing movie IDs
        movie_ids = set(row[0] for row in session.query(Movie.id).all())
        print(f"Found {len(movie_ids)} movies in database")

        # Collect similar movie data
        similar_movie_data = []
        for _, row in df.iterrows():
            movie_id = int(row['id'])
            if movie_id in movie_ids:
                similar_ids = parse_list_string(row.get('similar_movie_ids', '[]'))
                if similar_ids:
                    similar_movie_data.append((movie_id, similar_ids))

        # Add relationships
        print("Adding similar movie relationships...")
        similar_count = 0
        batch_size = 1000
        batch = []

        for movie_id, similar_ids in similar_movie_data:
            for similar_id in similar_ids:
                if similar_id in movie_ids:
                    batch.append({'movie_id': movie_id, 'similar_movie_id': similar_id})
                    similar_count += 1

                    if len(batch) >= batch_size:
                        stmt = pg_insert(similar_movies).values(batch).on_conflict_do_nothing()
                        session.execute(stmt)
                        session.commit()
                        batch = []
                        print(f"Processed {similar_count} relationships...")

        # Insert remaining batch
        if batch:
            stmt = pg_insert(similar_movies).values(batch).on_conflict_do_nothing()
            session.execute(stmt)
            session.commit()

        print(f"\nAdded {similar_count} similar movie relationships")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    add_similar_movies('data/raw/MOVIE_FINAL_FIXED_TITLES.csv')
