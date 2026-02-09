"""
Regenerate emotion_tags with 7 emotion clusters
Based on keywords (English) and overview_ko (Korean)

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
from typing import Dict, List, Set

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import execute_batch

# ============================================================
# CLUSTER DEFINITIONS
# ============================================================

CLUSTER_KEYWORDS = {
    "healing": {
        # English keywords (가족/우정/성장 중심, 철학적 주제 제외)
        "en": {
            "family", "friendship", "coming of age", "growth", "bond",
            "father", "mother", "son", "daughter", "parent", "child", "sibling",
            "brother", "sister", "grandmother", "grandfather", "reunion",
            "forgiveness", "reconciliation", "support", "care", "love", "warmth",
            "hometown", "home", "comfort", "hope", "dream", "encourage",
            "pet", "dog", "cat", "animal", "nature", "countryside",
            "childhood", "memory", "nostalgia", "heartwarming"
        },
        # Korean keywords (가족/우정/성장 중심, deep과 겹치는 키워드 제거)
        "ko": {
            "가족", "우정", "성장", "힐링", "사랑", "따뜻", "감동",
            "아버지", "어머니", "아들", "딸", "부모", "형제", "자매",
            "할머니", "할아버지", "재회", "용서", "화해", "위로", "희망",
            "꿈", "고향", "집", "추억", "어린시절", "유년", "동물",
            "반려", "강아지", "고양이", "자연", "시골", "마음", "정",
            "우리", "함께", "행복", "웃음", "포근", "온기", "품"
        }
    },
    "tension": {
        "en": {
            "twist", "mystery", "suspense", "psychological", "thriller",
            "detective", "investigation", "crime", "murder", "killer",
            "serial killer", "conspiracy", "betrayal", "deception", "lies",
            "secret", "hidden", "puzzle", "clue", "evidence", "suspect",
            "chase", "escape", "trap", "hostage", "kidnapping", "ransom",
            "spy", "undercover", "infiltration", "surveillance", "paranoia",
            "mind game", "manipulation", "tension", "nerve", "anxiety",
            "dark", "sinister", "menace", "threat", "danger", "fear"
        },
        "ko": {
            "반전", "추리", "서스펜스", "심리", "스릴러", "미스터리",
            "범인", "수사", "형사", "탐정", "살인", "범죄", "음모",
            "배신", "거짓", "비밀", "숨겨진", "단서", "증거", "용의자",
            "추격", "탈출", "함정", "인질", "납치", "스파이", "잠입",
            "감시", "긴장", "공포", "위험", "두려움", "어둠", "의심",
            "진실", "거짓말", "속임수", "조작", "트릭"
        }
    },
    "energy": {
        "en": {
            "explosion", "action", "chase", "fight", "battle", "war",
            "revenge", "hero", "superhero", "villain", "combat", "martial arts",
            "gun", "weapon", "shoot", "violence", "destruction", "crash",
            "speed", "race", "car chase", "motorcycle", "adrenaline",
            "mission", "rescue", "save", "protect", "soldier", "warrior",
            "power", "strength", "muscle", "punch", "kick", "stunt",
            "epic", "intense", "explosive", "spectacular", "blockbuster"
        },
        "ko": {
            "폭발", "액션", "추격", "격투", "전투", "전쟁", "복수",
            "히어로", "슈퍼히어로", "영웅", "악당", "빌런", "무술",
            "총", "무기", "폭력", "파괴", "충돌", "속도", "레이스",
            "자동차", "오토바이", "아드레날린", "미션", "구출", "구조",
            "보호", "군인", "전사", "힘", "파워", "주먹", "스턴트",
            "대규모", "스펙터클", "블록버스터", "격렬", "강렬"
        }
    },
    "romance": {
        "en": {
            "romance", "love", "first love", "breakup", "lover", "couple",
            "destiny", "fate", "soulmate", "kiss", "date", "wedding",
            "marriage", "relationship", "affair", "passion", "desire",
            "heart", "longing", "yearning", "miss", "reunion",
            "confession", "proposal", "engagement", "honeymoon",
            "romantic", "sweet", "tender", "intimate", "emotional",
            "separation", "goodbye", "farewell", "tears", "heartbreak"
        },
        "ko": {
            "로맨스", "사랑", "첫사랑", "이별", "연인", "커플", "운명",
            "소울메이트", "키스", "데이트", "결혼", "웨딩", "관계",
            "열정", "욕망", "설렘", "그리움", "재회", "고백", "프러포즈",
            "약혼", "신혼", "로맨틱", "달콤", "애틋", "감성", "눈물",
            "슬픔", "아픔", "상처", "헤어짐", "만남", "인연", "사랑에"
        }
    },
    "deep": {
        "en": {
            "life", "death", "existence", "meaning", "philosophy", "solitude",
            "lonely", "isolation", "depression", "mental", "identity",
            "true story", "based on", "biography", "documentary", "history",
            "social", "political", "war", "poverty", "inequality", "justice",
            "humanity", "moral", "ethics", "conscience", "guilt", "redemption",
            "art", "artist", "music", "literature", "culture", "genius",
            "struggle", "overcome", "survival", "trauma", "healing"
        },
        "ko": {
            "인생", "삶", "죽음", "존재", "의미", "철학", "고독", "외로움",
            "우울", "정신", "정체성", "실화", "바탕", "전기", "다큐",
            "역사", "사회", "정치", "전쟁", "가난", "불평등", "정의",
            "인류", "도덕", "윤리", "양심", "죄책감", "구원", "예술",
            "예술가", "음악", "문학", "문화", "천재", "투쟁", "극복",
            "생존", "트라우마", "상처", "치유", "성찰", "깨달음"
        }
    },
    "fantasy": {
        "en": {
            "magic", "wizard", "witch", "spell", "sorcery", "supernatural",
            "space", "universe", "alien", "ufo", "planet", "galaxy", "star",
            "superpower", "telekinesis", "telepathy", "mutant", "power",
            "time travel", "time loop", "parallel", "dimension", "portal",
            "dragon", "monster", "creature", "mythical", "legend", "fairy",
            "fantasy", "imagination", "dream", "surreal", "otherworldly",
            "future", "dystopia", "utopia", "sci-fi", "cyberpunk", "robot"
        },
        "ko": {
            "마법", "마법사", "마녀", "주문", "초자연", "우주", "외계",
            "외계인", "행성", "은하", "별", "초능력", "염력", "텔레파시",
            "뮤턴트", "타임", "시간여행", "타임루프", "평행", "차원",
            "포탈", "용", "드래곤", "몬스터", "괴물", "신화", "전설",
            "요정", "판타지", "상상", "환상", "꿈", "초현실", "미래",
            "디스토피아", "유토피아", "SF", "사이버펑크", "로봇", "AI"
        }
    },
    "light": {
        "en": {
            "comedy", "humor", "funny", "joke", "laugh", "hilarious",
            "parody", "satire", "spoof", "silly", "goofy", "absurd",
            "daily", "everyday", "slice of life", "casual", "simple",
            "friend", "buddy", "hangout", "party", "fun", "enjoy",
            "quirky", "eccentric", "charming", "witty", "clever",
            "romantic comedy", "rom-com", "feel-good", "lighthearted",
            "adventure", "road trip", "vacation", "holiday"
        },
        "ko": {
            "코미디", "유머", "웃음", "개그", "웃긴", "코믹", "패러디",
            "풍자", "스푸프", "바보", "엉뚱", "황당", "일상", "소소",
            "친구", "동료", "놀이", "파티", "즐거움", "재미", "유쾌",
            "발랄", "상큼", "톡톡", "로맨틱코미디", "로코",
            "여행", "휴가", "모험", "소확행", "귀여운", "사랑스러운",
            "소동", "장난", "촌스러운", "밝은", "가벼운", "떠들썩", "해프닝",
            "엉망", "대소동", "난리", "시끌벅적", "왁자지껄", "허당", "실수"
        }
    }
}

# Genre boost mapping
GENRE_CLUSTER_BOOST = {
    "healing": ["가족", "애니메이션", "Family", "Animation"],  # 드라마 제거 (deep과 구분)
    "tension": ["스릴러", "미스터리", "범죄", "Thriller", "Mystery", "Crime"],
    "energy": ["액션", "모험", "SF", "Action", "Adventure", "Science Fiction"],
    "romance": ["로맨스", "멜로", "Romance"],
    "deep": ["드라마", "다큐멘터리", "전쟁", "역사", "Drama", "Documentary", "War", "History"],
    "fantasy": ["판타지", "SF", "Fantasy", "Science Fiction"],
    "light": ["코미디", "애니메이션", "가족", "Comedy", "Animation", "Family"]  # 가족 추가
}

# Negative keywords (감점 키워드) - 클러스터와 반대되는 키워드
NEGATIVE_KEYWORDS = {
    "healing": {
        "en": {"murder", "killing", "explosion", "terror", "crime", "conspiracy",
               "revenge", "massacre", "torture", "violence", "gore", "brutal"},
        "ko": {"살인", "폭발", "테러", "범죄", "음모", "복수", "학살", "고문",
               "폭력", "잔혹", "피", "시체", "죽음", "살해"}
    },
    "tension": {
        "en": {"comedy", "funny", "romantic", "heartwarming", "cute", "adorable"},
        "ko": {"코미디", "웃긴", "로맨틱", "따뜻", "귀여운", "사랑스러운", "유쾌"}
    },
    "energy": {
        "en": {"slow", "quiet", "meditative", "peaceful", "gentle", "subtle"},
        "ko": {"조용", "평화", "명상", "잔잔", "느린", "고요", "차분"}
    },
    "romance": {
        "en": {"murder", "horror", "gore", "monster", "zombie", "alien"},
        "ko": {"살인", "공포", "괴물", "좀비", "외계인", "시체", "피"}
    },
    "deep": {
        "en": {"silly", "goofy", "absurd", "parody", "slapstick"},
        "ko": {"바보", "엉뚱", "황당", "패러디", "슬랩스틱", "개그"}
    },
    "fantasy": {
        "en": {"documentary", "true story", "biography", "historical"},
        "ko": {"다큐", "실화", "전기", "역사적"}
    },
    "light": {
        "en": {"murder", "horror", "terror", "gore", "torture", "death", "tragedy"},
        "ko": {"살인", "공포", "테러", "잔혹", "고문", "죽음", "비극", "슬픔"}
    }
}

# Genre penalty (장르 페널티) - 클러스터와 어울리지 않는 장르
GENRE_PENALTY = {
    "healing": ["범죄", "스릴러", "공포", "Crime", "Thriller", "Horror"],
    "tension": ["가족", "애니메이션", "로맨스", "Family", "Animation", "Romance"],
    "energy": ["다큐멘터리", "멜로", "Documentary"],
    "romance": ["공포", "Horror"],
    "deep": ["애니메이션", "Animation"],
    "fantasy": ["다큐멘터리", "Documentary"],
    "light": ["공포", "스릴러", "Horror", "Thriller"]
}


def calculate_cluster_scores(keywords: List[str], overview_ko: str, genres: List[str]) -> Dict[str, float]:
    """Calculate scores for each emotion cluster"""
    scores = {}

    # Normalize inputs
    keywords_set = set(k.lower() for k in keywords) if keywords else set()
    overview_lower = overview_ko.lower() if overview_ko else ""
    genres_set = set(genres) if genres else set()

    for cluster, cluster_keywords in CLUSTER_KEYWORDS.items():
        score = 0.0
        match_count = 0

        # Check English keywords
        en_matches = keywords_set & cluster_keywords["en"]
        match_count += len(en_matches)

        # Check Korean keywords in overview
        ko_matches = sum(1 for kw in cluster_keywords["ko"] if kw in overview_lower)
        match_count += ko_matches

        # Genre boost (+0.15 per matching genre)
        genre_boost = 0
        if cluster in GENRE_CLUSTER_BOOST:
            genre_matches = genres_set & set(GENRE_CLUSTER_BOOST[cluster])
            genre_boost = len(genre_matches) * 0.15

        # Calculate base score
        if match_count > 0:
            # Linear scaling, cap at 1.0
            base_score = min(match_count / 10, 1.0)
            score = min(base_score + genre_boost, 1.0)
        else:
            score = genre_boost  # Only genre boost if no keyword matches

        # === PENALTY LOGIC ===
        penalty = 0.0

        # 1. Negative keywords penalty (-0.1 per match)
        if cluster in NEGATIVE_KEYWORDS:
            neg_kw = NEGATIVE_KEYWORDS[cluster]
            # English negative keywords
            neg_en_matches = keywords_set & neg_kw["en"]
            penalty += len(neg_en_matches) * 0.1
            # Korean negative keywords in overview
            neg_ko_matches = sum(1 for kw in neg_kw["ko"] if kw in overview_lower)
            penalty += neg_ko_matches * 0.1

        # 2. Genre penalty (-0.15 per mismatched genre)
        if cluster in GENRE_PENALTY:
            genre_penalty_matches = genres_set & set(GENRE_PENALTY[cluster])
            penalty += len(genre_penalty_matches) * 0.15

        # Apply penalty and ensure non-negative
        score = max(0.0, score - penalty)

        # Cap at MAX_KEYWORD_SCORE (0.7) to not compete with LLM scores
        score = min(score, 0.7)

        # Round to 2 decimal places
        scores[cluster] = round(score, 2)

    return scores


def main():
    print("=" * 60)
    print("Regenerating emotion_tags with 7 emotion clusters")
    print("(Keyword-based only, excluding LLM-processed movies)")
    print("Max score cap: 0.7")
    print("=" * 60)

    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # Get LLM-processed movie IDs (top 1000 by popularity)
    print("\nIdentifying LLM-processed movies to exclude...")
    cur.execute('''
        SELECT id FROM movies
        WHERE vote_count >= 50
        ORDER BY popularity DESC
        LIMIT 1000
    ''')
    llm_movie_ids = set(row[0] for row in cur.fetchall())
    print(f"Excluding {len(llm_movie_ids)} LLM-processed movies")

    # Get all movies EXCEPT LLM-processed ones
    print("\nFetching keyword-based movies...")
    llm_ids_str = ','.join(map(str, llm_movie_ids)) if llm_movie_ids else '0'
    cur.execute(f'''
        SELECT m.id, m.overview_ko,
               ARRAY_AGG(DISTINCT k.name) FILTER (WHERE k.name IS NOT NULL) as keywords,
               ARRAY_AGG(DISTINCT g.name) FILTER (WHERE g.name IS NOT NULL) as genres
        FROM movies m
        LEFT JOIN movie_keywords mk ON m.id = mk.movie_id
        LEFT JOIN keywords k ON mk.keyword_id = k.id
        LEFT JOIN movie_genres mg ON m.id = mg.movie_id
        LEFT JOIN genres g ON mg.genre_id = g.id
        WHERE m.id NOT IN ({llm_ids_str})
        GROUP BY m.id, m.overview_ko
    ''')

    movies = cur.fetchall()
    total = len(movies)
    print(f"Found {total} movies to process")

    # Process movies
    updates = []
    processed = 0

    for movie_id, overview_ko, keywords, genres in movies:
        scores = calculate_cluster_scores(
            keywords or [],
            overview_ko or "",
            genres or []
        )
        updates.append((json.dumps(scores), movie_id))
        processed += 1

        if processed % 5000 == 0:
            print(f"Processed {processed}/{total} movies...")

    print(f"\nUpdating database...")

    # Batch update
    execute_batch(
        cur,
        "UPDATE movies SET emotion_tags = %s::jsonb WHERE id = %s",
        updates,
        page_size=1000
    )

    conn.commit()
    print(f"Updated {processed} movies")

    # Verify results - specific movies
    print("\n" + "=" * 60)
    print("Verification - Specific Movies:")
    print("=" * 60)

    target_movies = ['Inception', 'The Dark Knight', 'Interstellar', 'Avengers']
    for movie_title in target_movies:
        cur.execute('''
            SELECT title, emotion_tags
            FROM movies
            WHERE title ILIKE %s
            ORDER BY vote_count DESC
            LIMIT 1
        ''', (f'%{movie_title}%',))
        row = cur.fetchone()
        if row:
            print(f"\n{row[0]}:")
            print(f"  {row[1]}")

    # Stats
    print("\n" + "=" * 60)
    print("Statistics:")
    print("=" * 60)

    for cluster in CLUSTER_KEYWORDS.keys():
        cur.execute(f'''
            SELECT COUNT(*) FROM movies
            WHERE (emotion_tags->>'{cluster}')::float > 0.3
        ''')
        count = cur.fetchone()[0]
        print(f"{cluster}: {count} movies with score > 0.3")

    cur.close()
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
