"""
Template-based recommendation reason generator.
Produces a 1-2 sentence Korean reason string from recommendation tags and movie metadata.
No LLM calls — pure string template matching at zero cost and zero latency.
"""
import random

from app.models import Movie
from app.schemas.recommendation import RecommendationTag

# --- Korean label mappings ---

WEATHER_KO = {
    "sunny": "맑은 날",
    "rainy": "비 오는 날",
    "cloudy": "흐린 날",
    "snowy": "눈 오는 날",
}

MOOD_KO = {
    "relaxed": "편안한",
    "tense": "긴장감 넘치는",
    "excited": "신나는",
    "emotional": "감성적인",
    "imaginative": "상상력 자극하는",
    "light": "가벼운",
    "gloomy": "울적한",
    "stifled": "답답한",
}

# MBTI temperament groups
_NT = {"INTJ", "INTP", "ENTJ", "ENTP"}
_NF = {"INFJ", "INFP", "ENFJ", "ENFP"}
_SJ = {"ISTJ", "ISFJ", "ESTJ", "ESFJ"}
_SP = {"ISTP", "ISFP", "ESTP", "ESFP"}


def _primary_genre(movie: Movie) -> str:
    """Extract the first genre name from a movie."""
    if movie.genres:
        g = movie.genres[0]
        return g.name if hasattr(g, "name") else str(g)
    return "영화"


def _is_classic(movie: Movie) -> bool:
    """Check if a movie is a classic (released 10+ years ago)."""
    if movie.release_date:
        try:
            return int(str(movie.release_date)[:4]) <= 2016
        except (ValueError, TypeError):
            pass
    return False


def _is_recent(movie: Movie) -> bool:
    """Check if a movie was released in the last 3 years."""
    if movie.release_date:
        try:
            return int(str(movie.release_date)[:4]) >= 2024
        except (ValueError, TypeError):
            pass
    return False


# --- Template pools ---

def _compound_reason(
    tag_types: set[str],
    mbti: str | None,
    weather: str | None,
    mood: str | None,
    genre: str,
    vote_avg: float,
) -> str | None:
    """Try to build a compound (2+ signals) reason. Returns None if no match."""
    w_ko = WEATHER_KO.get(weather or "", "")
    m_ko = MOOD_KO.get(mood or "", "")

    if "mbti" in tag_types and weather and w_ko:
        return random.choice([
            f"{mbti}이(가) {w_ko}에 보면 더 좋은 영화",
            f"{w_ko}, {mbti} 성향에 어울리는 {genre}",
        ])
    if "mbti" in tag_types and mood and m_ko:
        return random.choice([
            f"{mbti}이(가) {m_ko} 기분일 때 딱 맞는 작품",
            f"{m_ko} 기분의 {mbti}를 위한 {genre}",
        ])
    if weather and w_ko and mood and m_ko:
        return f"{w_ko} {m_ko} 기분에 완벽한 선택이에요"
    if "personal" in tag_types and "rating" in tag_types:
        return "취향에 딱 맞으면서 평점도 높은 영화예요"
    if "mbti" in tag_types and "rating" in tag_types:
        return f"{mbti} 유형이 좋아하는 평점 {vote_avg:.1f}의 명작"
    return None


def _mood_reason(label: str) -> str:
    """Generate reason from a mood/personal tag label."""
    table: dict[str, list[str]] = {
        "#편안한": ["마음이 편안해지는 따뜻한 이야기예요"],
        "#긴장감": ["손에 땀을 쥐게 하는 긴장감이 매력이에요"],
        "#신나는": ["에너지 넘치는 액션으로 기분 전환!"],
        "#감성적인": ["감동이 밀려오는 깊은 이야기예요"],
        "#상상력": ["무한한 상상의 세계로 떠나보세요"],
        "#가벼운": ["부담 없이 가볍게 즐길 수 있어요"],
        "#울적한": ["눈물로 마음을 비우고 싶을 때 추천해요"],
        "#답답한": ["속이 뻥 뚫리는 사이다 같은 영화예요"],
    }
    return random.choice(table.get(label, ["당신의 기분에 어울리는 영화예요"]))


def _personal_reason(label: str, genre: str) -> str:
    """Generate reason from a personal preference tag."""
    if label == "#취향저격":
        return random.choice([
            f"좋아하시는 {genre} 장르의 숨겨진 보석이에요",
            "최근 찜한 영화와 비슷한 감성이에요",
        ])
    if label == "#비슷한영화":
        return "이전에 높게 평가한 영화와 비슷한 작품이에요"
    return "취향을 저격하는 영화예요"


def _mbti_reason(mbti: str, genre: str, score: float) -> str:
    """Generate reason from an MBTI tag."""
    if score > 0.7:
        specific: dict[str, list[str]] = {
            "INTJ": [f"INTJ 유형이 좋아하는 지적인 {genre} 영화예요"],
            "INTP": [f"분석적인 INTP에게 딱 맞는 {genre}"],
            "ENFP": [f"상상력 풍부한 ENFP를 위한 {genre}"],
            "INFJ": ["깊은 통찰을 즐기는 INFJ에게 추천해요"],
            "ENTJ": [f"ENTJ의 리더십 감각에 어울리는 {genre}"],
        }
        if mbti in specific:
            return random.choice(specific[mbti])

    # Temperament-based fallback
    if mbti in _NT:
        return random.choice([f"논리와 분석을 즐기는 {mbti}에게 딱이에요", f"{mbti} 유형의 취향을 저격하는 작품이에요"])
    if mbti in _NF:
        return random.choice([f"감성과 공감 능력이 뛰어난 {mbti}를 위한 영화", f"{mbti} 성향에 잘 맞는 영화예요"])
    if mbti in _SJ:
        return random.choice([f"안정과 질서를 중시하는 {mbti}에게 어울려요", f"{mbti} 성향에 잘 맞는 영화예요"])
    if mbti in _SP:
        return random.choice([f"즉흥적이고 활동적인 {mbti}가 좋아할 영화", f"{mbti} 성향에 잘 맞는 영화예요"])
    return f"{mbti} 성향에 잘 맞는 영화예요"


def _weather_reason(weather: str, genre: str) -> str:
    """Generate reason from a weather tag."""
    w_ko = WEATHER_KO.get(weather, weather)
    table: dict[str, dict[str, list[str]]] = {
        "rainy": {
            "드라마": ["비 오는 날 잔잔한 드라마를 보며 힐링해보세요"],
            "로맨스": ["빗소리와 함께 보면 더 감성적인 로맨스"],
            "스릴러": ["비 오는 밤, 긴장감 넘치는 스릴러 어때요?"],
        },
        "sunny": {
            "모험": ["화창한 날씨만큼 시원한 모험 영화"],
            "코미디": ["맑은 날 기분처럼 유쾌한 코미디"],
        },
        "cloudy": {
            "미스터리": ["흐린 날 분위기에 어울리는 미스터리"],
        },
        "snowy": {
            "애니메이션": ["눈 오는 날 따뜻하게 볼 애니메이션"],
            "가족": ["눈 내리는 날 가족과 함께 보기 좋은 영화"],
        },
    }
    specific = table.get(weather, {}).get(genre)
    if specific:
        return random.choice(specific)

    defaults: dict[str, str] = {
        "rainy": "비 내리는 날 감성에 어울리는 영화예요",
        "sunny": "맑은 날씨에 딱 맞는 기분 좋은 영화예요",
        "cloudy": "흐린 날 감성에 빠져볼 영화예요",
        "snowy": "눈 오는 날 포근하게 감싸주는 영화예요",
    }
    return defaults.get(weather, f"{w_ko}에 어울리는 영화예요")


def _quality_reason(movie: Movie) -> str:
    """Generate reason from a quality/rating tag."""
    va = movie.vote_average or 0.0
    if va >= 8.0:
        return f"평점 {va:.1f}의 압도적 명작이에요"
    if _is_classic(movie):
        return "시간이 지나도 빛나는 클래식 명작"
    if _is_recent(movie):
        return "최근 개봉한 화제작, 놓치지 마세요"
    return "높은 평점이 증명하는 수작이에요"


def generate_reason(
    tags: list[RecommendationTag],
    movie: Movie | None,
    mbti: str | None = None,
    weather: str | None = None,
    mood: str | None = None,
) -> str:
    """
    Generate a 1-sentence Korean recommendation reason from tags and context.

    Priority: compound > mood/personal > mbti > weather > quality > fallback.
    """
    if not movie:
        return ""

    genre = _primary_genre(movie)
    vote_avg = movie.vote_average or 0.0
    tag_types = {t.type for t in tags}

    # 1. Compound conditions (2+ signals)
    compound = _compound_reason(tag_types, mbti, weather, mood, genre, vote_avg)
    if compound:
        return compound

    # 2. Sort tags by priority then score
    priority = {"personal": 0, "mbti": 1, "weather": 2, "rating": 3}
    sorted_tags = sorted(tags, key=lambda t: (priority.get(t.type, 9), -(t.score or 0)))

    for tag in sorted_tags:
        if tag.type == "personal":
            if tag.label in MOOD_KO.values() or tag.label.startswith("#") and any(
                tag.label == v for v in ["#편안한", "#긴장감", "#신나는", "#감성적인", "#상상력", "#가벼운", "#울적한", "#답답한"]
            ):
                return _mood_reason(tag.label)
            return _personal_reason(tag.label, genre)
        if tag.type == "mbti" and mbti:
            return _mbti_reason(mbti, genre, tag.score or 0.0)
        if tag.type == "weather" and weather:
            return _weather_reason(weather, genre)
        if tag.type == "rating":
            return _quality_reason(movie)

    return ""
