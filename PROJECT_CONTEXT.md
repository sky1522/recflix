# RecFlix 프로젝트 컨텍스트

실시간 컨텍스트(날씨/기분)와 성격 특성(MBTI)을 결합한 초개인화 영화 큐레이션 플랫폼

---

## 0. 배포 정보 (2026-02-03)

| 서비스 | URL |
|--------|-----|
| Frontend (Vercel) | https://frontend-eight-gules-78.vercel.app |
| Backend API (Railway) | https://backend-production-cff2.up.railway.app |
| API Docs | https://backend-production-cff2.up.railway.app/docs |
| GitHub | https://github.com/sky1522/recflix |

**데이터**: 32,625편 영화 (Railway PostgreSQL에 마이그레이션 완료)

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

-- 영화
movies (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    title_ko VARCHAR(255),
    certification VARCHAR(10),
    runtime INTEGER,
    vote_average DECIMAL(3,1),
    vote_count INTEGER,
    popularity DECIMAL(10,2),
    overview TEXT,
    overview_ko TEXT,
    tagline VARCHAR(500),
    poster_path VARCHAR(255),
    release_date DATE,
    is_adult BOOLEAN DEFAULT FALSE,
    mbti_scores JSONB,      -- {"INTJ": 0.8, "ENFP": 0.6, ...}
    weather_scores JSONB,   -- {"sunny": 0.7, "rainy": 0.9, ...}
    emotion_tags JSONB,     -- {"healing": 0.8, "tension": 0.3, ...}
    created_at TIMESTAMP DEFAULT NOW()
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
Score = (0.35 × MBTI) + (0.25 × Weather) + (0.40 × Personal)
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
| #명작 | 평점 8.0↑ | 노랑 |

---

## 5. 프론트엔드 페이지

| 경로 | 컴포넌트 | 기능 |
|------|----------|------|
| `/` | page.tsx | 홈, 날씨 배너, 추천 Row |
| `/login` | login/page.tsx | 로그인 |
| `/signup` | signup/page.tsx | 회원가입 + MBTI |
| `/profile` | profile/page.tsx | MBTI 변경 |
| `/movies` | movies/page.tsx | 검색, 필터, 정렬 |

### 주요 컴포넌트

| 컴포넌트 | 기능 |
|----------|------|
| `Header` | 네비게이션, 검색, 날씨 인디케이터 |
| `WeatherBanner` | 날씨 정보, 추천 메시지, 선택 버튼, 애니메이션 |
| `MovieRow` | 가로 스크롤 영화 목록 |
| `MovieCard` | 포스터 카드, 호버 효과 |
| `MovieModal` | 상세 정보, 별점(1~5), 찜하기 |
| `FeaturedBanner` | 대표 영화 배너 |

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
- **Size**: 32,625편 영화
- **File**: `data/raw/MOVIE_FINAL_FIXED_TITLES.csv`

### 주요 컬럼

| 카테고리 | 컬럼 |
|----------|------|
| 기본 정보 | id, title, title_ko, certification, runtime, release_date |
| 평가 | vote_average, vote_count, popularity |
| 텍스트 | overview, overview_ko, tagline, keywords |
| 관계 | genres, cast, director, similar_movie_ids |
| 장르 플래그 | SF, 가족, 공포, 드라마, 로맨스, 스릴러, 액션, 코미디 등 |
