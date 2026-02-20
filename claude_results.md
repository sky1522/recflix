# Phase 37: LLM 추천 이유 생성 — 설계 문서

## 날짜
2026-02-20

---

## 1. 추천 이유 생성 방식 비교

### 옵션 A: LLM(Claude) 매번 생성

| 항목 | 내용 |
|------|------|
| 품질 | 최고 — 자연스러운 한국어 문장, 문맥 반영 |
| 비용 | **높음** — 추천 40편 × Haiku 호출 = 요청당 ~40회 API 콜 |
| 지연 | 1~3초/편 × 40 = 심각한 지연 (병렬해도 5~10초) |
| 캐싱 | 가능하나 context(MBTI+날씨+기분) 조합이 많아 캐시 히트율 낮음 |
| 폴백 | 필수 (API 실패, 비용 초과 시) |

**비용 추정** (Haiku):
- 1회 호출: ~200 input + ~50 output tokens ≈ $0.00006
- 일일 1,000 추천 요청 × 40편 = 40,000 호출/일 ≈ $2.4/일 = **$72/월**
- RecFlix 규모 대비 과도한 비용

### 옵션 B: 템플릿 기반 생성

| 항목 | 내용 |
|------|------|
| 품질 | 중상 — 잘 설계하면 자연스러움, 다양성은 템플릿 수에 비례 |
| 비용 | **$0** — 서버 사이드 문자열 조합 |
| 지연 | **0ms** — 추천 점수 계산 시 동시 생성 |
| 캐싱 | 불필요 (즉시 생성) |
| 폴백 | 불필요 |

### 옵션 C: 하이브리드 (기본 템플릿 + 특별 케이스 LLM)

| 항목 | 내용 |
|------|------|
| 품질 | 높음 — 대부분 템플릿, top-3만 LLM |
| 비용 | 낮음 — 요청당 3회 API 콜 ≈ $0.18/일 |
| 지연 | 추가 1~2초 (상위 3편만) |
| 복잡도 | 높음 — 두 시스템 관리 + 폴백 |

### 최종 선택: **옵션 B (템플릿 기반)**

**근거:**
1. **비용 $0** — RecFlix 프로덕션 환경에 최적 (무료 티어/소규모)
2. **지연 0ms** — 추천 응답 속도에 영향 없음
3. **일관성** — 모든 영화에 동일 품질의 추천 이유 제공
4. **기존 데이터 활용** — RecommendationTag의 type/label/score + 영화 메타데이터(장르, 평점, emotion_tags)로 충분히 풍부한 문장 생성 가능
5. **운영 단순성** — API 키 의존성 없음, 폴백 불필요
6. 기존 `llm.py` 캐치프레이즈 인프라는 개별 영화용이므로 구조가 다름 — 재활용보다 별도 모듈이 적합

---

## 2. 템플릿 설계

### 2.1 데이터 소스

추천 이유 생성에 활용 가능한 데이터:

| 데이터 | 소스 | 예시 |
|--------|------|------|
| `RecommendationTag.type` | 추천 엔진 | `mbti`, `weather`, `personal`, `rating` |
| `RecommendationTag.label` | 추천 엔진 | `#INTJ추천`, `#비오는날`, `#취향저격` |
| `RecommendationTag.score` | 추천 엔진 | `0.0~1.0` |
| `movie.genres` | DB | `["드라마", "SF"]` |
| `movie.vote_average` | DB | `8.5` |
| `movie.weighted_score` | DB | `7.8` |
| `movie.emotion_tags` | DB JSONB | `{"healing": 0.8, "romance": 0.6}` |
| `movie.release_date` | DB | `2024-03-15` |
| `mbti` (유저) | 추천 컨텍스트 | `INTJ` |
| `weather` (실시간) | 추천 컨텍스트 | `rainy` |
| `mood` (유저 선택) | 추천 컨텍스트 | `relaxed` |

### 2.2 태그 타입별 문장 템플릿

#### MBTI (type: "mbti")

| # | 조건 | 템플릿 |
|---|------|--------|
| 1 | INTJ + score > 0.7 | `{mbti} 유형이 좋아하는 지적인 {genre} 영화예요` |
| 2 | INTP + score > 0.7 | `분석적인 {mbti}에게 딱 맞는 {genre}` |
| 3 | ENFP + score > 0.7 | `상상력 풍부한 {mbti}를 위한 {genre}` |
| 4 | INFJ + score > 0.7 | `깊은 통찰을 즐기는 {mbti}에게 추천해요` |
| 5 | ENTJ + score > 0.7 | `{mbti}의 리더십 감각에 어울리는 {genre}` |
| 6 | 기본 (score > 0.5) | `{mbti} 성향에 잘 맞는 영화예요` |
| 7 | 기본 (score > 0.6) | `{mbti} 유형의 취향을 저격하는 작품이에요` |
| 8 | NT 기질 | `논리와 분석을 즐기는 {mbti}에게 딱이에요` |
| 9 | NF 기질 | `감성과 공감 능력이 뛰어난 {mbti}를 위한 영화` |
| 10 | SJ 기질 | `안정과 질서를 중시하는 {mbti}에게 어울려요` |
| 11 | SP 기질 | `즉흥적이고 활동적인 {mbti}가 좋아할 영화` |

#### Weather (type: "weather")

| # | 조건 | 템플릿 |
|---|------|--------|
| 12 | rainy + genre:드라마 | `비 오는 날 잔잔한 드라마를 보며 힐링해보세요` |
| 13 | rainy + genre:로맨스 | `빗소리와 함께 보면 더 감성적인 로맨스` |
| 14 | rainy + genre:스릴러 | `비 오는 밤, 긴장감 넘치는 스릴러 어때요?` |
| 15 | rainy + 기본 | `비 내리는 날 감성에 어울리는 영화예요` |
| 16 | sunny + genre:모험 | `화창한 날씨만큼 시원한 모험 영화` |
| 17 | sunny + genre:코미디 | `맑은 날 기분처럼 유쾌한 코미디` |
| 18 | sunny + 기본 | `맑은 날씨에 딱 맞는 기분 좋은 영화예요` |
| 19 | cloudy + genre:미스터리 | `흐린 날 분위기에 어울리는 미스터리` |
| 20 | cloudy + 기본 | `흐린 날 감성에 빠져볼 영화예요` |
| 21 | snowy + genre:애니메이션 | `눈 오는 날 따뜻하게 볼 애니메이션` |
| 22 | snowy + genre:가족 | `눈 내리는 날 가족과 함께 보기 좋은 영화` |
| 23 | snowy + 기본 | `눈 오는 날 포근하게 감싸주는 영화예요` |

#### Mood/Personal (type: "personal")

| # | 조건 | 템플릿 |
|---|------|--------|
| 24 | label=#편안한 | `마음이 편안해지는 따뜻한 이야기예요` |
| 25 | label=#긴장감 | `손에 땀을 쥐게 하는 긴장감이 매력이에요` |
| 26 | label=#신나는 | `에너지 넘치는 액션으로 기분 전환!` |
| 27 | label=#감성적인 | `감동이 밀려오는 깊은 이야기예요` |
| 28 | label=#상상력 | `무한한 상상의 세계로 떠나보세요` |
| 29 | label=#가벼운 | `부담 없이 가볍게 즐길 수 있어요` |
| 30 | label=#울적한 | `눈물로 마음을 비우고 싶을 때 추천해요` |
| 31 | label=#답답한 | `속이 뻥 뚫리는 사이다 같은 영화예요` |
| 32 | label=#취향저격 | `최근 찜한 영화와 비슷한 감성이에요` |
| 33 | label=#취향저격 + genre | `좋아하시는 {genre} 장르의 숨겨진 보석이에요` |
| 34 | label=#비슷한영화 | `이전에 높게 평가한 영화와 비슷한 작품이에요` |

#### Quality (type: "rating")

| # | 조건 | 템플릿 |
|---|------|--------|
| 35 | ws >= 8.0 | `평점 {vote_avg}의 압도적 명작이에요` |
| 36 | ws >= 7.5 + 오래된 영화 | `시간이 지나도 빛나는 클래식 명작` |
| 37 | ws >= 7.5 + 최신작 | `최근 개봉한 화제작, 놓치지 마세요` |
| 38 | ws >= 7.5 | `높은 평점이 증명하는 수작이에요` |

#### 복합 조건 (2개 이상 태그 결합)

| # | 조건 | 템플릿 |
|---|------|--------|
| 39 | mbti + weather | `{mbti}이(가) {weather_ko}에 보면 더 좋은 영화` |
| 40 | mbti + mood | `{mbti}이(가) {mood_ko} 기분일 때 딱 맞는 작품` |
| 41 | weather + mood | `{weather_ko} {mood_ko} 기분에 완벽한 선택이에요` |
| 42 | personal + quality | `취향에 딱 맞으면서 평점도 높은 영화예요` |
| 43 | mbti + quality | `{mbti} 유형이 좋아하는 평점 {vote_avg}의 명작` |

### 2.3 동적 변수

| 변수 | 소스 | 예시 값 |
|------|------|---------|
| `{mbti}` | 유저 프로필 | `INTJ` |
| `{genre}` | movie.genres[0] 한국어 | `드라마`, `SF` |
| `{vote_avg}` | movie.vote_average | `8.5` |
| `{weather_ko}` | 매핑 | `비 오는 날`, `맑은 날` |
| `{mood_ko}` | 매핑 | `편안한`, `긴장감 넘치는` |
| `{year}` | movie.release_date[:4] | `2024` |

### 2.4 문장 생성 우선순위

추천 태그가 여러 개일 때, 가장 의미 있는 이유를 선택하는 우선순위:

```
1. 복합 조건 (2개+ 태그 결합) — 가장 구체적
2. Mood/Personal 태그 — 사용자 감성과 직결
3. MBTI 태그 — 개인화 핵심
4. Weather 태그 — 실시간 컨텍스트
5. Quality 태그 — 보편적 추천 (폴백)
```

동일 우선순위 내에서는 `score`가 높은 태그 우선.

### 2.5 예시 30개

| # | 컨텍스트 | 생성된 추천 이유 |
|---|---------|----------------|
| 1 | INTJ + 비 + 드라마 | INTJ이(가) 비 오는 날에 보면 더 좋은 영화 |
| 2 | ENFP + 맑음 + 모험 | 상상력 풍부한 ENFP를 위한 모험 |
| 3 | INFP + 편안한 | 마음이 편안해지는 따뜻한 이야기예요 |
| 4 | 비 + 로맨스 | 빗소리와 함께 보면 더 감성적인 로맨스 |
| 5 | 눈 + 가족영화 | 눈 내리는 날 가족과 함께 보기 좋은 영화 |
| 6 | INTJ + score 0.85 | INTJ 유형이 좋아하는 지적인 SF 영화예요 |
| 7 | ESFP + score 0.7 | 즉흥적이고 활동적인 ESFP가 좋아할 영화 |
| 8 | 흐린 날 + 미스터리 | 흐린 날 분위기에 어울리는 미스터리 |
| 9 | 긴장감 mood | 손에 땀을 쥐게 하는 긴장감이 매력이에요 |
| 10 | 신나는 mood | 에너지 넘치는 액션으로 기분 전환! |
| 11 | #취향저격 + 코미디 | 좋아하시는 코미디 장르의 숨겨진 보석이에요 |
| 12 | #비슷한영화 | 이전에 높게 평가한 영화와 비슷한 작품이에요 |
| 13 | ws 8.5 | 평점 8.5의 압도적 명작이에요 |
| 14 | ws 7.8 + 2024년 | 최근 개봉한 화제작, 놓치지 마세요 |
| 15 | ws 7.6 + 1990년 | 시간이 지나도 빛나는 클래식 명작 |
| 16 | INTJ + #명작 | INTJ 유형이 좋아하는 평점 8.2의 명작 |
| 17 | #취향저격 + #명작 | 취향에 딱 맞으면서 평점도 높은 영화예요 |
| 18 | INFJ + 감성적인 | INFJ이(가) 감성적인 기분일 때 딱 맞는 작품 |
| 19 | 맑은 날 + 코미디 | 맑은 날 기분처럼 유쾌한 코미디 |
| 20 | 비 + 스릴러 | 비 오는 밤, 긴장감 넘치는 스릴러 어때요? |
| 21 | ENTP + 드라마 | 분석적인 ENTP에게 딱 맞는 드라마 |
| 22 | 상상력 mood | 무한한 상상의 세계로 떠나보세요 |
| 23 | 가벼운 mood | 부담 없이 가볍게 즐길 수 있어요 |
| 24 | 울적한 mood | 눈물로 마음을 비우고 싶을 때 추천해요 |
| 25 | 답답한 mood | 속이 뻥 뚫리는 사이다 같은 영화예요 |
| 26 | ISTJ + score 0.6 | 안정과 질서를 중시하는 ISTJ에게 어울려요 |
| 27 | 눈 + 기본 | 눈 오는 날 포근하게 감싸주는 영화예요 |
| 28 | 비 + 편안한 | 비 내리는 날 감성에 어울리는 영화예요 |
| 29 | ENFJ + 기본 | ENFJ 성향에 잘 맞는 영화예요 |
| 30 | ws 7.5 + 기본 | 높은 평점이 증명하는 수작이에요 |

---

## 3. 적용 위치

### 3.1 Backend

**응답 구조 변경:**

```python
# schemas/recommendation.py
class HybridMovieItem(MovieListItem):
    recommendation_tags: List[RecommendationTag] = []
    hybrid_score: float = 0.0
    recommendation_reason: str = ""  # ← 새로 추가
```

**생성 위치:**
- `recommendation_engine.py`의 `calculate_hybrid_scores()` 반환 시 또는
- 별도 모듈 `recommendation_reason.py`에서 `(tags, movie, context) → reason` 생성

### 3.2 Frontend

**표시 위치: 카드 하단 (태그 아래)**

```
┌──────────────┐
│              │
│   포스터      │  ← 기존 HybridMovieCard
│              │
│     87%      │  ← hybrid_score 뱃지
├──────────────┤
│ 인셉션       │  ← 제목
│ 2010 · SF    │  ← 연도 · 장르
│ #INTJ추천    │  ← 기존 태그 뱃지
│ #비오는날     │
│              │
│ "INTJ 유형이  │  ← ★ 추천 이유 (NEW)
│  좋아하는     │     text-xs, text-white/60
│  지적인 SF"   │     max 2줄, ellipsis
└──────────────┘
```

**구현 방식:**
- `HybridMovieCard.tsx`에서 `movie.recommendation_reason`이 있으면 태그 아래에 표시
- 스타일: `text-xs text-white/50 italic line-clamp-2`
- 최대 2줄, 넘치면 `...` 처리

---

## 4. 구현 계획

### 단계별 실행 순서

#### Step 1: Backend — 추천 이유 생성 모듈 (신규)
- **새 파일**: `backend/app/api/v1/recommendation_reason.py`
- 함수: `generate_reason(tags, movie, mbti, weather, mood) → str`
- 태그 우선순위 로직 + 템플릿 매칭 + 동적 변수 치환
- 약 100~150줄

#### Step 2: Backend — 스키마 수정
- **수정**: `backend/app/schemas/recommendation.py`
- `HybridMovieItem`에 `recommendation_reason: str = ""` 필드 추가
- `from_movie_with_tags()`에 reason 파라미터 추가

#### Step 3: Backend — 엔진 연동
- **수정**: `backend/app/api/v1/recommendation_engine.py`
- `calculate_hybrid_scores()` 반환값에 reason 포함
- 또는 `recommendations.py`에서 최종 응답 조립 시 reason 생성

#### Step 4: Backend — 추천 API 응답에 reason 포함
- **수정**: `backend/app/api/v1/recommendations.py`
- `HybridMovieItem.from_movie_with_tags()` 호출 시 reason 전달

#### Step 5: Frontend — 타입 정의
- **수정**: `frontend/types/index.ts`
- `HybridMovie` 인터페이스에 `recommendation_reason?: string` 추가

#### Step 6: Frontend — 카드 UI
- **수정**: `frontend/components/movie/HybridMovieCard.tsx`
- 태그 뱃지 아래에 `recommendation_reason` 텍스트 표시
- 스타일: `text-xs text-white/50 italic line-clamp-2`

### 수정 파일 목록

| 파일 | 작업 | 신규/수정 |
|------|------|----------|
| `backend/app/api/v1/recommendation_reason.py` | 추천 이유 생성 모듈 | **신규** |
| `backend/app/schemas/recommendation.py` | reason 필드 추가 | 수정 |
| `backend/app/api/v1/recommendation_engine.py` | reason 생성 호출 | 수정 |
| `backend/app/api/v1/recommendations.py` | reason 응답 포함 | 수정 |
| `frontend/types/index.ts` | HybridMovie 타입 | 수정 |
| `frontend/components/movie/HybridMovieCard.tsx` | reason UI 표시 | 수정 |

### 변경하지 않는 파일
- `recommendation_constants.py` — 기존 가중치/매핑 그대로
- `diversity.py` — 다양성 정책 그대로
- `recommendation_cf.py` — CF 로직 그대로
- `llm.py` — 캐치프레이즈는 별도 기능으로 유지

---

## 5. 설계 원칙

1. **비용 $0** — LLM API 호출 없음, 순수 템플릿 기반
2. **지연 0ms** — 추천 점수 계산과 동시에 문자열 조합
3. **기존 로직 무수정** — 추천 알고리즘, 다양성 정책 변경 없음
4. **Karpathy 원칙 준수** — 신규 모듈 100~150줄 이내
5. **점진적 확장 가능** — 향후 LLM 생성으로 업그레이드 시 `generate_reason()` 함수만 교체
