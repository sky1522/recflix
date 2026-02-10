"""
Migration Script: Add new columns to movies table
- director (VARCHAR 500)
- director_ko (VARCHAR 500)
- cast_ko (TEXT)
- production_countries_ko (TEXT)
- release_season (VARCHAR 10)
- weighted_score (FLOAT)

Usage:
  cd backend
  ./venv/Scripts/python.exe scripts/migrate_add_columns.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


ALTER_STATEMENTS = [
    "ALTER TABLE movies ADD COLUMN IF NOT EXISTS director VARCHAR(500)",
    "ALTER TABLE movies ADD COLUMN IF NOT EXISTS director_ko VARCHAR(500)",
    "ALTER TABLE movies ADD COLUMN IF NOT EXISTS cast_ko TEXT",
    "ALTER TABLE movies ADD COLUMN IF NOT EXISTS production_countries_ko TEXT",
    "ALTER TABLE movies ADD COLUMN IF NOT EXISTS release_season VARCHAR(10)",
    "ALTER TABLE movies ADD COLUMN IF NOT EXISTS weighted_score FLOAT DEFAULT 0.0",
]


def run_migration():
    print("=== Movies table migration: Add new columns ===\n")

    with engine.connect() as conn:
        # Check existing columns
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'movies'
            ORDER BY ordinal_position
        """))
        existing = {row[0] for row in result}
        print(f"Existing columns ({len(existing)}): {sorted(existing)}\n")

        new_columns = ['director', 'director_ko', 'cast_ko',
                       'production_countries_ko', 'release_season', 'weighted_score']
        to_add = [c for c in new_columns if c not in existing]

        if not to_add:
            print("All columns already exist. Nothing to do.")
            return

        print(f"Columns to add: {to_add}\n")

        for stmt in ALTER_STATEMENTS:
            col_name = stmt.split("IF NOT EXISTS ")[1].split(" ")[0]
            if col_name in to_add:
                print(f"  Adding column: {col_name} ... ", end="")
                conn.execute(text(stmt))
                print("OK")

        conn.commit()
        print(f"\nMigration complete. Added {len(to_add)} columns.")

        # Verify
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'movies'
            ORDER BY ordinal_position
        """))
        final = {row[0] for row in result}
        print(f"Final columns ({len(final)}): {sorted(final)}")


if __name__ == "__main__":
    run_migration()
