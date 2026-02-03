"""
Data Loading Script for RecFlix
Loads movie data from CSV into PostgreSQL
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

import ast
import pandas as pd
from datetime import datetime
from sqlalchemy import text

from app.database import engine, SessionLocal, Base
from app.models import Movie, Genre, Person, Keyword, Country, GENRE_MAPPING
from app.models.movie import movie_genres, movie_cast, movie_keywords, movie_countries, similar_movies


def parse_list_string(value):
    """Parse string representation of list"""
    if pd.isna(value) or value == '[]' or value == '':
        return []
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return []


def parse_date(value):
    """Parse date string"""
    if pd.isna(value) or value == '':
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")


def load_genres(session):
    """Load predefined genres"""
    print("Loading genres...")
    genres = {}
    for name, name_ko in GENRE_MAPPING.items():
        genre = session.query(Genre).filter(Genre.name == name).first()
        if not genre:
            genre = Genre(name=name, name_ko=name_ko)
            session.add(genre)
            session.flush()
        genres[name] = genre
    session.commit()
    print(f"Loaded {len(genres)} genres")
    return genres


def load_data(csv_path: str):
    """Load movie data from CSV"""
    print(f"Loading data from {csv_path}...")

    # Read CSV
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    print(f"Found {len(df)} movies in CSV")

    session = SessionLocal()

    try:
        # Load genres first
        genre_cache = load_genres(session)

        # Caches for entities
        person_cache = {}
        keyword_cache = {}
        country_cache = {}
        movie_ids = set()

        # First pass: collect all unique entities
        print("Collecting unique entities...")
        all_persons = set()
        all_keywords = set()
        all_countries = set()

        for _, row in df.iterrows():
            # Collect cast and directors
            cast_list = parse_list_string(row.get('cast', '[]'))
            for person in cast_list:
                all_persons.add(person)

            director = row.get('director', '')
            if pd.notna(director) and director:
                all_persons.add(director)

            # Collect keywords
            keywords_list = parse_list_string(row.get('keywords', '[]'))
            for kw in keywords_list:
                all_keywords.add(kw)

            # Collect countries
            countries_list = parse_list_string(row.get('production_countries', '[]'))
            for country in countries_list:
                all_countries.add(country)

        # Bulk insert persons
        print(f"Inserting {len(all_persons)} persons...")
        for name in all_persons:
            if name:
                person = Person(name=name)
                session.add(person)
                session.flush()
                person_cache[name] = person
        session.commit()

        # Bulk insert keywords
        print(f"Inserting {len(all_keywords)} keywords...")
        for name in all_keywords:
            if name:
                keyword = Keyword(name=name)
                session.add(keyword)
                session.flush()
                keyword_cache[name] = keyword
        session.commit()

        # Bulk insert countries
        print(f"Inserting {len(all_countries)} countries...")
        for name in all_countries:
            if name:
                country = Country(name=name)
                session.add(country)
                session.flush()
                country_cache[name] = country
        session.commit()

        # Second pass: insert movies
        print("Inserting movies...")
        similar_movie_data = []  # Store for later processing

        for idx, row in df.iterrows():
            movie_id = int(row['id'])
            movie_ids.add(movie_id)

            # Create movie
            movie = Movie(
                id=movie_id,
                title=row.get('title', ''),
                title_ko=row.get('title_ko', ''),
                certification=row.get('certification', '') if pd.notna(row.get('certification')) else None,
                runtime=int(row['runtime']) if pd.notna(row.get('runtime')) and row['runtime'] > 0 else None,
                vote_average=float(row['vote_average']) if pd.notna(row.get('vote_average')) else 0.0,
                vote_count=int(row['vote_count']) if pd.notna(row.get('vote_count')) else 0,
                overview=row.get('overview', '') if pd.notna(row.get('overview')) else None,
                overview_ko=row.get('overview-ko', '') if pd.notna(row.get('overview-ko')) else None,
                tagline=row.get('tagline', '') if pd.notna(row.get('tagline')) else None,
                release_date=parse_date(row.get('release_date')),
                popularity=float(row['popularity']) if pd.notna(row.get('popularity')) else 0.0,
                poster_path=row.get('poster_path', '') if pd.notna(row.get('poster_path')) else None,
                overview_lang=row.get('overview_lang', '') if pd.notna(row.get('overview_lang')) else None,
                is_adult=row.get('is_adult', False) == True or row.get('is_adult', 'False') == 'True',
            )
            session.add(movie)
            session.flush()

            # Add genres
            genres_list = parse_list_string(row.get('genres', '[]'))
            for genre_name in genres_list:
                if genre_name in genre_cache:
                    movie.genres.append(genre_cache[genre_name])

            # Add cast (actors) - avoid duplicates
            cast_list = parse_list_string(row.get('cast', '[]'))
            added_persons = set()
            for person_name in cast_list:
                if person_name in person_cache and person_name not in added_persons:
                    movie.cast_members.append(person_cache[person_name])
                    added_persons.add(person_name)

            # Add director (if not already added as actor)
            director = row.get('director', '')
            if pd.notna(director) and director and director in person_cache:
                if director not in added_persons:
                    movie.cast_members.append(person_cache[director])

            # Add keywords
            keywords_list = parse_list_string(row.get('keywords', '[]'))
            for kw in keywords_list:
                if kw in keyword_cache:
                    movie.keywords.append(keyword_cache[kw])

            # Add countries
            countries_list = parse_list_string(row.get('production_countries', '[]'))
            for country in countries_list:
                if country in country_cache:
                    movie.countries.append(country_cache[country])

            # Store similar movie IDs for later
            similar_ids = parse_list_string(row.get('similar_movie_ids', '[]'))
            if similar_ids:
                similar_movie_data.append((movie_id, similar_ids))

            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1}/{len(df)} movies...")
                session.commit()

        session.commit()
        print(f"Inserted {len(df)} movies")

        # Third pass: add similar movie relationships
        print("Adding similar movie relationships...")
        similar_count = 0
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        for movie_id, similar_ids in similar_movie_data:
            for similar_id in similar_ids:
                if similar_id in movie_ids:
                    stmt = pg_insert(similar_movies).values(
                        movie_id=movie_id,
                        similar_movie_id=similar_id
                    ).on_conflict_do_nothing()
                    session.execute(stmt)
                    similar_count += 1

        session.commit()
        print(f"Added {similar_count} similar movie relationships")

        print("\nData loading complete!")
        print_stats(session)

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


def print_stats(session):
    """Print database statistics"""
    print("\n=== Database Statistics ===")
    print(f"Movies: {session.query(Movie).count()}")
    print(f"Genres: {session.query(Genre).count()}")
    print(f"Persons: {session.query(Person).count()}")
    print(f"Keywords: {session.query(Keyword).count()}")
    print(f"Countries: {session.query(Country).count()}")


def reset_database():
    """Drop and recreate all tables"""
    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete!")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Load movie data into RecFlix database')
    parser.add_argument('--reset', action='store_true', help='Reset database before loading')
    parser.add_argument('--csv', default='data/raw/MOVIE_FINAL_FIXED_TITLES.csv', help='Path to CSV file')
    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    if args.reset:
        reset_database()
    else:
        create_tables()

    load_data(args.csv)
