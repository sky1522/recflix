# RecFlix 프로젝트 컨텍스트

실시간 컨텍스트(날씨/기분)와 성격 특성(MBTI)을 결합한 초개인화 영화 큐레이션 플랫폼

---

## 0. 배포 정보 (2026-02-13)

| 서비스 | URL |
|--------|-----|
| Frontend (Vercel) | https://jnsquery-reflix.vercel.app |
| Backend API (Railway) | https://backend-production-cff2.up.railway.app |
| API Docs | https://backend-production-cff2.up.railway.app/docs |
| GitHub | https://github.com/sky1522/recflix |

**데이터**: 42,917편 영화 (Railway PostgreSQL에 마이그레이션 완료)

---

## 1. 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend                             │
│              Next.js 14 (App Router)                    │
│      TailwindCSS + Framer Motion + Zustand              │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API
                      ▼
┌─────────────────────────────────────────────────────────┐
│                     Backend                              │
│                  Python FastAPI                          │
│        SQLAlchemy + Pydantic + Redis + httpx            │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────────┐
    │PostgreSQL│ │  Redis   │ │ OpenWeather  │
    │  (DB)    │ │ (Cache)  │ │    API       │
    └──────────┘ └──────────┘ └──────────────┘
```

---

## 2. 데이터베이스 스키마

### 주요 테이블

```sql
-- 사용자
users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    mbti VARCHAR(4),
    birth_date DATE,
    location_consent BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
)

-- 영화 (22컬럼)
movies (
    id INTEGER PRIMARY KEY,           -- TMDB ID
    title VARCHAR(500) NOT NULL,      -- 영어/원어 제목
    title_ko VARCHAR(500),            -- 한국어 제목
    certification VARCHAR(20),        -- 연령등급
    runtime INTEGER,
    vote_average FLOAT,
    vote_count INTEGER,
    popularity FLOAT,
    overview TEXT,                     -- 줄거리 (한국어 통일)
    tagline VARCHAR(500),
    poster_path VARCHAR(200),
    release_date DATE,
    is_adult BOOLEAN DEFAULT FALSE,
    director VARCHAR(500),            -- 감독 (영어)
    director_ko VARCHAR(500),         -- 감독 (한국어)
    cast_ko TEXT,                     -- 출연진 (한국어, 쉼표 구분, 100% 한글화)
    production_countries_ko TEXT,     -- 제작국가 (한국어)
    release_season VARCHAR(10),       -- 봄/여름/가을/겨울
    weighted_score FLOAT,             -- 품질 점수 (vote_average + vote_count 가중)
    mbti_scores JSONB,                -- {"INTJ": 0.8, "ENFP": 0.6, ...}
    weather_scores JSONB,             -- {"sunny": 0.7, "rainy": 0.9, ...}
    emotion_tags JSONB                -- {"healing": 0.8, "tension": 0.3, ...}
)

-- 유사 영화 (자체 계산, 영화별 Top 10)
similar_movies (
    movie_id INTEGER REFERENCES movies(id),
    similar_movie_id INTEGER REFERENCES movies(id),
    PRIMARY KEY (movie_id, similar_movie_id)
)

-- 평점
ratings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    movie_id INTEGER REFERENCES movies(id),
    score DECIMAL(2,1) NOT NULL,  -- 0.5 ~ 5.0
    weather_context VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, movie_id)
)

-- 컬렉션
collections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
)

collection_movies (
    collection_id INTEGER REFERENCES collections(id),
    movie_id INTEGER REFERENCES movies(id),
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (collection_id, movie_id)
)
```

### JSONB 인덱스

```sql
CREATE INDEX idx_movies_mbti ON movies USING GIN(mbti_scores);
CREATE INDEX idx_movies_weather ON movies USING GIN(weather_scores);
CREATE INDEX idx_movies_emotion ON movies USING GIN(emotion_tags);
```

---

## 3. API 엔드포인트

### 인증

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/auth/signup` | 회원가입 |
| POST | `/api/v1/auth/login` | 로그인 (JWT 발급) |
| POST | `/api/v1/auth/refresh` | 토큰 갱신 |

### 사용자

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/users/me` | 내 정보 |
| PUT | `/api/v1/users/me` | 정보 수정 |
| PUT | `/api/v1/users/me/mbti` | MBTI 설정 |

### 영화

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/movies` | 목록 (검색, 필터, 페이지네이션) |
| GET | `/api/v1/movies/{id}` | 상세 |
| GET | `/api/v1/movies/{id}/similar` | 유사 영화 |
| GET | `/api/v1/movies/genres` | 장르 목록 |

### 추천

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/recommendations` | 홈 통합 추천 |
| GET | `/api/v1/recommendations/weather?weather=rainy` | 날씨 기반 |
| GET | `/api/v1/recommendations/mbti?mbti=ENFP` | MBTI 기반 |
| GET | `/api/v1/recommendations/emotion?emotion=healing` | 감정 기반 |
| GET | `/api/v1/recommendations/for-you` | 개인화 (찜 기반) |
| GET | `/api/v1/recommendations/popular` | 인기 영화 |
| GET | `/api/v1/recommendations/top-rated` | 높은 평점 |

### 날씨

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/weather?city=Seoul` | 도시 기반 |
| GET | `/api/v1/weather?lat=37.5&lon=127` | 좌표 기반 |
| GET | `/api/v1/weather/conditions` | 지원 날씨 조건 |

### 평점

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/v1/ratings` | 평점 등록 (Upsert) |
| GET | `/api/v1/ratings/me` | 내 평점 목록 |
| GET | `/api/v1/ratings/{movie_id}` | 특정 영화 평점 |
| DELETE | `/api/v1/ratings/{movie_id}` | 평점 삭제 |

### 상호작용 (통합)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/interactions/movie/{id}` | 영화별 평점/찜 상태 |
| POST | `/api/v1/interactions/movies` | 다중 영화 상태 조회 |
| POST | `/api/v1/interactions/favorite/{id}` | 찜 토글 |
| GET | `/api/v1/interactions/favorites` | 찜 목록 |

### 컬렉션

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/v1/collections` | 내 컬렉션 목록 |
| POST | `/api/v1/collections` | 생성 |
| GET | `/api/v1/collections/{id}` | 상세 |
| POST | `/api/v1/collections/{id}/movies` | 영화 추가 |
| DELETE | `/api/v1/collections/{id}/movies/{mid}` | 영화 제거 |

---

## 4. 추천 알고리즘

### Hybrid Scoring

```
Mood 있을 때: (0.25 × MBTI) + (0.20 × Weather) + (0.30 × Mood) + (0.25 × Personal)
Mood 없을 때: (0.35 × MBTI) + (0.25 × Weather) + (0.40 × Personal)
품질 보정: weighted_score 기반 ×0.85~1.0 연속 보정
품질 필터: weighted_score >= 6.0
```

### MBTI 매핑 (예시)

| MBTI | 선호 장르 |
|------|----------|
| INTJ | 미스터리, SF, 전략적 플롯 |
| ENFP | 로맨스, 모험, 감성 드라마 |
| ISTP | 액션, 스릴러, 기술 중심 |
| INFP | 판타지, 예술영화, 감정적 서사 |

### 날씨 매핑

| 날씨 | 추천 분위기 |
|------|------------|
| sunny | 모험, 코미디, 밝은 영화 |
| rainy | 멜로, 드라마, 감성적 영화 |
| cloudy | 힐링, 다큐멘터리, 차분한 영화 |
| snowy | 로맨스, 가족, 따뜻한 영화 |

### 기분(Mood) 매핑 (8종)

| 기분 | 한국어 | 감성 클러스터 매핑 |
|------|--------|-------------------|
| relaxed | 평온한 | healing, light |
| tense | 긴장된 | tension, energy |
| excited | 활기찬 | energy, light |
| emotional | 몽글몽글한 | romance, healing |
| imaginative | 상상에 빠진 | fantasy, deep |
| light | 유쾌한 | light, energy |
| gloomy | 울적한 | deep, healing |
| stifled | 답답한 | energy, tension |

### 개인화 추천 로직 (Personal Score)

1. **장르 분석**: 찜 + 고평점(4.0↑) 영화 장르 집계 (고평점 2배 가중치)
2. **상위 3개 장르 추출**
3. **유사 영화 보너스**: similar_movies 테이블 활용
4. **명작 보너스**: 평점 8.0↑, 투표 100↑ 영화

### 추천 태그 시스템

| 태그 | 조건 | 색상 |
|------|------|------|
| #MBTI추천 | MBTI 스코어 > 0.5 | 보라 |
| #비오는날 등 | 날씨 스코어 > 0.5 | 파랑 |
| #취향저격 | 장르 2개↑ 매칭 | 초록 |
| #비슷한영화 | similar_movies 포함 | 초록 |
| #명작 | weighted_score >= 7.5 | 노랑 |

---

## 5. 프론트엔드 페이지

| 경로 | 컴포넌트 | 기능 |
|------|----------|------|
| `/` | page.tsx | 홈, 날씨 배너, 추천 Row |
| `/login` | login/page.tsx | 로그인 |
| `/signup` | signup/page.tsx | 회원가입 + MBTI |
| `/profile` | profile/page.tsx | MBTI 변경 |
| `/movies` | movies/page.tsx | 검색, 필터, 정렬 |
| `/movies/[id]` | movies/[id]/page.tsx | 영화 상세 (동적 OG 태그) |

### 주요 컴포넌트

| 컴포넌트 | 기능 |
|----------|------|
| `Header` | 네비게이션, 검색 자동완성, 날씨 인디케이터 |
| `WeatherBanner` | 날씨 정보, 추천 메시지, 선택 버튼, 애니메이션 |
| `MovieRow` | 가로 스크롤 영화 목록, 큐레이션 서브타이틀, 새로고침 |
| `HybridMovieRow` | 맞춤 추천 전용 Row (로그인 시 표시) |
| `MovieCard` | 포스터 카드, 호버 효과 |
| `MovieModal` | 상세 정보, 별점(1~5), 찜하기 |
| `FeaturedBanner` | 대표 영화 배너, 날씨/기분 선택 UI |
| `SearchAutocomplete` | 검색 자동완성 (키보드 네비게이션, 하이라이팅) |

### Zustand 스토어

| 스토어 | 역할 |
|--------|------|
| `authStore` | 인증 상태, 로그인/로그아웃 |
| `interactionStore` | 평점/찜 상태 캐싱, Optimistic UI |

---

## 6. 날씨 테마

| 날씨 | Primary Color | 배경 | 분위기 |
|------|--------------|------|--------|
| sunny | #FFD93D | Warm gradient | 밝고 활기찬 |
| rainy | #6B7AA1 | Gray-blue | 잔잔하고 감성적 |
| cloudy | #95A5A6 | Soft gray | 편안하고 차분한 |
| snowy | #E8F4F8 | White-blue | 포근하고 로맨틱 |

---

## 7. 데이터셋

- **Source**: TMDB 기반
- **Size**: 42,917편 영화
- **cast_ko**: 100% 한글화 (Claude API 음역 변환)
- **emotion_tags**: 2-Tier 시스템 (LLM 1,711편 + 키워드 41,206편)
- **similar_movies**: 자체 유사도 계산 (429,170개 관계)

### movies 테이블 (22컬럼)

| 카테고리 | 컬럼 |
|----------|------|
| 기본 정보 (13) | id, title, title_ko, certification, runtime, vote_average, vote_count, overview, tagline, release_date, popularity, poster_path, is_adult |
| 추가 정보 (6) | director, director_ko, cast_ko, production_countries_ko, release_season, weighted_score |
| 점수 (3, JSONB) | mbti_scores, weather_scores, emotion_tags |

### 유사 영화 계산 공식

```
유사도 = 0.5×emotion코사인 + 0.3×mbti코사인 + 0.2×장르Jaccard + LLM보너스(0.05)
필터: weighted_score >= 6.0, 장르 1개 이상 겹침
```
