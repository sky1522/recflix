# RecFlix 시스템 아키텍처

## 전체 구조

```
┌──────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                        │
│  Geolocation → useWeather → 날씨 기반 추천                       │
│  Zustand (authStore, interactionStore) → Optimistic UI           │
│  eventTracker → Beacon API → 행동 이벤트 배치 전송                │
└──────────────────┬───────────────────────────────────────────────┘
                   │ HTTPS
┌──────────────────▼───────────────────────────────────────────────┐
│                    Vercel (Frontend)                              │
│  Next.js 14 App Router                                           │
│  - SSR: generateMetadata (OG 메타태그)                            │
│  - CSR: 홈/검색/상세/프로필 (동적 콘텐츠)                          │
│  - Sentry (에러 모니터링)                                         │
└──────────────────┬───────────────────────────────────────────────┘
                   │ REST API (/api/v1/*)
┌──────────────────▼───────────────────────────────────────────────┐
│                    Railway (Backend)                              │
│  FastAPI + Uvicorn                                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Middleware Stack                                             │ │
│  │  CORS → RequestIDMiddleware → slowapi Rate Limiter          │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ API Router (/api/v1/)                                       │ │
│  │  recommendations │ movies │ auth │ ratings │ collections    │ │
│  │  events │ users │ weather │ health │ llm │ interactions     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Core Services                                               │ │
│  │  recommendation_engine │ semantic_search │ diversity         │ │
│  │  recommendation_cf │ recommendation_reason                  │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  structlog (JSON/console) │ Sentry │ Alembic                    │
└────────┬────────────┬────────────┬───────────────────────────────┘
         │            │            │
    ┌────▼────┐  ┌────▼────┐  ┌───▼──────────────┐
    │PostgreSQL│  │  Redis  │  │  External APIs   │
    │ 42,917편 │  │  캐시   │  │  Voyage AI       │
    │ 6 tables │  │  세션   │  │  Claude API      │
    │ GIN idx  │  │  JTI   │  │  OpenWeatherMap   │
    └─────────┘  └─────────┘  │  TMDB API        │
                              └──────────────────┘
```

## 데이터 흐름: 홈 추천 요청

```
1. 사용자 브라우저
   ├── Geolocation API → 위도/경도 획득
   ├── useWeather() → GET /weather?lat=&lon= → 날씨 상태 (sunny/rainy/...)
   └── 홈 페이지 로드

2. GET /api/v1/recommendations?weather=sunny&mood=relaxed&mbti=INFP
   ├── JWT 검증 (로그인 시) → current_user
   ├── 품질 필터: weighted_score >= 6.0
   ├── 연령등급 필터: age_rating 매핑
   └── 섹션별 추천 생성:
       ├── popular: popularity DESC (TOP 50, 셔플 20)
       ├── top_rated: weighted_score DESC (TOP 50)
       ├── weather: weather_scores JSONB 쿼리
       ├── mood: emotion_tags JSONB 쿼리
       ├── mbti: mbti_scores JSONB 쿼리
       └── hybrid: 5축 하이브리드 스코어링 (로그인 시)

3. 하이브리드 스코어링 (recommendation_engine.py)
   ├── MBTI Score: mbti_scores[user.mbti] x 가중치
   ├── Weather Score: weather_scores[weather] x 가중치
   ├── Mood Score: emotion_tags[cluster] x 가중치
   ├── Personal Score: 찜/고평점 장르 매칭 x 가중치
   ├── CF Score: SVD item_bias 정규화 x 가중치
   └── Quality: weighted_score 연속 보정 (x0.85~1.0)

4. 다양성 후처리 (diversity.py)
   ├── diversify_by_genre: 장르 캡 (연속 동일 장르 제한)
   ├── ensure_freshness: 신선도 보장 (최신 영화 우대)
   ├── inject_serendipity: 의외의 발견 삽입
   └── deduplicate_section: 섹션 간 중복 제거

5. 추천 이유 생성 (recommendation_reason.py)
   └── 43개 템플릿 매칭 → 한국어 추천 이유 텍스트

6. 응답 → 프론트엔드 렌더링
   ├── MovieRow: 가로 스크롤 영화 카드
   ├── HybridMovieRow: 추천 태그 + 추천 이유
   └── 큐레이션 서브타이틀 (258개 문구 중 매칭)
```

## 데이터베이스 스키마

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   movies    │     │    users     │     │  user_events │
│ (42,917행)  │     │  (17컬럼)    │     │  (10종)      │
├─────────────┤     ├──────────────┤     ├──────────────┤
│ id (PK)     │     │ id (PK)      │     │ id (PK)      │
│ title       │     │ email (UQ)   │     │ user_id (FK) │
│ title_ko    │     │ hashed_pw    │     │ event_type   │
│ overview    │     │ mbti         │     │ event_data   │
│ poster_path │     │ kakao_id     │     │  (JSONB)     │
│ vote_avg    │     │ google_id    │     │ session_id   │
│ popularity  │     │ auth_provider│     │ page_url     │
│ cast_ko     │     │ experiment_  │     │ created_at   │
│ director_ko │     │   group      │     └──────────────┘
│ trailer_key │     │ preferred_   │
│ mbti_scores │     │   genres     │     ┌──────────────┐
│  (JSONB)    │     │ onboarding_  │     │   ratings    │
│ weather_    │     │   completed  │     ├──────────────┤
│  scores     │     └──────┬───────┘     │ user_id (FK) │
│  (JSONB)    │            │             │ movie_id(FK) │
│ emotion_    │            │             │ score (0.5~5)│
│  tags       │     ┌──────▼───────┐     │ (UQ: u+m)   │
│  (JSONB)    │     │ collections  │     └──────────────┘
│ weighted_   │     ├──────────────┤
│  score      │     │ user_id (FK) │     ┌───────────────┐
└──────┬──────┘     │ name         │     │similar_movies │
       │            └──────────────┘     ├───────────────┤
       │                                 │ movie_id (FK) │
  ┌────▼─────┐                           │ similar_id(FK)│
  │  M:M     │                           │ similarity    │
  │ tables   │                           │ (429,170행)   │
  ├──────────┤                           └───────────────┘
  │ genres   │
  │ persons  │
  │ keywords │
  │ countries│
  └──────────┘
```

### JSONB 인덱스 (GIN)
```sql
CREATE INDEX idx_movies_mbti ON movies USING GIN(mbti_scores);
CREATE INDEX idx_movies_weather ON movies USING GIN(weather_scores);
CREATE INDEX idx_movies_emotion ON movies USING GIN(emotion_tags);
```

## 캐시 전략

| 캐시 계층 | TTL | 대상 |
|-----------|-----|------|
| **Redis** | 30분 | 날씨 API 응답 |
| **Redis** | 1시간 | 자동완성 결과 |
| **Redis** | 24시간 | LLM 캐치프레이즈 |
| **Redis** | 7일 | refresh_token JTI (토큰 회전) |
| **프로세스 캐시** | 앱 수명 | 시맨틱 검색 임베딩 (NumPy 배열) |
| **프로세스 캐시** | 앱 수명 | SVD 모델 (item_bias, global_mean) |
| **localStorage** | 10분 | 날씨 데이터 (프론트엔드) |
| **localStorage** | 영속 | 인증 토큰 (Zustand persist) |

## 인증 흐름

### JWT + Refresh Token 회전
```
1. POST /auth/login → { access_token (30분), refresh_token (7일) }
2. refresh_token JTI를 Redis에 저장 (1회용)
3. access_token 만료 시:
   POST /auth/refresh → 새 access_token + 새 refresh_token
   이전 JTI 무효화 + 새 JTI 저장
4. 탈취 감지: 이미 사용된 JTI로 요청 시 → 전체 세션 무효화
```

### OAuth 소셜 로그인
```
1. Frontend → 카카오/Google 인증 페이지 리다이렉트
2. 인증 성공 → 콜백 페이지 (code 파라미터)
3. POST /auth/kakao (or /auth/google) { code }
4. Backend → OAuth 제공자에 토큰 교환 → 사용자 정보 조회
5. DB에 사용자 생성/조회 → JWT 발급
```

## 외부 서비스 의존성

| 서비스 | 용도 | 필수 여부 | 비용 |
|--------|------|-----------|------|
| **OpenWeatherMap** | 실시간 날씨 + 역지오코딩 | 권장 | 무료 (1,000 calls/day) |
| **Voyage AI** | 시맨틱 검색 임베딩 생성 (1회) | 선택 | ~$2 (42,917편) |
| **Claude API** | 감정 태그 분석 + 캐치프레이즈 | 선택 | ~$12 (emotion_tags 1,711편) |
| **TMDB API** | 트레일러 수집 (1회) | 선택 | 무료 |
| **Sentry** | 에러 모니터링 | 선택 | 무료 (5K events/month) |

모든 외부 서비스는 graceful degradation — 설정되지 않거나 장애 시 해당 기능만 비활성화.

## CI/CD 파이프라인

```
git push origin main
       │
       ▼
  GitHub Actions
  ┌─────────────────────────────────────────┐
  │  backend-lint    : ruff check (critical)│
  │  backend-test    : pytest -v --tb=short │
  │  backend-typecheck: pyright (optional)  │
  │  frontend-build  : next build           │
  └────────────────┬────────────────────────┘
                   │ all pass
                   ▼
  deploy-backend: railway up --service backend
  deploy-frontend: Vercel GitHub 연동 (자동)
```

## 로깅

- **structlog** — stdlib logging 통합
- **Production**: JSON one-line (Railway 로그 파싱)
- **Development**: Colored console (human-readable)
- **X-Request-ID**: 모든 요청에 UUID 바인딩 → 로그 추적
- **Noisy loggers**: uvicorn.access, httpx → WARNING 레벨
