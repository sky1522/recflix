"""
Recommendation system constants and mapping data
"""

# Age rating group mapping
AGE_RATING_MAP = {
    "family": ["ALL", "G", "PG", "12"],
    "teen": ["ALL", "G", "PG", "PG-13", "12", "15"],
}

# Hybrid scoring weights (with mood) - tuned v2
WEIGHT_MBTI = 0.25
WEIGHT_WEATHER = 0.20
WEIGHT_MOOD = 0.30
WEIGHT_PERSONAL = 0.25

# Hybrid scoring weights (without mood)
WEIGHT_MBTI_NO_MOOD = 0.35
WEIGHT_WEATHER_NO_MOOD = 0.25
WEIGHT_PERSONAL_NO_MOOD = 0.40

# CF 모델 사용 시 가중치 (with mood + CF)
WEIGHT_MBTI_CF = 0.20
WEIGHT_WEATHER_CF = 0.15
WEIGHT_MOOD_CF = 0.25
WEIGHT_PERSONAL_CF = 0.15
WEIGHT_CF = 0.25

# CF 모델 사용 시 가중치 (without mood + CF)
WEIGHT_MBTI_NO_MOOD_CF = 0.25
WEIGHT_WEATHER_NO_MOOD_CF = 0.20
WEIGHT_PERSONAL_NO_MOOD_CF = 0.30
WEIGHT_CF_NO_MOOD = 0.25

# Quality correction range (weighted_score based)
QUALITY_BOOST_MIN = 0.85  # floor multiplier for ws=6.0
QUALITY_BOOST_MAX = 1.00  # ceiling multiplier for ws=max

# Mood to emotion_tags mapping
# DB 키 (7대 감성 클러스터): healing, tension, energy, romance, deep, fantasy, light
MOOD_EMOTION_MAPPING = {
    "relaxed": ["healing"],           # 편안한 → 힐링 (가족애/우정/성장/힐링)
    "tense": ["tension"],             # 긴장감 → 긴장감 (반전/추리/서스펜스/심리전)
    "excited": ["energy"],            # 신나는 → 에너지 (폭발/추격전/복수/히어로)
    "emotional": ["romance", "deep"], # 감성적인 → 로맨스+깊이 (첫사랑/이별 + 인생/철학)
    "imaginative": ["fantasy"],       # 상상력 → 판타지 (마법/우주/초능력/타임루프)
    "light": ["light"],               # 가벼운 → 라이트 (유머/일상/친구/패러디)
    "gloomy": ["deep", "healing"],    # 울적한 → 깊이+힐링 (카타르시스/펑펑 울고 싶을 때)
    "stifled": ["energy", "tension"], # 답답한 → 에너지+긴장감 (사이다/속이 뻥 뚫리는)
}

# Mood label mapping
MOOD_LABELS = {
    "relaxed": "#편안한",
    "tense": "#긴장감",
    "excited": "#신나는",
    "emotional": "#감성적인",
    "imaginative": "#상상력",
    "light": "#가벼운",
    "gloomy": "#울적한",
    "stifled": "#답답한",
}

# Mood section titles and descriptions
MOOD_SECTION_CONFIG = {
    "relaxed": {"title": "😌 편안한 기분일 때", "desc": "마음이 따뜻해지는 영화"},
    "tense": {"title": "😰 긴장감이 필요할 때", "desc": "손에 땀을 쥐게 하는 영화"},
    "excited": {"title": "😆 신나는 기분일 때", "desc": "에너지 넘치는 영화"},
    "emotional": {"title": "💕 감성적인 기분일 때", "desc": "감동이 밀려오는 영화"},
    "imaginative": {"title": "🔮 상상에 빠지고 싶을 때", "desc": "판타지 세계로 떠나는 영화"},
    "light": {"title": "😄 가볍게 보고 싶을 때", "desc": "부담 없이 즐기는 영화"},
    "gloomy": {"title": "😢 울적한 기분일 때", "desc": "눈물로 마음을 비우는 영화"},
    "stifled": {"title": "😤 답답할 때", "desc": "속이 뻥 뚫리는 사이다 영화"},
}

# Weather label mapping
WEATHER_LABELS = {
    "sunny": "#맑은날",
    "rainy": "#비오는날",
    "cloudy": "#흐린날",
    "snowy": "#눈오는날"
}

WEATHER_TITLES = {
    "sunny": "☀️ 맑은 날 추천",
    "rainy": "🌧️ 비 오는 날 추천",
    "cloudy": "☁️ 흐린 날 추천",
    "snowy": "❄️ 눈 오는 날 추천"
}
