# RecFlix 프로젝트 컨텍스트 핸드오프

> 클로드 웹 새 채팅에 붙여넣기용. 2026-02-23 기준.

---

## 1. 프로젝트 개요

**RecFlix** — MBTI/날씨/기분 기반 초개인화 영화 추천 서비스 (Netflix 클론 UI)

| 항목 | 내용 |
|------|------|
| Frontend | Next.js 14 App Router + TailwindCSS + Framer Motion + Zustand |
| Backend | FastAPI + SQLAlchemy + Pydantic + Redis + httpx |
| DB | PostgreSQL 16 + Redis (캐싱) |
| 영화 데이터 | 42,917편 (TMDB 기반) |
| Frontend 배포 | Vercel — https://jnsquery-reflix.vercel.app |
| Backend 배포 | Railway — https://backend-production-cff2.up.railway.app |
| API 문서 | https://backend-production-cff2.up.railway.app/docs |
| GitHub | https://github.com/sky1522/recflix |
| 총 커밋 | 210개, Phase 37까지 완료 |
| 소스 파일 | Backend 52개 (.py) / Frontend 46개 (.ts/.tsx) |

---

## 2. 핵심 아키텍처

### 프로젝트 구조
```
backend/app/
  api/v1/
    recommendations.py        # 홈 추천 API (347줄)
    recommendation_engine.py  # Hybrid 스코어링 엔진 (330줄)
    recommendation_constants.py # 가중치 상수 (76줄)
    recommendation_cf.py      # SVD 협업 필터링 모듈
    recommendation_reason.py  # 추천 이유 생성 (228줄, 43개 템플릿)
    movies.py                 # 검색/상세/자동완성/장르/시맨틱검색
    auth.py                   # 회원가입, JWT 로그인, 토큰 갱신
    users.py                  # 프로필, MBTI 설정
    ratings.py / collections.py / interactions.py
    events.py                 # 사용자 행동 이벤트 (10종)
    health.py                 # 헬스체크 (DB/Redis/SVD/임베딩)
    llm.py                    # Claude API 캐치프레이즈
  core/
    deps.py / security.py / config.py / exceptions.py / rate_limit.py
  models/
    movie.py / user.py / rating.py / collection.py / similar_movie.py / user_event.py
  services/
    weather.py (OpenWeatherMap + 역지오코딩) / llm.py (Claude + Redis)

frontend/
  app/
    page.tsx                  # 홈 (배너 + 추천 Row + 큐레이션)
    movies/page.tsx           # 영화 검색 (필터/정렬/무한스크롤/시맨틱검색)
    movies/[id]/page.tsx      # 영화 상세 (231줄 + 4개 서브컴포넌트)
    login/ signup/ profile/ favorites/ ratings/ onboarding/
    auth/kakao/callback/ auth/google/callback/
  components/movie/
    MovieRow / HybridMovieRow / MovieCard / HybridMovieCard
    MovieModal / FeaturedBanner
  components/layout/ Header / MobileNav
  components/weather/ WeatherBanner
  components/search/ SearchAutocomplete / HighlightText
  lib/
    api.ts (24개 API 함수) / curationMessages.ts (258개 문구)
    contextCuration.ts / constants.ts / eventTracker.ts / utils.ts
  stores/ authStore / interactionStore
  hooks/ useWeather / useInfiniteScroll / useDebounce / useImpressionTracker
```

### DB 스키마 (핵심)
```
movies: 22컬럼, 42,917행
  id(TMDB PK), title(영어), title_ko(한국어), certification, runtime,
  vote_average, vote_count, popularity, overview(한국어), tagline,
  poster_path, release_date, is_adult,
  director, director_ko, cast_ko(100% 한글, 쉼표 구분),
  production_countries_ko, release_season, weighted_score,
  mbti_scores JSONB(16종), weather_scores JSONB(4종), emotion_tags JSONB(7종)

similar_movies: 429,170개 (영화별 Top 10)
users: email UNIQUE, mbti, bcrypt password + kakao_id, google_id, experiment_group 등
user_events: 10종 이벤트, JSONB metadata (★ 프로덕션 미생성)
ratings: user_id+movie_id UNIQUE, score 0.5~5.0
collections + collection_movies: 찜 관리
genres(19), persons(97,206), keywords, countries: M:M 연결
```

**주의 - CSV→DB 매핑**: CSV `title`(한국어) → DB `title_ko` / CSV `title_ko_en`(영어) → DB `title`

---

## 3. 추천 알고리즘 (Hybrid v3)

### 가중치
- **CF 활성화 + Mood**: MBTI 0.20 + Weather 0.15 + Mood 0.25 + Personal 0.15 + CF 0.25
- **CF 활성화 + Mood 없음**: MBTI 0.25 + Weather 0.20 + Personal 0.30 + CF 0.25
- **CF 비활성화**: 기존 v2 (MBTI 0.25~0.35 + Weather 0.20~0.25 + Mood 0.30 + Personal 0.25~0.40)

### 핵심 메커니즘
- **품질 필터**: weighted_score >= 6.0
- **품질 보정**: ws 6.0~9.0 → ×0.85~1.0 연속 보정
- **emotion_tags 2-Tier**: LLM 1,711편(최대 1.0) + 키워드 41,206편(최대 0.7)
- **30% LLM 보장**: 추천 풀에서 LLM 분석 영화 최소 30%
- **기분 8종**: relaxed/tense/excited/emotional/imaginative/light/gloomy/stifled
- **CF**: MovieLens 25M → SVD (k=100, RMSE 0.8768), item_bias 기반 품질 시그널
- **추천 이유**: 템플릿 기반 43개 패턴 (MBTI 11 + Weather 12 + Mood 10 + Quality 4 + Compound 6)
- **다양성 정책**: 장르 다양성 + 신선도 가중치 + serendipity + 중복 제거
- **시맨틱 검색**: Voyage AI 임베딩 42,917편, NumPy 코사인 유사도

---

## 4. CI/CD 파이프라인

- **CI**: GitHub Actions — Backend Lint (ruff 0.1.13) + Frontend Build (next build)
- **CD**: GitHub Actions → `railway up --service backend --environment production --detach`
- **Vercel**: GitHub 연동 자동 배포 (push 시)
- **Railway Token**: Project Token (Account Token 아님), GitHub Secrets `RAILWAY_TOKEN`
- **파일**: `.github/workflows/ci.yml`

---

## 5. 완료된 Phase 요약 (1~37)

| Phase | 날짜 | 핵심 |
|-------|------|------|
| 1-8 | ~02/02 | 기본 기능 (Backend API, Frontend, 날씨, 검색, Hybrid 추천, 모바일, 배포설정) |
| 9 | 02/03 | 프로덕션 배포 (Vercel + Railway + PostgreSQL + Redis) |
| 10 | 02/04 | LLM 캐치프레이즈, UX 개선 |
| 11 | 02/09 | emotion_tags 고도화, 기분 추천 |
| 12 | 02/10 | Vercel 도메인 변경 (jnsquery-reflix) |
| 13-14 | 02/10 | 42,917편 마이그레이션, 6컬럼 추가, 알고리즘 v2 튜닝, 연령등급 |
| 15-16 | 02/11 | 보안 DB 교체, Favicon, 날씨 한글화, 배너 개선 |
| 17 | 02/12 | DB 스키마 정리 (24→22컬럼) |
| 18-19 | 02/12~13 | cast_ko 100% 한글화 (Claude API $13.47) |
| 20-26 | 02/13 | SEO OG태그, 유사영화 자체계산, 검색강화, 큐레이션 258개 문구, 기분 8종 |
| 27-28 | 02/19 | CLAUDE.md + skills 환경, 코드 리팩토링 |
| 29 | 02/19 | Sentry + Rate Limiting + 에러 핸들링 표준화 |
| 30 | 02/19 | 사용자 행동 이벤트 (10종, 배치 전송, Beacon API) |
| 31 | 02/19 | SVD 협업 필터링 (MovieLens 25M, CF 25% 통합) |
| 32 | 02/19 | A/B 테스트 + 소셜 로그인 (Kakao/Google) + 온보딩 |
| 33 | 02/20 | 시맨틱 검색 (Voyage AI 임베딩) |
| 34 | 02/20 | 추천 다양성/신선도 정책 |
| 35 | 02/20 | SVD 모델 프로덕션 배포 (Dockerfile LFS) |
| 36 | 02/20 | 헬스체크 + CI/CD (GitHub Actions) |
| 37 | 02/20 | 추천 이유 생성 (템플릿 43개 패턴) |

---

## 6. 프로덕션 미반영 사항 (중요!)

### 6.1 DB 마이그레이션 필요 (Phase 29-32 스키마)
Phase 29~32에서 코드에 추가했지만 **프로덕션 Railway DB에 아직 미적용**:
- `user_events` 테이블 생성 (사용자 행동 이벤트)
- `users` 테이블 6컬럼 추가:
  - `experiment_group` (A/B 테스트)
  - `kakao_id`, `google_id` (소셜 로그인)
  - `profile_image`
  - `onboarding_completed`
  - `preferred_genres` (온보딩 장르 선택)
- 마이그레이션 SQL: `backend/scripts/migrate_phase4.sql`

**→ 소셜 로그인/온보딩/A/B 테스트가 프로덕션에서 동작하려면 필수**

---

## 7. 향후 작업 후보

우선순위순:
1. **프로덕션 DB 마이그레이션** — Phase 29-32 스키마 적용 (소셜 로그인/온보딩 활성화)
2. **PWA 지원** — 오프라인 캐싱, 앱 설치 프롬프트, Service Worker
3. **추천 알고리즘 평가 대시보드** — A/B 테스트 결과 시각화 (CTR, 전환율, 체류시간)
4. **사용자 리뷰/코멘트 기능** — 영화별 한줄평
5. **OAuth 앱 등록 완료** — Kakao/Google Developer Console 환경변수

---

## 8. 해결한 주요 이슈 패턴 (반복 참고)

| 이슈 | 해결 |
|------|------|
| Vercel Image Optimization 한도 | `unoptimized: true` |
| Windows venv | `./venv/Scripts/python.exe` |
| CSV BOM | `encoding='utf-8-sig'` |
| Railway DB proxy | `shinkansen.proxy.rlwy.net:20053` |
| Railway CD 토큰 | **Project Token** (Account Token 아님) |
| numpy 2.x pickle | numpy/scipy 버전 맞춤 |
| 소셜 로그인 OAuth 400 | Vercel 환경변수 `\n` → `.trim()` |
| Pydantic EmailStr `.local` | `@noreply.example.com` |
| CORS 500 에러 | 코드-DB 불일치 → 재배포 |
| 대용량 JSON 쓰기 (Windows) | 원자적 쓰기 (tmp+rename) |
| CSR 페이지 검증 | WebFetch 불가 → API 직접 호출 |

---

## 9. 개발 규칙

1. 커밋: `git add -A && git commit -m 'type(scope): 설명' && git push origin HEAD:main`
2. 결과 기록: `claude_results.md`
3. Python: `logging` 모듈 (print 금지), Ruff 린트, 함수 100줄↓, 타입 힌트 필수
4. TypeScript: ESLint, `any` 금지, 상수는 `constants.ts`, 모듈 레벨 mutable 변수 금지
5. 코드 품질: 파일 500줄↓, 함수 50줄↓, 단일 책임
6. DB 스키마 변경 시 JSONB GIN 인덱스 확인
7. 추천 알고리즘 변경 시 `docs/RECOMMENDATION_LOGIC.md` 동기화
8. 환경변수에 시크릿 하드코딩 금지

---

## 10. 배포 명령어

```bash
# Backend (CI/CD 자동, 수동 필요 시)
cd backend && railway up --service backend --environment production

# Frontend (GitHub push로 자동, 수동 필요 시)
cd frontend && npx vercel --prod

# DB 프로덕션 복원
PGPASSWORD=recflix123 pg_dump -h localhost -U recflix -d recflix --no-owner --no-acl -Fc -f dump.dump
PGPASSWORD=<railway_pw> pg_restore -h shinkansen.proxy.rlwy.net -p 20053 -U postgres -d railway --clean --if-exists --no-owner --no-acl dump.dump

# 로컬 실행
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

---

## 11. 참고 문서

| 문서 | 경로 | 설명 |
|------|------|------|
| 프로젝트 규칙 | `CLAUDE.md` | 구조/규칙/이슈패턴 (루트) |
| 진행 상황 | `PROGRESS.md` | Phase 1-37 상세 |
| 변경 이력 | `CHANGELOG.md` | 날짜별 변경사항 |
| 추천 로직 | `docs/RECOMMENDATION_LOGIC.md` | 알고리즘 상세 |
| 아키텍처 결정 | `DECISION.md` | 7개 주요 결정 |
| 프로젝트 리뷰 | `docs/PROJECT_REVIEW.md` | 달성도 분석 + 고도화 로드맵 |
| 스킬 인덱스 | `.claude/skills/INDEX.md` | 8개 도메인 스킬 |
