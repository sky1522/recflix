"""
Generate MBTI, Weather, and Emotion scores for movies
Rule-based scoring using genre and keyword mappings
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Movie, Genre, Keyword


# ============================================================
# MBTI Scoring Rules
# ============================================================
# Each MBTI type has preferences for certain genres and themes
MBTI_GENRE_WEIGHTS = {
    # Analysts (NT)
    'INTJ': {'SF': 0.30, '미스터리': 0.25, '스릴러': 0.20, '다큐멘터리': 0.15, '범죄': 0.15},
    'INTP': {'SF': 0.30, '미스터리': 0.25, '다큐멘터리': 0.20, '판타지': 0.15, '스릴러': 0.10},
    'ENTJ': {'액션': 0.25, '스릴러': 0.20, '범죄': 0.20, '드라마': 0.15, '역사': 0.15},
    'ENTP': {'코미디': 0.25, 'SF': 0.20, '모험': 0.20, '미스터리': 0.15, '액션': 0.10},

    # Diplomats (NF)
    'INFJ': {'드라마': 0.30, '판타지': 0.20, '미스터리': 0.15, '로맨스': 0.15, '다큐멘터리': 0.10},
    'INFP': {'판타지': 0.30, '드라마': 0.25, '로맨스': 0.20, '애니메이션': 0.15, '음악': 0.10},
    'ENFJ': {'드라마': 0.30, '로맨스': 0.20, '가족': 0.20, '역사': 0.15, '음악': 0.10},
    'ENFP': {'로맨스': 0.25, '모험': 0.25, '코미디': 0.20, '판타지': 0.15, '애니메이션': 0.10},

    # Sentinels (SJ)
    'ISTJ': {'역사': 0.25, '범죄': 0.20, '스릴러': 0.20, '다큐멘터리': 0.20, '전쟁': 0.15},
    'ISFJ': {'가족': 0.30, '드라마': 0.25, '로맨스': 0.20, '애니메이션': 0.15, '역사': 0.10},
    'ESTJ': {'액션': 0.25, '범죄': 0.20, '스릴러': 0.20, '전쟁': 0.20, '역사': 0.15},
    'ESFJ': {'로맨스': 0.25, '가족': 0.25, '코미디': 0.20, '드라마': 0.20, '음악': 0.10},

    # Explorers (SP)
    'ISTP': {'액션': 0.30, '스릴러': 0.25, 'SF': 0.20, '범죄': 0.15, '서부': 0.10},
    'ISFP': {'음악': 0.25, '로맨스': 0.25, '드라마': 0.20, '애니메이션': 0.15, '판타지': 0.15},
    'ESTP': {'액션': 0.35, '스릴러': 0.25, '모험': 0.20, '범죄': 0.15, '코미디': 0.10},
    'ESFP': {'코미디': 0.30, '음악': 0.25, '로맨스': 0.20, '모험': 0.15, '가족': 0.10},
}

# Keyword boosts for MBTI types
MBTI_KEYWORD_BOOSTS = {
    'INTJ': ['strategic', 'mastermind', 'intellectual', 'plot twist', 'conspiracy', 'genius'],
    'INTP': ['science', 'technology', 'philosophy', 'puzzle', 'logic', 'invention'],
    'ENTJ': ['leadership', 'power', 'ambition', 'success', 'corporate', 'war'],
    'ENTP': ['debate', 'innovation', 'satire', 'wit', 'unconventional', 'chaos'],
    'INFJ': ['spiritual', 'meaning', 'transformation', 'redemption', 'vision', 'empathy'],
    'INFP': ['dream', 'imagination', 'poetry', 'art', 'idealism', 'nature'],
    'ENFJ': ['inspiration', 'community', 'teaching', 'mentor', 'sacrifice', 'hope'],
    'ENFP': ['adventure', 'freedom', 'creativity', 'enthusiasm', 'possibility', 'magic'],
    'ISTJ': ['duty', 'tradition', 'honor', 'procedure', 'discipline', 'loyalty'],
    'ISFJ': ['family', 'caring', 'protection', 'home', 'nurturing', 'service'],
    'ESTJ': ['order', 'justice', 'military', 'organization', 'rules', 'authority'],
    'ESFJ': ['friendship', 'celebration', 'harmony', 'hospitality', 'community', 'wedding'],
    'ISTP': ['mechanic', 'survival', 'tool', 'motorcycle', 'combat', 'precision'],
    'ISFP': ['beauty', 'art', 'nature', 'music', 'emotion', 'sensory'],
    'ESTP': ['extreme', 'adrenaline', 'risk', 'sports', 'gambling', 'stunt'],
    'ESFP': ['party', 'performance', 'fun', 'dancing', 'celebrity', 'entertainment'],
}


# ============================================================
# Weather Scoring Rules
# ============================================================
WEATHER_GENRE_WEIGHTS = {
    'sunny': {'액션': 0.30, '모험': 0.30, '코미디': 0.25, '가족': 0.20, '애니메이션': 0.20},
    'rainy': {'드라마': 0.30, '로맨스': 0.25, '미스터리': 0.20, '스릴러': 0.15, '범죄': 0.10},
    'cloudy': {'드라마': 0.25, '스릴러': 0.20, '미스터리': 0.20, '범죄': 0.15, 'SF': 0.15},
    'snowy': {'로맨스': 0.30, '가족': 0.25, '판타지': 0.25, '애니메이션': 0.20, '드라마': 0.15},
}

WEATHER_KEYWORD_BOOSTS = {
    'sunny': ['summer', 'beach', 'adventure', 'road trip', 'outdoor', 'tropical', 'bright', 'vacation'],
    'rainy': ['rain', 'melancholy', 'cozy', 'introspective', 'london', 'seattle', 'noir', 'mystery'],
    'cloudy': ['urban', 'city', 'contemplative', 'gray', 'detective', 'moody', 'atmospheric'],
    'snowy': ['christmas', 'winter', 'snow', 'holiday', 'cozy', 'warm', 'fireplace', 'romance'],
}


# ============================================================
# Emotion Scoring Rules
# ============================================================
EMOTION_GENRE_WEIGHTS = {
    'healing': {'가족': 0.35, '애니메이션': 0.25, '코미디': 0.20, '로맨스': 0.15},
    'tension': {'스릴러': 0.40, '공포': 0.35, '범죄': 0.25, '미스터리': 0.20},
    'touching': {'드라마': 0.35, '로맨스': 0.25, '가족': 0.20, '전쟁': 0.15},
    'fun': {'코미디': 0.40, '액션': 0.25, '모험': 0.20, '애니메이션': 0.15},
    'horror': {'공포': 0.50, '스릴러': 0.25, '미스터리': 0.15},
    'excitement': {'로맨스': 0.35, '모험': 0.25, '판타지': 0.20, '음악': 0.15},
    'sadness': {'드라마': 0.35, '전쟁': 0.25, '로맨스': 0.20, '역사': 0.15},
}

EMOTION_KEYWORD_BOOSTS = {
    'healing': ['heartwarming', 'feel-good', 'uplifting', 'hope', 'friendship', 'nature', 'healing'],
    'tension': ['suspense', 'thriller', 'chase', 'escape', 'danger', 'survival', 'psychological'],
    'touching': ['tear-jerker', 'emotional', 'sacrifice', 'loss', 'love', 'family', 'farewell'],
    'fun': ['comedy', 'hilarious', 'parody', 'satire', 'slapstick', 'funny', 'witty'],
    'horror': ['horror', 'scary', 'ghost', 'demon', 'haunted', 'nightmare', 'monster', 'zombie'],
    'excitement': ['romance', 'first love', 'crush', 'dating', 'passion', 'chemistry'],
    'sadness': ['tragedy', 'death', 'grief', 'loss', 'farewell', 'depression', 'lonely'],
}


def calculate_mbti_scores(genres: list, keywords: list) -> dict:
    """Calculate MBTI compatibility scores based on genres and keywords"""
    scores = {mbti: 0.0 for mbti in MBTI_GENRE_WEIGHTS.keys()}

    # Genre-based scoring
    for mbti, genre_weights in MBTI_GENRE_WEIGHTS.items():
        for genre in genres:
            if genre in genre_weights:
                scores[mbti] += genre_weights[genre]

    # Keyword-based boosting
    keyword_lower = [kw.lower() for kw in keywords]
    for mbti, boost_keywords in MBTI_KEYWORD_BOOSTS.items():
        for boost_kw in boost_keywords:
            for kw in keyword_lower:
                if boost_kw in kw:
                    scores[mbti] += 0.05

    # Normalize to 0.0 - 1.0 range
    max_score = max(scores.values()) if scores.values() else 1.0
    if max_score > 0:
        scores = {k: round(min(v / max_score, 1.0), 2) for k, v in scores.items()}

    # Ensure minimum variance - add base score
    scores = {k: round(max(v, 0.1), 2) for k, v in scores.items()}

    return scores


def calculate_weather_scores(genres: list, keywords: list) -> dict:
    """Calculate weather compatibility scores"""
    scores = {weather: 0.0 for weather in WEATHER_GENRE_WEIGHTS.keys()}

    # Genre-based scoring
    for weather, genre_weights in WEATHER_GENRE_WEIGHTS.items():
        for genre in genres:
            if genre in genre_weights:
                scores[weather] += genre_weights[genre]

    # Keyword-based boosting
    keyword_lower = [kw.lower() for kw in keywords]
    for weather, boost_keywords in WEATHER_KEYWORD_BOOSTS.items():
        for boost_kw in boost_keywords:
            for kw in keyword_lower:
                if boost_kw in kw:
                    scores[weather] += 0.1

    # Normalize
    max_score = max(scores.values()) if scores.values() else 1.0
    if max_score > 0:
        scores = {k: round(min(v / max_score, 1.0), 2) for k, v in scores.items()}

    # Base score
    scores = {k: round(max(v, 0.2), 2) for k, v in scores.items()}

    return scores


def calculate_emotion_scores(genres: list, keywords: list) -> dict:
    """Calculate emotion tag scores"""
    scores = {emotion: 0.0 for emotion in EMOTION_GENRE_WEIGHTS.keys()}

    # Genre-based scoring
    for emotion, genre_weights in EMOTION_GENRE_WEIGHTS.items():
        for genre in genres:
            if genre in genre_weights:
                scores[emotion] += genre_weights[genre]

    # Keyword-based boosting
    keyword_lower = [kw.lower() for kw in keywords]
    for emotion, boost_keywords in EMOTION_KEYWORD_BOOSTS.items():
        for boost_kw in boost_keywords:
            for kw in keyword_lower:
                if boost_kw in kw:
                    scores[emotion] += 0.15

    # Normalize
    max_score = max(scores.values()) if scores.values() else 1.0
    if max_score > 0:
        scores = {k: round(min(v / max_score, 1.0), 2) for k, v in scores.items()}

    # Base score
    scores = {k: round(max(v, 0.1), 2) for k, v in scores.items()}

    return scores


def add_score_columns():
    """Add JSONB columns to movies table if they don't exist"""
    print("Adding score columns to movies table...")
    with engine.connect() as conn:
        # Check and add columns
        for column in ['mbti_scores', 'weather_scores', 'emotion_tags']:
            try:
                conn.execute(text(f"""
                    ALTER TABLE movies ADD COLUMN IF NOT EXISTS {column} JSONB DEFAULT '{{}}'::jsonb
                """))
                conn.commit()
            except Exception as e:
                print(f"Column {column} may already exist: {e}")
    print("Score columns ready!")


def generate_scores():
    """Generate scores for all movies"""
    print("Generating scores for all movies...")

    session = SessionLocal()

    try:
        # Get total count
        total = session.query(Movie).count()
        print(f"Processing {total} movies...")

        # Process in batches using raw SQL for JSONB update
        batch_size = 500
        processed = 0

        while processed < total:
            movies = session.query(Movie).offset(processed).limit(batch_size).all()

            for movie in movies:
                # Get genres
                genres = [g.name for g in movie.genres]

                # Get keywords
                keywords = [k.name for k in movie.keywords]

                # Calculate scores
                mbti_scores = calculate_mbti_scores(genres, keywords)
                weather_scores = calculate_weather_scores(genres, keywords)
                emotion_tags = calculate_emotion_scores(genres, keywords)

                # Update using raw SQL for reliable JSONB update
                import json
                session.execute(
                    text("""
                        UPDATE movies
                        SET mbti_scores = CAST(:mbti AS jsonb),
                            weather_scores = CAST(:weather AS jsonb),
                            emotion_tags = CAST(:emotion AS jsonb)
                        WHERE id = :movie_id
                    """),
                    {
                        'mbti': json.dumps(mbti_scores),
                        'weather': json.dumps(weather_scores),
                        'emotion': json.dumps(emotion_tags),
                        'movie_id': movie.id
                    }
                )

            session.commit()
            processed += len(movies)
            print(f"Processed {processed}/{total} movies...")

        print("\nScore generation complete!")

        # Refresh session for sample print
        session.expire_all()
        print_sample_scores(session)

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


def print_sample_scores(session):
    """Print sample scores for verification"""
    print("\n" + "=" * 60)
    print("Sample Scores")
    print("=" * 60)

    # Get a few popular movies
    samples = session.query(Movie).filter(
        Movie.vote_count > 100
    ).order_by(Movie.popularity.desc()).limit(5).all()

    for movie in samples:
        print(f"\n{movie.title_ko or movie.title}")
        print(f"  Genres: {[g.name for g in movie.genres]}")
        print(f"  Top MBTI: {sorted(movie.mbti_scores.items(), key=lambda x: x[1], reverse=True)[:3]}")
        print(f"  Weather: {movie.weather_scores}")
        print(f"  Emotions: {sorted(movie.emotion_tags.items(), key=lambda x: x[1], reverse=True)[:3]}")


def create_indexes():
    """Create GIN indexes for JSONB columns"""
    print("\nCreating indexes for score columns...")
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_movies_mbti ON movies USING GIN(mbti_scores)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_movies_weather ON movies USING GIN(weather_scores)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_movies_emotion ON movies USING GIN(emotion_tags)"))
            conn.commit()
            print("Indexes created!")
        except Exception as e:
            print(f"Index creation error: {e}")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Step 1: Add columns
    add_score_columns()

    # Step 2: Generate scores
    generate_scores()

    # Step 3: Create indexes
    create_indexes()
