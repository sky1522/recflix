# RecFlix

실시간 컨텍스트(날씨/기분)와 MBTI를 결합한 초개인화 영화 큐레이션 플랫폼.
https://jnsquery-reflix.vercel.app

## 기술스택

Frontend: Next.js 14 App Router + TailwindCSS + Framer Motion + Zustand (Vercel 배포)
Backend: FastAPI + SQLAlchemy + Pydantic + Redis + httpx (Railway 배포)
DB: PostgreSQL 16 (Railway) + Redis (캐싱)
영화 데이터: 42,917편, TMDB 기반

## 핵심 구조

```
backend/
  app/
    api/v1/
      recommendations.py   # ★ 하이브리드 추천 엔진 (770 LOC)
      movies.py             # 검색, 상세, 자동완성, 장르
      weather.py            # 날씨 API 라우터
      auth.py               # 회원가입, JWT 로그인, 토큰 갱신
      users.py              # 프로필, MBTI 설정
      ratings.py            # 평점 CRUD (0.5~5.0)
      collections.py        # 찜 컬렉션 관리
      interactions.py       # 통합 상호작용 (찜/평점 상태)
      llm.py                # Claude API 캐치프레이즈
      router.py             # API 라우터 통합
    core/
      deps.py               # DI (get_db, get_current_user)
      security.py           # JWT 토큰 생성/검증 (bcrypt)
    models/
      movie.py              # Movie + Genre + Person + Keyword + Country
      user.py               # User
      rating.py             # Rating (user_id + movie_id UNIQUE)
      collection.py         # Collection + CollectionMovie
      similar_movie.py      # SimilarMovie (자기참조 M:M)
    schemas/                # Pydantic 요청/응답 스키마
    services/
      weather.py            # OpenWeatherMap + 역지오코딩 + 70개 한글 도시명
      llm.py                # Claude API + Redis 캐싱
    config.py               # pydantic-settings (env 기반)
    database.py             # SQLAlchemy engine + session
  scripts/
    compute_similar_movies.py    # 유사 영화 자체 계산 (코사인+Jaccard)
    llm_emotion_tags.py          # Claude API 감성 분석
    regenerate_emotion_tags.py   # 키워드 기반 감성 태그
    transliterate_cast_names.py  # 출연진 한글 음역
    transliterate_persons.py     # persons 테이블 한글화

frontend/
  app/
    page.tsx               # ★ 홈 (배너 + 추천 Row + 큐레이션)
    movies/
      page.tsx             # 영화 검색 (필터, 정렬, 무한스크롤)
      [id]/page.tsx        # 영화 상세 (622 LOC, 동적 OG 태그)
    login/page.tsx         # 로그인
    signup/page.tsx        # 회원가입 + MBTI 선택
    profile/page.tsx       # 프로필 + MBTI 변경
    favorites/page.tsx     # 찜 목록
    ratings/page.tsx       # 내 평점 목록
  components/
    movie/
      MovieRow.tsx         # 가로 스크롤 영화 Row + 큐레이션 서브타이틀
      HybridMovieRow.tsx   # 맞춤 추천 Row (로그인 시)
      MovieCard.tsx        # 포스터 카드 + 호버 효과
      MovieModal.tsx       # 상세 모달 (별점, 찜)
      FeaturedBanner.tsx   # 대표 영화 배너
      HybridMovieCard.tsx  # 추천 태그 표시 카드
    layout/
      Header.tsx           # 네비게이션 + 검색 + 날씨 인디케이터
    weather/
      WeatherBanner.tsx    # 날씨 정보 + 테마 전환
    search/
      SearchAutocomplete.tsx # 자동완성 (키보드, 하이라이팅)
      HighlightText.tsx    # 검색어 하이라이팅
  lib/
    api.ts                 # 24개 API 함수 (fetchAPI 래퍼)
    curationMessages.ts    # 258개 큐레이션 문구
    contextCuration.ts     # 시간대/계절/기온 컨텍스트 감지
    constants.ts           # 캐시 키, 매직넘버 상수
    utils.ts               # 유틸리티 함수
  stores/
    authStore.ts           # Zustand: 인증 상태
    interactionStore.ts    # Zustand: 찜/평점 Optimistic UI
  hooks/
    useWeather.ts          # Geolocation + localStorage 캐시
    useInfiniteScroll.ts   # 무한스크롤
    useDebounce.ts         # 디바운스
  types/
    index.ts               # TypeScript 타입 정의
```

## DB 모델

```
movies: 22컬럼, 42,917행
  id=TMDB PK, title(영어), title_ko(한국어), certification, runtime,
  vote_average, vote_count, popularity, overview(한국어), tagline,
  poster_path, release_date, is_adult,
  director, director_ko, cast_ko(100% 한글, 쉼표 구분),
  production_countries_ko, release_season, weighted_score,
  mbti_scores JSONB(16종), weather_scores JSONB(4종), emotion_tags JSONB(7종)
  GIN 인덱스: mbti_scores, weather_scores, emotion_tags

similar_movies: 429,170개 관계 (영화별 Top 10, 자기참조 M:M)
users: email UNIQUE, mbti VARCHAR(4), bcrypt password
ratings: user_id+movie_id UNIQUE, score DECIMAL(2,1) 0.5~5.0
collections + collection_movies: 찜 관리
genres(19종), persons(97,206), keywords, countries: M:M 연결 테이블
```

**주의 - CSV → DB 컬럼 매핑:**
- CSV `title`(한국어) → DB `title_ko`
- CSV `title_ko_en`(영어) → DB `title`
- `cast_ko`: 쉼표 구분 문자열, 프론트엔드에서 `.split(", ")`로 파싱
- `persons` 테이블: API로 반환되지만 프론트엔드 미사용

## 배포

```
Frontend: Vercel (https://jnsquery-reflix.vercel.app)
Backend:  Railway (https://backend-production-cff2.up.railway.app)
DB:       Railway PostgreSQL + Redis
API Docs: https://backend-production-cff2.up.railway.app/docs
GitHub:   https://github.com/sky1522/recflix
```

```bash
# Backend → Railway
cd backend && railway up

# Frontend → Vercel
cd frontend && npx vercel --prod

# DB 프로덕션 복원 (로컬 → Railway)
PGPASSWORD=recflix123 pg_dump -h localhost -U recflix -d recflix --no-owner --no-acl -Fc -f dump.dump
PGPASSWORD=<railway_pw> pg_restore -h shinkansen.proxy.rlwy.net -p 20053 -U postgres -d railway --clean --if-exists --no-owner --no-acl dump.dump
```

## 로컬 실행

```bash
# Backend (포트 8000) — 필수: PostgreSQL(5432), Redis/Memurai(6379)
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend (포트 3000)
cd frontend && npm run dev
```

## 규칙

1. 작업 완료 시: `git add -A && git commit -m 'type(scope): 설명' && git push origin HEAD:main`
2. 결과는 `claude_results.md`에 저장 (날짜, 변경 파일, 핵심 변경사항, 검증 결과)
3. Python: `logging` 모듈 사용 (`print()` 금지), Ruff 린트/포맷, 함수 100줄 이내
4. TypeScript: ESLint core-web-vitals, 상수는 `constants.ts`, 모듈 레벨 mutable 변수 금지
5. 환경변수에 시크릿 하드코딩 금지 (`.env` 파일에만)
6. DB 스키마 변경 시 JSONB GIN 인덱스 확인
7. 추천 알고리즘 변경 시 `docs/RECOMMENDATION_LOGIC.md` 동기화
8. 복잡한 작업은 `.claude/skills/workflow.md`의 RPI 프로세스를 따른다

## 알려진 이슈 패턴

- Vercel Image Optimization 무료 한도 → `unoptimized: true` 설정됨
- Windows venv: Git Bash에서 `./venv/Scripts/python.exe` 사용
- CSV BOM: `encoding='utf-8-sig'`로 읽기
- Railway DB proxy: `shinkansen.proxy.rlwy.net:20053`
- Windows 대용량 JSON 쓰기: 원자적 쓰기(tmp+rename) 패턴 사용
- 프론트엔드 CSR 페이지: WebFetch로 동적 콘텐츠 확인 불가 → API 직접 호출로 검증

## 스킬

상세 도메인 지식은 `.claude/skills/` 참조. 인덱스: `.claude/skills/INDEX.md`
