# RecFlix 추천 시스템 로직

> 마지막 업데이트: 2026-02-25

---

## 0. 품질 필터 (Quality Filter)

모든 추천 섹션에 `weighted_score` 기반 통합 품질 필터가 적용됩니다:

```python
# 통합 품질 필터 (v2, 2026-02-10~)
weighted_score >= 6.0   # vote_count, vote_average, popularity를 종합한 가중 점수
```

> **변경 이유**: 기존 `vote_count >= 30 AND vote_average >= 5.0` 2중 필터 대비,
> `weighted_score`는 투표 수·평균 평점·인기도를 종합한 단일 지표로 더 정밀한 품질 판별이 가능합니다.

| 섹션 | 품질 필터 | 정렬 기준 |
|------|----------|----------|
| 기분별 추천 | weighted_score >= 6.0 | emotion_score DESC, weighted_score DESC |
| 인기 영화 | weighted_score >= 6.0 | popularity DESC, weighted_score DESC |
| 날씨별 추천 | weighted_score >= 6.0 | weather_score DESC, weighted_score DESC |
| MBTI 추천 | weighted_score >= 6.0 | mbti_score DESC, weighted_score DESC |
| 높은 평점 | weighted_score >= 6.0 | vote_average DESC, weighted_score DESC |
| Hybrid 맞춤 | weighted_score >= 6.0 | hybrid_score DESC |

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
| **LLM 분석** | 인기 상위 영화 | ~1,711 | 1.0 |
| **키워드 기반** | 나머지 영화 | ~41,206 | **0.7** (상한) |

### 2.2 LLM 분석 (Claude API)

인기 상위 영화에 대해 Claude API로 정밀 분석:

```python
# 스크립트: backend/scripts/llm_emotion_tags.py (초기 분석)
#           backend/scripts/llm_reanalyze_all.py (재분석, 배치 저장 + resume 지원)
# 모델: claude-sonnet-4-20250514
# 배치: 10편씩 묶어서 API 호출

# 입력: 영화 제목, 장르, 줄거리 (overview)
# 출력: 7개 클러스터별 점수 (0.0 ~ 1.0, 세밀한 분포: 0.35, 0.72 등)
```

> **v2 프롬프트 (2026-02-10)**: 기존 대비 더 세밀한 점수 분포를 생성하도록 프롬프트 개선.
> 0.0/0.5/1.0 같은 단순 점수 대신 0.35, 0.72 같은 연속적인 점수 분포를 생성합니다.

**LLM 분석 결과 예시:**
| 영화 | 1위 | 2위 | 3위 |
|------|-----|-----|-----|
| 인셉션 | tension: 0.88 | fantasy: 0.85 | deep: 0.78 |
| 다크 나이트 | tension: 0.82 | energy: 0.72 | deep: 0.68 |
| 인터스텔라 | deep: 0.85 | fantasy: 0.82 | tension: 0.52 |
| 어벤저스 | energy: 0.95 | fantasy: 0.78 | tension: 0.55 |

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

| 클러스터 | LLM (~1,711편) | 키워드 (~41,206편) |
|---------|---------------|------------------|
| healing | ~350 | ~5,200 |
| tension | ~900 | ~4,100 |
| energy | ~850 | ~3,000 |
| romance | ~250 | ~2,500 |
| deep | ~550 | ~4,500 |
| fantasy | ~550 | ~2,100 |
| light | ~380 | ~2,900 |

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
# 가중치: 25% (mood 있을 때) / 35% (mood 없을 때)
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

### 6.1 지원 기분 (8개, 2x4 그리드)

**1행:**
| 코드 | 이모지 | 한국어 | emotion_tags 매핑 |
|------|--------|--------|-------------------|
| relaxed | 😌 | 평온한 | healing |
| tense | 😰 | 긴장된 | tension |
| excited | 😆 | 활기찬 | energy |
| emotional | 💕 | 몽글몽글한 | romance, deep |

**2행:**
| 코드 | 이모지 | 한국어 | emotion_tags 매핑 |
|------|--------|--------|-------------------|
| imaginative | 🔮 | 상상에 빠진 | fantasy |
| light | 😄 | 유쾌한 | light |
| gloomy | 🌧️ | 울적한 | deep, healing |
| stifled | 😤 | 답답한 | tension, energy |

### 6.2 기분 → emotion_tags 매핑

```python
MOOD_EMOTION_MAPPING = {
    "relaxed": ["healing"],           # 평온한 → 힐링
    "tense": ["tension"],             # 긴장된 → 긴장감
    "excited": ["energy"],            # 활기찬 → 에너지
    "emotional": ["romance", "deep"], # 몽글몽글한 → 로맨스+깊이
    "imaginative": ["fantasy"],       # 상상에 빠진 → 판타지
    "light": ["light"],               # 유쾌한 → 라이트
    "gloomy": ["deep", "healing"],    # 울적한 → 깊이+힐링
    "stifled": ["tension", "energy"], # 답답한 → 긴장감+에너지
}
```

### 6.3 Hybrid 스코어링에서의 Mood

```python
# 가중치: 30% (mood 있을 때만)
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

### 7.1 가중치 구성 (v3, CF 통합, 2026-02-19~)

**CF 모델 활성화 + Mood 있을 때:**
```
Hybrid Score = (0.20 × MBTI) + (0.15 × Weather) + (0.25 × Mood) + (0.15 × Personal) + (0.25 × CF)
```

**CF 모델 활성화 + Mood 없을 때:**
```
Hybrid Score = (0.25 × MBTI) + (0.20 × Weather) + (0.30 × Personal) + (0.25 × CF)
```

**CF 모델 없을 때 (기존 v2):**
```
Mood 있음: (0.25 × MBTI) + (0.20 × Weather) + (0.30 × Mood) + (0.25 × Personal)
Mood 없음: (0.35 × MBTI) + (0.25 × Weather) + (0.40 × Personal)
```

> **v3 변경점**: MovieLens 25M 기반 SVD 협업 필터링 모델의 item_bias를 CF 품질 점수로 25% 가중치 배정.
> RecFlix 사용자는 MovieLens에 없으므로 CF = global_mean + item_bias (아이템 품질 추정).
> SVD RMSE=0.8768 (Item Mean 0.9656 대비 -9.2% 개선).

### 7.2 Personal Score 구성요소

```python
personal_score = 0.0

# 0. 콜드스타트 보완 (Phase 46, 상호작용 < 5건 시)
#    온보딩 preferred_genres(한글) → Genre 테이블로 영어 변환 → genre_counts에 가중치 1 추가
#    상호작용 5건 이상이면 preferred_genres 무시 (기존 데이터로 충분)
#    → 신규 사용자도 온보딩에서 선택한 장르 기반으로 즉시 개인화 추천 가능

# 1. 장르 매칭 보너스 (최대 0.9)
matching_genres = movie_genres & user_top_genres
personal_score += min(len(matching_genres) * 0.3, 0.9)

# 2. 유사 영화 보너스 (+0.4)
if movie.id in similar_to_user_favorites:
    personal_score += 0.4

# 3. #명작 태그 (weighted_score 기반)
if weighted_score >= 7.5:
    tags.append("#명작")   # 태그만 표시, 점수 가산 없음

# 4. 인기도 보너스 (+0.05)
if movie.popularity > 100:
    hybrid_score += 0.05
```

### 7.3 품질 보정 (Quality Correction)

Hybrid Score 계산 후, `weighted_score`에 기반한 연속 품질 보정이 적용됩니다:

```python
# weighted_score 기반 연속 보정 (binary bonus 대체)
# ws=6.0 이하 → ×0.85 (감점), ws=9.0 → ×1.00 (만점)
max_ws = 9.0
quality_ratio = clamp((ws - 6.0) / (max_ws - 6.0), 0.0, 1.0)
quality_factor = 0.85 + 0.15 × quality_ratio
hybrid_score *= quality_factor
```

> **변경 이유**: 기존 binary bonus(+0.1/+0.2)는 7.0/8.0 기준으로 점수가 급변했지만,
> 연속 보정은 6.0~9.0 구간에서 0.85~1.0으로 부드럽게 품질을 반영합니다.

---

## 8. 연령등급 필터링 (Age Rating Filter)

### 8.1 개요

모든 추천/검색 API에 `age_rating` 파라미터로 연령등급 필터를 적용할 수 있습니다.

```python
# 파라미터: age_rating (all | family | teen | adult)
# NULL 등급(전체의 ~55.6%)은 모든 그룹에 포함
```

### 8.2 등급 그룹 매핑

```python
AGE_RATING_MAP = {
    "family": ["ALL", "G", "PG", "12"],
    "teen":   ["ALL", "G", "PG", "PG-13", "12", "15"],
}
# "all" / "adult": 필터 미적용 (모든 등급 포함)
```

| 그룹 | 포함 등급 | 설명 |
|------|----------|------|
| family | ALL, G, PG, 12 + NULL | 가족 관람가 |
| teen | ALL, G, PG, PG-13, 12, 15 + NULL | 청소년 관람가 |
| adult | 전체 | 성인 포함 전체 |
| all | 전체 | 필터 없음 |

### 8.3 적용 범위

| API | age_rating 지원 |
|-----|:---:|
| `GET /recommendations` | ✅ |
| `GET /recommendations/hybrid` | ✅ |
| `GET /recommendations/mbti` | ✅ |
| `GET /recommendations/weather` | ✅ |
| `GET /recommendations/emotion` | ✅ |
| `GET /recommendations/popular` | ✅ |
| `GET /recommendations/top-rated` | ✅ |
| `GET /movies` (검색) | ✅ |

### 8.4 Frontend UI

- **MovieCard**: certification 값에 따라 색상 배지 표시 (ALL=초록, PG-13=노랑, R=빨강 등)
- **검색 페이지**: 등급 필터 드롭다운 (전체/가족/청소년/성인)

---

## 9. 홈 화면 섹션 순서

### 9.1 로그인 상태별 순서

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

### 9.2 🔄 새로고침 버튼

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

## 10. API 엔드포인트 요약

| 엔드포인트 | 메서드 | 파라미터 | 설명 |
|-----------|--------|----------|------|
| `/recommendations` | GET | weather, mood, age_rating | 홈 화면 전체 추천 |
| `/recommendations/hybrid` | GET | weather, limit, age_rating | 로그인 필수, 종합 추천 |
| `/recommendations/mbti` | GET | mbti, limit, age_rating | MBTI별 추천 |
| `/recommendations/weather` | GET | weather, limit, age_rating | 날씨별 추천 |
| `/recommendations/emotion` | GET | emotion, limit, age_rating | 감정별 추천 |
| `/recommendations/popular` | GET | limit, age_rating | 인기 영화 |
| `/recommendations/top-rated` | GET | limit, min_votes, age_rating | 높은 평점 |
| `/recommendations/for-you` | GET | limit | 로그인 필수, 찜 기반 |
| `/movies` | GET | genre, query, age_rating, ... | 영화 검색 |

---

## 11. 관련 파일

| 파일 | 설명 |
|------|------|
| `backend/app/api/v1/recommendations.py` | 추천 API 엔드포인트 (Hybrid 스코어링, 품질 필터, 연령등급) |
| `backend/app/api/v1/recommendation_engine.py` | Hybrid 스코어링 엔진 (CF 통합) |
| `backend/app/api/v1/recommendation_constants.py` | 가중치 상수 (v2/v3, A/B 테스트, 다양성 정책) |
| `backend/app/api/v1/recommendation_cf.py` | 협업 필터링 모듈 (SVD item_bias 예측) |
| `backend/app/api/v1/recommendation_reason.py` | 추천 이유 생성 (43개 템플릿) |
| `backend/app/api/v1/diversity.py` | 다양성 후처리 (장르/연도/serendipity/중복 제거) |
| `backend/app/api/v1/semantic_search.py` | 시맨틱 검색 (인메모리 벡터 검색) |
| `backend/app/services/two_tower_retriever.py` | Two-Tower ANN 후보 생성 (FAISS) |
| `backend/app/services/reranker.py` | LightGBM CTR 예측 재랭커 서빙 |
| `backend/scripts/train_reranker.py` | LightGBM 재랭커 학습 스크립트 |
| `backend/app/api/v1/movies.py` | 영화 검색 API (시맨틱 검색 통합, 연령등급 필터) |
| `backend/app/models/movie.py` | Movie 모델 (JSONB 컬럼) |
| `backend/scripts/regenerate_emotion_tags.py` | 키워드 기반 emotion_tags 생성 |
| `backend/scripts/llm_emotion_tags.py` | LLM 기반 emotion_tags 초기 생성 |
| `backend/scripts/llm_reanalyze_all.py` | LLM 재분석 (배치 저장 + resume) |
| `backend/scripts/test_llm_prompt.py` | LLM 프롬프트 테스트 |
| `backend/scripts/analyze_hybrid_scores.py` | Hybrid 점수 분석 스크립트 |
| `frontend/app/page.tsx` | 홈 화면 (섹션 렌더링) |
| `frontend/app/movies/page.tsx` | 영화 검색 (시맨틱 검색 + 연령등급 필터) |
| `frontend/components/movie/FeaturedBanner.tsx` | 날씨/기분 선택 UI |
| `frontend/components/movie/MovieCard.tsx` | 영화 카드 (등급 배지 포함) |
| `frontend/components/movie/HybridMovieCard.tsx` | 추천 태그 + 추천 이유 표시 카드 |
| `frontend/hooks/useWeather.ts` | 날씨 상태 관리 |
| `frontend/lib/api.ts` | API 호출 함수 |
| `frontend/lib/curationMessages.ts` | 큐레이션 문구 258개 + 헬퍼 함수 |
| `frontend/lib/contextCuration.ts` | 시간대/계절/기온 컨텍스트 감지 |

---

## 12. 시맨틱 검색 (Semantic Search)

### 12.1 개요

자연어 질의로 영화를 검색하는 기능입니다. 사전 계산된 임베딩을 인메모리에 로드하여 실시간 코사인 유사도 검색을 수행합니다.

| 항목 | 내용 |
|------|------|
| 임베딩 모델 | Voyage AI `voyage-multilingual-2` |
| 임베딩 차원 | 1024 |
| 영화 수 | 42,917편 |
| 검색 방식 | NumPy 인메모리 코사인 유사도 |
| 저장 | `backend/data/embeddings/` (git-lfs) |

### 12.2 동작 흐름

```
1. 서버 시작 시 임베딩 로드 (movie_embeddings.npy + movie_id_index.json)
2. L2 정규화 (코사인 유사도 → 내적으로 변환)
3. 사용자 질의 → Voyage AI API로 실시간 임베딩
4. 내적 계산 (N,1024) @ (1024,) → (N,) 스코어
5. argpartition으로 Top-K 추출 (O(N), argsort O(N log N)보다 빠름)
6. 재랭킹: 유사도 + 인기도 + 품질 복합점수
```

### 12.3 재랭킹 공식 (v2, Phase 49)

```python
# 시맨틱 유사도 60% + 인기도 15% (log) + 품질 25%
pop_log = log1p(popularity) / log1p(max_popularity)  # log 정규화
quality_norm = weighted_score / 10
final_score = 0.60 * semantic_score + 0.15 * pop_log + 0.25 * quality_norm
```

> **v2 변경점 (Phase 49)**: 인기도 편향 감소를 위해 log1p 정규화 도입,
> 품질 가중치 15%→25% 상향, 시맨틱 유사도 70%→60% 하향.

### 12.4 API 엔드포인트

```
GET /movies/semantic-search?q={자연어 질의}&limit=20
```

응답에 `match_reason` 필드 포함 (예: "따뜻한 가족 이야기의 감동적인 영화").

### 12.5 Frontend 통합

- 검색 페이지에서 자연어 질의 감지 시 자동으로 시맨틱 검색 섹션 표시
- "AI 추천" 섹션 UI로 일반 검색 결과와 구분

---

## 13. 다양성 후처리 (Diversity Post-Processing)

### 13.1 개요

추천 스코어 계산 후, 결과의 다양성을 보장하기 위한 5개 후처리 함수가 순차 적용됩니다.

```python
# 적용 순서 (backend/app/api/v1/diversity.py)
1. diversify_by_genre()    # 동일 장르 연속 제한
2. apply_genre_cap()       # 단일 장르 비율 제한
3. ensure_freshness()      # 최신작/클래식 비율 보장
4. inject_serendipity()    # 의외의 발견 삽입
5. deduplicate_section()   # 섹션 간 중복 제거
```

### 13.2 함수별 상세

#### 13.2.1 `diversify_by_genre` — 동일 장르 연속 제한

```python
# 같은 primary genre가 max_consecutive개 연속되지 않도록 재배치
# 상위 pool 내에서 재배치하므로 스코어 손실 최소화
# 조건 만족 영화가 없으면 제약 완화 후 최고점 선택
max_consecutive = 3  # GENRE_MAX_CONSECUTIVE
```

#### 13.2.2 `apply_genre_cap` — 단일 장르 비율 제한

```python
# 단일 장르가 전체의 max_genre_ratio를 초과하지 않도록 필터링
# 5편 이하 결과에는 미적용
# 부족하면 스킵된 영화로 채움
max_genre_ratio = 0.35  # GENRE_MAX_RATIO
```

#### 13.2.3 `ensure_freshness` — 연도 다양성 보장

```python
# 최신작(3년 이내): 최소 20%
# 클래식(10년 이전): 최소 10%
# 나머지: 원래 스코어 순 채움
recent_ratio = 0.20   # FRESHNESS_RECENT_RATIO
classic_ratio = 0.10  # FRESHNESS_CLASSIC_RATIO
```

#### 13.2.4 `inject_serendipity` — 의외의 발견

```python
# 추천 리스트의 10%를 사용자 선호 장르 외 고품질 영화로 대체
# DB에서 랜덤 조회 (user_top_genres 제외, weighted_score >= 7.0)
# 리스트의 70% 지점에 삽입 (상위 관련성 높은 영화 유지)
# "#의외의발견" 태그 부여
serendipity_ratio = 0.10        # SERENDIPITY_RATIO
min_quality = 7.0               # SERENDIPITY_MIN_QUALITY
```

#### 13.2.5 `deduplicate_section` — 섹션 간 중복 제거

```python
# 이미 다른 섹션에 노출된 영화(seen_ids)를 현재 섹션에서 제외
# 홈 화면 렌더링 시 섹션 순서대로 seen_ids에 추가
```

### 13.3 정책 상수 (`recommendation_constants.py`)

| 상수 | 값 | 설명 |
|------|-----|------|
| `DIVERSITY_ENABLED` | `True` | 다양성 정책 전체 on/off |
| `GENRE_MAX_CONSECUTIVE` | 3 | 동일 장르 연속 최대 수 |
| `GENRE_MAX_RATIO` | 0.35 | 단일 장르 최대 비율 |
| `FRESHNESS_RECENT_RATIO` | 0.20 | 최신작(3년) 최소 비율 |
| `FRESHNESS_CLASSIC_RATIO` | 0.10 | 클래식(10년+) 최소 비율 |
| `SERENDIPITY_RATIO` | 0.10 | 의외의 발견 비율 |
| `SERENDIPITY_MIN_QUALITY` | 7.0 | 의외의 발견 최소 품질 |
| `SEMANTIC_GENRE_MAX` | 5 | 시맨틱 검색 같은 장르 최대 편수 |

---

## 14. 추천 이유 생성 (Recommendation Reason)

### 14.1 개요

추천 태그와 영화 메타데이터로 한국어 추천 이유 문장을 생성합니다. LLM 호출 없이 순수 문자열 템플릿 매칭으로 동작합니다.

| 항목 | 내용 |
|------|------|
| 파일 | `backend/app/api/v1/recommendation_reason.py` (239줄) |
| 템플릿 수 | 43개 |
| 비용 | $0 (LLM 호출 없음) |
| 지연 | ~0ms (문자열 조합) |

### 14.2 우선순위

```
1. 복합조건 (2+ 시그널): MBTI+Weather, MBTI+Mood, Weather+Mood, Personal+Rating, MBTI+Rating
2. Mood/Personal 태그
3. MBTI 태그
4. Weather 태그
5. Quality/Rating 태그
6. Fallback (빈 문자열)
```

### 14.3 카테고리별 템플릿 수

| 카테고리 | 템플릿 수 | 예시 |
|---------|----------|------|
| Compound (복합) | 6 | "INTJ이(가) 비 오는 날에 보면 더 좋은 영화" |
| MBTI | 11 | "분석적인 INTP에게 딱 맞는 액션" |
| Weather | 12 | "비 오는 밤, 긴장감 넘치는 스릴러 어때요?" |
| Mood | 10 | "손에 땀을 쥐게 하는 긴장감이 매력이에요" |
| Quality | 4 | "평점 8.5의 압도적 명작이에요" |

### 14.4 MBTI 기질 그룹 매핑

```python
NT (분석형): INTJ, INTP, ENTJ, ENTP → "논리와 분석을 즐기는 ..."
NF (외교형): INFJ, INFP, ENFJ, ENFP → "감성과 공감 능력이 뛰어난 ..."
SJ (관리형): ISTJ, ISFJ, ESTJ, ESFJ → "안정과 질서를 중시하는 ..."
SP (탐험형): ISTP, ISFP, ESTP, ESFP → "즉흥적이고 활동적인 ..."
```

### 14.5 Frontend 표시

- `HybridMovieItem` 스키마: `recommendation_reason: str = ""` 필드
- `HybridMovieCard` 컴포넌트: 추천 태그 아래 이탤릭 텍스트로 표시 (`line-clamp-2`)

---

## 15. SVD 협업 필터링 프로덕션 배포

### 15.1 모델 정보

| 항목 | 내용 |
|------|------|
| 데이터셋 | MovieLens 25M (22.5M 평점, 162K 사용자) |
| 매핑 | 20,372편 RecFlix ↔ MovieLens TMDB ID |
| 알고리즘 | SVD (k=100, scipy.sparse.linalg.svds) |
| RMSE | 0.8768 (Item Mean 0.9656 대비 -9.2%) |
| CF 점수 | `global_mean + item_bias` (아이템 품질 추정) |

### 15.2 프로덕션 배포 방식

```dockerfile
# Dockerfile에서 git-lfs로 모델 + 임베딩 다운로드
RUN apt-get install -y git-lfs && git lfs install
RUN git lfs pull --include="data/embeddings/*,data/svd_model.pkl"
```

- numpy 2.x 호환성: pickle 직렬화 형식 + pandas/scipy 버전 맞춤
- 서버 시작 시 모델 로드: `load_cf_model()` → 인메모리 item_bias dict

---

## 16. 이벤트 트래킹 & A/B 테스트 메트릭

### 16.1 이벤트 트래킹 개요

사용자 행동 이벤트에 `experiment_group`과 추천 컨텍스트가 메타데이터로 포함됩니다.

```
이벤트 수집 흐름:
1. 추천 섹션 렌더링 → recommendation_impression (section 정보 포함)
2. 영화 카드 클릭 → movie_click (section + ?from=section&pos=index URL 파라미터)
3. 상세 페이지 진입 → movie_detail_view (source_section, source_position)
4. 상세 페이지 이탈 → movie_detail_leave (duration_ms)
5. 평점/찜 액션 → rating, favorite_add/remove (source_section 포함)
```

### 16.2 추천 컨텍스트 전파 (Phase 52A)

```typescript
// MovieCard / HybridMovieCard
<Link href={`/movies/${movie.id}?from=${section}&pos=${index}`}>

// movies/[id]/page.tsx
const sourceSection = searchParams.get("from") || "direct";
const sourcePosition = searchParams.get("pos");
// → movie_detail_view 이벤트의 metadata에 source_section, source_position 포함
```

### 16.3 A/B 리포트 메트릭 (Phase 52B)

| 메트릭 | 설명 |
|--------|------|
| CTR | 클릭 / 노출 |
| CTR CI (Wilson) | CTR 95% 신뢰구간 |
| rating_conversion | 평점 이벤트 / 상세 조회 |
| favorite_conversion | 찜 이벤트 / 상세 조회 |
| avg_rating_from_recs | 추천 섹션 경유 평점 평균 |
| return_rate | 2일+ 활성 사용자 비율 |
| avg_session_events | 세션당 이벤트 수 평균 |
| funnel | impression → click → detail → rating/favorite 전환율 |
| daily_active_users | 그룹별 일별 고유 사용자 수 |
| comparisons (Z-test) | 그룹 쌍별 CTR/전환율 Z-test (p_value, significant) |

### 16.4 통계 검증

```
Z-test for Proportions (two-tailed):
z = (p₁ - p₂) / √(p_pool × (1 - p_pool) × (1/n₁ + 1/n₂))
p_value = 2 × (1 - Φ(|z|))
유의 수준: α = 0.05, 최소 표본: 그룹당 30건
```

### 16.5 실험 그룹 가중치 배정

```
EXPERIMENT_WEIGHTS=control:34,test_a:33,test_b:33  # 기본값
EXPERIMENT_WEIGHTS=control:80,test_a:10,test_b:10  # 보수적 실험
```

관련 파일: `backend/app/api/v1/ab_stats.py`, `backend/app/api/v1/events.py`, `backend/app/config.py`

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-02-20 | 추천 이유 생성: 템플릿 기반 43개 패턴, recommendation_reason.py 신규 |
| 2026-02-20 | 다양성 후처리: 장르 다양성, 신선도, serendipity, 중복 제거 (diversity.py 신규) |
| 2026-02-20 | SVD 모델 프로덕션 배포: Dockerfile LFS 다운로드, numpy 2.x 호환 |
| 2026-02-20 | 시맨틱 검색: Voyage AI 임베딩 42,917편, NumPy 인메모리 코사인 유사도 (semantic_search.py 신규) |
| 2026-02-27 | Step 05: LightGBM CTR 예측 재랭커 (76dim 피처, AUC 0.66). Two-Tower(200) → GBDT(50) → Hybrid(20). test_a=twotower_lgbm_v1, test_b=twotower_v1 |
| 2026-02-25 | Phase 52: 이벤트 사각지대 해소 + 추천 컨텍스트 전파 + Z-test 통계 유의성 + A/B 메트릭 7종 + 그룹 가중치 배정 |
| 2026-02-25 | preferred_genres 콜드스타트 가중치: 1 → 3 (온보딩 장르 기반 추천 강화) |
| 2026-02-24 | 시맨틱 재랭킹 v2: semantic 60% + popularity 15% (log1p) + quality 25% (기존 70/15/15) |
| 2026-02-23 | 피드백 루프: interaction_version 캐시 무효화 (평점/찜 변경 시 추천 즉시 갱신) |
| 2026-02-23 | 콜드스타트 보완: 상호작용 <5건 시 온보딩 preferred_genres → genre_counts fallback |
| 2026-02-19 | CF 통합 (v3): MovieLens 25M SVD item_bias → 25% 가중치, recommendation_cf.py 신규 |
| 2026-02-13 | 기분 카테고리 확장: 6개 → 8개 (gloomy 울적한, stifled 답답한 추가) |
| 2026-02-13 | 컨텍스트 큐레이션 시스템: 시간대+계절+기온 감지, 258개 문구 (contextCuration.ts) |
| 2026-02-13 | 큐레이션 서브타이틀 시스템: 날씨/기분/MBTI/고정별 보조 메시지 |
| 2026-02-10 | 품질 보정: binary bonus → 연속 보정 (×0.85~1.0, weighted_score 기반) |
| 2026-02-10 | Hybrid 가중치 v2 튜닝: Mood 0.20→0.30, MBTI 0.30→0.25, Personal 0.30→0.25 |
| 2026-02-10 | 연령등급 필터링 추가: age_rating 파라미터 (all/family/teen/adult) 전 API 적용 |
| 2026-02-10 | 품질 필터 통합: vote_count+vote_average → weighted_score >= 6.0 단일 기준 |
| 2026-02-10 | LLM emotion_tags 재분석: 1,000편 → 1,711편 (새 프롬프트, 세밀 분포) |
| 2026-02-10 | #명작 태그 기준 변경: weighted_score >= 7.5 (점수 가산 없이 태그만 표시) |
| 2026-02-10 | 정렬 기준 개선: 2차 정렬에 weighted_score DESC 추가 |
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
