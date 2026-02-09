# RecFlix 추천 시스템 로직

> 마지막 업데이트: 2026-02-09

---

## 0. 품질 필터 (Quality Filter)

모든 추천 섹션에 최소 품질 필터가 적용됩니다:

```python
# 기본 품질 필터
vote_count >= 30      # 최소 30표 이상
vote_average >= 5.0   # 평점 5.0 이상
```

| 섹션 | vote_count | vote_average |
|------|------------|--------------|
| 기분별 추천 | >= 30 | >= 5.0 |
| 인기 영화 | >= 30 | >= 5.0 |
| 날씨별 추천 | >= 30 | >= 5.0 |
| MBTI 추천 | >= 30 | >= 5.0 |
| 높은 평점 | >= 100 | >= 5.0 |
| Hybrid 맞춤 | >= 30 | >= 5.0 |

---

## 1. 데이터베이스 구조

### Movie 테이블의 Score 컬럼 (JSONB)

```sql
-- movies 테이블
mbti_scores    JSONB   -- 16개 MBTI 유형별 점수 (0.0 ~ 1.0)
weather_scores JSONB   -- 4개 날씨별 점수 (0.0 ~ 1.0)
emotion_tags   JSONB   -- 7개 감정 태그별 점수 (0.0 ~ 1.0)
```

**예시 데이터:**
```json
{
  "mbti_scores": {"INTJ": 0.85, "ENFP": 0.72, ...},
  "weather_scores": {"sunny": 0.90, "rainy": 0.30, ...},
  "emotion_tags": {"healing": 0.75, "tension": 0.20, ...}
}
```

---

## 2. emotion_tags 점수 생성 (2-Tier 시스템)

### 2.1 개요

emotion_tags는 두 가지 방식으로 생성됩니다:

| 방식 | 대상 | 영화 수 | 최대 점수 |
|------|------|--------|----------|
| **LLM 분석** | 인기 상위 1,000편 | 1,000 | 1.0 |
| **키워드 기반** | 나머지 영화 | 31,625 | **0.7** (상한) |

### 2.2 LLM 분석 (Claude API)

인기 상위 1,000편 (vote_count >= 50, popularity DESC)에 대해 Claude API로 정밀 분석:

```python
# 스크립트: backend/scripts/llm_emotion_tags.py
# 모델: claude-sonnet-4-20250514
# 배치: 10편씩 묶어서 API 호출

# 입력: 영화 제목, 장르, 줄거리 (overview_ko)
# 출력: 7개 클러스터별 점수 (0.0 ~ 1.0)
```

**LLM 분석 결과 예시:**
| 영화 | 1위 | 2위 | 3위 |
|------|-----|-----|-----|
| 인셉션 | tension: 0.90 | fantasy: 0.90 | deep: 0.80 |
| 다크 나이트 | tension: 0.80 | energy: 0.70 | deep: 0.70 |
| 인터스텔라 | deep: 0.80 | fantasy: 0.80 | tension: 0.50 |
| 어벤저스 | energy: 1.00 | fantasy: 0.80 | tension: 0.50 |

### 2.3 키워드 기반 점수 (나머지 영화)

```python
# 스크립트: backend/scripts/regenerate_emotion_tags.py

# 점수 공식
score = min(base_score + genre_boost - penalty, 0.7)  # 0.7 상한

# Base Score: 키워드 매칭
base_score = min(match_count / 10, 1.0)
match_count = 영어 키워드 매칭 수 + 한국어 키워드 매칭 수

# Genre Boost: +0.15/장르
genre_boost = 매칭 장르 수 × 0.15

# Penalty: 네거티브 키워드 + 장르 페널티
penalty = (neg_keyword_count × 0.1) + (bad_genre_count × 0.15)
```

### 2.4 7대 감성 클러스터 정의

| 클러스터 | 한국어 | 키워드 정의 | 부스트 장르 |
|---------|--------|------------|------------|
| healing | 힐링 | 가족애/우정/성장/힐링 | 가족, 애니메이션 |
| tension | 긴장감 | 반전/추리/서스펜스/심리전 | 스릴러, 미스터리, 범죄 |
| energy | 에너지 | 폭발/추격전/복수/히어로 | 액션, 모험, SF |
| romance | 로맨스 | 첫사랑/이별/연인/운명 | 로맨스, 멜로 |
| deep | 깊이 | 인생/고독/실화/철학 | 드라마, 다큐, 전쟁, 역사 |
| fantasy | 판타지 | 마법/우주/초능력/타임루프 | 판타지, SF |
| light | 라이트 | 유머/일상/친구/패러디 | 코미디, 애니메이션, 가족 |

### 2.5 네거티브 키워드 & 장르 페널티

**네거티브 키워드 (-0.1/개):**
| 클러스터 | 감점 키워드 |
|---------|------------|
| healing | 살인, 폭발, 테러, 범죄, 음모, 복수, 학살, 고문 |
| light | 살인, 공포, 테러, 잔혹, 고문, 죽음, 비극 |
| tension | 코미디, 웃긴, 로맨틱, 따뜻, 귀여운 |

**장르 페널티 (-0.15/개):**
| 클러스터 | 감점 장르 |
|---------|----------|
| healing | 범죄, 스릴러, 공포 |
| tension | 가족, 애니메이션, 로맨스 |
| light | 공포, 스릴러 |

### 2.6 클러스터별 영화 수 (score > 0.3)

| 클러스터 | LLM (1,000편) | 키워드 (31,625편) |
|---------|--------------|-----------------|
| healing | 254 | 4,813 |
| tension | 700 | 3,802 |
| energy | 668 | 2,847 |
| romance | 179 | 2,336 |
| deep | 414 | 4,114 |
| fantasy | 414 | 1,945 |
| light | 289 | 2,728 |

---

## 3. 추천 쿼리 (30% LLM 보장)

### 3.1 혼합 정렬 로직

```python
# backend/app/api/v1/recommendations.py - get_movies_by_score()

def get_movies_by_score(..., llm_min_ratio=0.3):
    # 1. LLM 영화 ID 조회 (상위 1,000편)
    llm_ids = get_llm_movie_ids(db)

    # 2. 확장 풀에서 영화 조회
    extended_pool = pool_size * 2

    # 3. LLM/키워드 분리
    llm_movies = [m for m in results if m.id in llm_ids]
    kw_movies = [m for m in results if m.id not in llm_ids]

    # 4. 최소 LLM 비율 보장 (30%)
    min_llm_count = int(pool_size * llm_min_ratio)  # 12개
    selected = llm_movies[:min_llm_count]

    # 5. 나머지는 점수순으로 채움
    remaining = pool_size - len(selected)
    all_remaining = llm_movies[min_llm_count:] + kw_movies
    all_remaining.sort(by=score, desc=True)
    selected.extend(all_remaining[:remaining])

    return selected
```

### 3.2 상위 20개 분포 (시뮬레이션)

| 클러스터 | LLM | 키워드 | 점수 범위 |
|---------|-----|--------|----------|
| healing | 12/20 | 8/20 | 0.70 - 1.00 |
| tension | 12/20 | 0/20 | 1.00 - 1.00 |
| energy | 12/20 | 1/20 | 1.00 - 1.00 |
| romance | 12/20 | 0/20 | 1.00 - 1.00 |
| deep | 12/20 | 0/20 | 0.90 - 1.00 |
| fantasy | 12/20 | 0/20 | 1.00 - 1.00 |
| light | 12/20 | 0/20 | 1.00 - 1.00 |

---

## 4. MBTI 추천 로직

### 4.1 지원 유형 (16개)

| 분류 | 유형 |
|------|------|
| 분석형 | INTJ, INTP, ENTJ, ENTP |
| 외교형 | INFJ, INFP, ENFJ, ENFP |
| 관리형 | ISTJ, ISFJ, ESTJ, ESFJ |
| 탐험형 | ISTP, ISFP, ESTP, ESFP |

### 4.2 Hybrid 스코어링에서의 MBTI

```python
# 가중치: 30% (mood 있을 때) / 35% (mood 없을 때)
mbti_score = movie.mbti_scores.get(mbti, 0.0)

# 태그 표시 조건: score > 0.5
if mbti_score > 0.5:
    tags.append("#INTJ추천")
```

---

## 5. Weather (날씨) 추천 로직

### 5.1 지원 날씨 (4개)

| 코드 | 한국어 | 아이콘 | 설명 |
|------|--------|--------|------|
| sunny | 맑음 | ☀️ | 밝고 활기찬 영화 |
| rainy | 비 | 🌧️ | 잔잔하고 감성적인 영화 |
| cloudy | 흐림 | ☁️ | 생각에 잠기게 하는 영화 |
| snowy | 눈 | ❄️ | 따뜻하고 포근한 영화 |

### 5.2 Hybrid 스코어링에서의 Weather

```python
# 가중치: 20% (mood 있을 때) / 25% (mood 없을 때)
weather_score = movie.weather_scores.get(weather, 0.0)

# 태그 표시 조건: score > 0.5
if weather_score > 0.5:
    tags.append("#비오는날")
```

---

## 6. Mood (기분) 추천 로직

### 6.1 지원 기분 (6개, 2x3 그리드)

**1행:**
| 코드 | 이모지 | 한국어 | emotion_tags 매핑 |
|------|--------|--------|-------------------|
| relaxed | 😌 | 편안한 | healing |
| tense | 😰 | 긴장감원해 | tension |
| excited | 😆 | 신나는 | energy |

**2행:**
| 코드 | 이모지 | 한국어 | emotion_tags 매핑 |
|------|--------|--------|-------------------|
| emotional | 💕 | 감성적인 | romance, deep |
| imaginative | 🔮 | 상상에빠지고싶은 | fantasy |
| light | 😄 | 가볍게볼래 | light |

### 6.2 기분 → emotion_tags 매핑

```python
MOOD_EMOTION_MAPPING = {
    "relaxed": ["healing"],           # 편안한 → 힐링
    "tense": ["tension"],             # 긴장감 → 긴장감
    "excited": ["energy"],            # 신나는 → 에너지
    "emotional": ["romance", "deep"], # 감성적인 → 로맨스+깊이
    "imaginative": ["fantasy"],       # 상상력 → 판타지
    "light": ["light"],               # 가벼운 → 라이트
}
```

### 6.3 Hybrid 스코어링에서의 Mood

```python
# 가중치: 20% (mood 있을 때만)
# 여러 emotion key가 있을 경우 평균 계산
emotion_keys = MOOD_EMOTION_MAPPING.get(mood, [])
emotion_values = [movie.emotion_tags.get(key) for key in emotion_keys]
mood_score = sum(emotion_values) / len(emotion_values)

# 태그 표시 조건: score > 0.5
if mood_score > 0.5:
    tags.append("#긴장감")
```

---

## 7. Hybrid (종합) 추천 로직

### 7.1 가중치 구성

**Mood 있을 때:**
```
Hybrid Score = (0.30 × MBTI) + (0.20 × Weather) + (0.20 × Mood) + (0.30 × Personal)
```

**Mood 없을 때:**
```
Hybrid Score = (0.35 × MBTI) + (0.25 × Weather) + (0.40 × Personal)
```

### 7.2 Personal Score 구성요소

```python
personal_score = 0.0

# 1. 장르 매칭 보너스 (최대 0.9)
matching_genres = movie_genres & user_top_genres
personal_score += min(len(matching_genres) * 0.3, 0.9)

# 2. 유사 영화 보너스 (+0.4)
if movie.id in similar_to_user_favorites:
    personal_score += 0.4

# 3. 고평점 영화 보너스
if movie.vote_average >= 8.0 and movie.vote_count >= 100:
    personal_score += 0.2  # #명작 태그

# 4. 인기도 보너스 (+0.05)
if movie.popularity > 100:
    hybrid_score += 0.05
```

---

## 8. 홈 화면 섹션 순서

### 8.1 로그인 상태별 순서

**로그인 시:** 개인화 → 범용
| 순서 | 섹션 | 데이터 소스 |
|:---:|------|-------------|
| 0 | 🎯 맞춤 추천 (hybrid_row) | Hybrid Score 상위 60개 → 40개 풀 → 20개 표시 |
| 1 | 💜 MBTI 추천 | mbti_scores 상위 50개 → 20개 표시 |
| 2 | 날씨별 추천 | weather_scores 상위 50개 → 20개 표시 |
| 3 | 기분별 추천 | emotion_tags 상위 50개 → 20개 표시 |
| 4 | 🔥 인기 영화 | popularity 순 100개 → 50개 풀 → 20개 표시 |
| 5 | ⭐ 높은 평점 | vote_average 순 100개 → 50개 풀 → 20개 표시 |

**비로그인 시:** 범용 → 개인화
| 순서 | 섹션 | 데이터 소스 |
|:---:|------|-------------|
| 1 | 🔥 인기 영화 | popularity 순 100개 → 50개 풀 → 20개 표시 |
| 2 | ⭐ 높은 평점 | vote_average 순 100개 → 50개 풀 → 20개 표시 |
| 3 | 날씨별 추천 | weather_scores 상위 50개 → 20개 표시 |
| 4 | 기분별 추천 | emotion_tags 상위 50개 → 20개 표시 |

### 8.2 🔄 새로고침 버튼

모든 섹션 제목 우측에 새로고침 버튼이 있습니다:
- **동작**: 풀(40~50개) 내에서 20개 재셔플
- **API 호출 없음**: 클라이언트 사이드에서 Fisher-Yates 알고리즘으로 셔플
- **애니메이션**: 버튼 클릭 시 회전 애니메이션 피드백

```typescript
// frontend/components/movie/MovieRow.tsx
const displayedMovies = useMemo(() => {
  const shuffled = shuffleArray(movies);  // Fisher-Yates
  return shuffled.slice(0, displayCount); // 20개
}, [movies, displayCount, shuffleKey]);
```

---

## 9. API 엔드포인트 요약

| 엔드포인트 | 메서드 | 파라미터 | 설명 |
|-----------|--------|----------|------|
| `/recommendations` | GET | weather, mood | 홈 화면 전체 추천 |
| `/recommendations/hybrid` | GET | weather, limit | 로그인 필수, 종합 추천 |
| `/recommendations/mbti` | GET | mbti, limit | MBTI별 추천 |
| `/recommendations/weather` | GET | weather, limit | 날씨별 추천 |
| `/recommendations/emotion` | GET | emotion, limit | 감정별 추천 |
| `/recommendations/popular` | GET | limit | 인기 영화 |
| `/recommendations/top-rated` | GET | limit, min_votes | 높은 평점 |
| `/recommendations/for-you` | GET | limit | 로그인 필수, 찜 기반 |

---

## 10. 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/app/api/v1/recommendations.py` | 추천 API 엔드포인트 |
| `backend/app/models/movie.py` | Movie 모델 (JSONB 컬럼) |
| `backend/scripts/regenerate_emotion_tags.py` | 키워드 기반 emotion_tags 생성 |
| `backend/scripts/llm_emotion_tags.py` | LLM 기반 emotion_tags 생성 |
| `frontend/app/page.tsx` | 홈 화면 (섹션 렌더링) |
| `frontend/components/movie/FeaturedBanner.tsx` | 날씨/기분 선택 UI |
| `frontend/hooks/useWeather.ts` | 날씨 상태 관리 |
| `frontend/lib/api.ts` | API 호출 함수 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-02-09 | 🔄 새로고침 버튼 추가 (풀 내 재셔플, API 호출 없음) |
| 2026-02-09 | 맞춤 추천 영화 수 증가: 10개 → 20개 (풀 40개) |
| 2026-02-09 | 섹션별 표시 영화 수: 20개 (풀 50개에서 셔플) |
| 2026-02-09 | 비로그인 시 섹션 순서 변경: 범용(인기→평점) → 개인화(날씨→기분) |
| 2026-02-09 | LLM 기반 emotion_tags 분석 추가 (상위 1,000편) |
| 2026-02-09 | 키워드 점수 0.7 상한 적용 |
| 2026-02-09 | 네거티브 키워드 & 장르 페널티 로직 추가 |
| 2026-02-09 | 30% LLM 보장 혼합 정렬 구현 |
| 2026-02-09 | emotion_tags 7대 감성 클러스터로 재생성 (32,625편) |
| 2026-02-09 | 품질 필터 추가 (vote_count >= 30, vote_average >= 5.0) |
| 2026-02-09 | Mood 기능 추가, emotion_tags 매핑 수정 |
| 2026-02-04 | 초기 Hybrid 추천 로직 구현 |
