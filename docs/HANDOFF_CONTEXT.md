# RecFlix 프로젝트 컨텍스트 핸드오프

> 클로드 웹 새 채팅에 붙여넣기용. 2026-03-03 기준. (Phase 54 완료, v2.0.0)

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
| 총 커밋 | 290개+, Phase 54 완료 (v2.0.0) |
| 소스 파일 | Backend 60개+ (.py) / Frontend 50개+ (.ts/.tsx) |

---

## 2. 핵심 아키텍처

### 프로젝트 구조
```
backend/app/
  api/v1/
    recommendations.py        # 홈 추천 API (412줄)
    recommendation_engine.py  # Hybrid 스코어링 엔진 (396줄)
    recommendation_constants.py # 가중치/다양성 상수 (115줄)
    recommendation_cf.py      # SVD 협업 필터링 모듈
    recommendation_reason.py  # 추천 이유 생성 (239줄, 43개 템플릿)
    movies.py                 # 검색/상세/자동완성/장르/시맨틱검색
    auth.py                   # 회원가입, JWT 로그인, Kakao/Google OAuth
    users.py                  # 프로필, MBTI 설정, GDPR 삭제
    ratings.py / collections.py / interactions.py
    events.py                 # 사용자 행동 이벤트 (10종)
    ab_stats.py               # A/B 통계 유틸리티 (Z-test, Wilson CI)
    health.py                 # 헬스체크 (DB/Redis/SVD/임베딩)
    llm.py                    # Claude API 캐치프레이즈
  core/
    deps.py / security.py / config.py / exceptions.py / rate_limit.py
    http_client.py            # httpx AsyncClient 싱글톤
    logging_config.py         # structlog 구조화 로깅
  middleware/
    request_id.py             # X-Request-ID (structlog contextvars)
  models/
    movie.py / user.py / rating.py / collection.py / similar_movie.py / user_event.py
  services/
    weather.py (OpenWeatherMap + 역지오코딩) / llm.py (Claude + Redis)
    two_tower_retriever.py    # Two-Tower ANN 후보 생성 (PyTorch + FAISS)
    reranker.py               # LightGBM CTR 예측 재랭커 (76dim 피처)
    reco_logger.py            # 추천 노출 로깅 (reco_impressions)
    interleaving.py / embedding.py
backend/tests/                # pytest 테스트 스위트 (14건)
backend/alembic/              # DB 마이그레이션 (Alembic)

frontend/
  app/
    page.tsx                  # 홈 (배너 + 추천 Row + 큐레이션)
    movies/page.tsx           # 영화 검색 (필터/정렬/무한스크롤/시맨틱검색)
    movies/[id]/page.tsx      # 영화 상세 (231줄 + 4개 서브컴포넌트)
    login/ signup/ profile/ favorites/ ratings/ onboarding/ settings/
    auth/kakao/callback/ auth/google/callback/
  components/movie/
    MovieRow / HybridMovieRow / MovieCard / HybridMovieCard
    MovieModal / FeaturedBanner / MovieGrid / MovieFilters / TrailerModal
  components/layout/
    Header (날씨/기분/MBTI/프로필 드롭다운) / HeaderMobileDrawer
    MobileNav / MBTIModal / ThemeProvider
  components/weather/ WeatherBanner
  components/search/ SearchAutocomplete / SearchResults
  components/ui/ HighlightText / Skeleton
  lib/
    api.ts (24개 API 함수) / curationMessages.ts (258개 문구)
    contextCuration.ts / searchUtils.ts / constants.ts / eventTracker.ts / utils.ts
  stores/ authStore / interactionStore / themeStore / useMoodStore
  hooks/ useWeather / useInfiniteScroll / useDebounce / useImpressionTracker
```

### DB 스키마 (핵심)
```
movies: 23컬럼, 42,917행
  id(TMDB PK), title(영어), title_ko(한국어), certification, runtime,
  vote_average, vote_count, popularity, overview(한국어), tagline,
  poster_path, release_date, is_adult,
  director, director_ko, cast_ko(100% 한글, 쉼표 구분),
  production_countries_ko, release_season, weighted_score, trailer_key(YouTube ID),
  mbti_scores JSONB(16종), weather_scores JSONB(4종), emotion_tags JSONB(7종)

similar_movies: 429,170개 (영화별 Top 10)
users: 17컬럼, email UNIQUE, mbti, bcrypt password + kakao_id, google_id, experiment_group, auth_provider, onboarding_completed, preferred_genres 등
user_events: 10종 이벤트, JSONB metadata (프로덕션 적용 완료)
ratings: user_id+movie_id UNIQUE, score 0.5~5.0
collections + collection_movies: 찜 관리
genres(19), persons(97,206), keywords, countries: M:M 연결
reco_impressions: 추천 노출 로그 (12컬럼, request_id/user_id/algorithm_version/section/movie_id/rank)
reco_interactions: 추천 상호작용 로그 (10컬럼, event_type/dwell_ms/position)
reco_judgments: 오프라인 평가 라벨 (7컬럼, label_type/label_value)
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
- **시맨틱 검색**: Voyage AI 임베딩 42,917편, NumPy 코사인 유사도, 재랭킹 v2 (semantic 60% + popularity 15% + quality 25%)
- **콜드스타트**: preferred_genres 기반 fallback (상호작용 <5건 시)
- **피드백 루프**: interaction_version 캐시 무효화 (평점/찜 변경 즉시 반영)

---

## 4. CI/CD 파이프라인

- **CI**: GitHub Actions — Backend Lint (ruff) + Backend Test (pytest, ML 패키지 제외) + Frontend Build (next build)
- **CD**: GitHub Actions → `npx @railway/cli@4.30.5 up --service backend --environment production --detach`
- **Vercel**: GitHub 연동 자동 배포 (push 시)
- **Railway Token**: Project Token (Account Token 아님), GitHub Secrets `RAILWAY_TOKEN`
- **파일**: `.github/workflows/ci.yml`

---

## 5. 완료된 Phase 요약 (1~50)

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
| 38 | 02/23 | 프로덕션 DB 마이그레이션 (user_events + users 7컬럼) |
| 39-45 | 02/23 | 문서화, 설정 경량화, 안전/정확성, DB 성능, 내결함성, SEO/접근성, 코드 품질 |
| 46 | 02/23 | 추천 콜드스타트 + GDPR 계정 삭제 + 보안 강화 + Error Boundary |
| 47 | 02/23 | TMDB 트레일러 연동 (28,486편, YouTube 임베드 UI) |
| 48 | 02/24 | async 최적화 (httpx 싱글톤, bcrypt to_thread) + Alembic 마이그레이션 |
| 49 | 02/24 | 시맨틱 재랭킹 v2 + pytest 14건 + structlog 구조화 로깅 |
| 50 | 02/24 | 문서 최종화 + v1.0.0 릴리스 |
| 51 | 02/24 | 모바일 UI/UX 개선 (터치 영역 44px + thumb zone + hover-only 대응) |
| 52 | 02/25 | A/B 테스트 강화 (이벤트 사각지대 해소 + Z-test 통계 유의성 + 추가 메트릭 + 그룹 가중치) |
| 53 | 02/27 | **v2.0 ML 파이프라인 배포** (Two-Tower + LGBM + FAISS + reco_* 테이블 + CI/CD 수정 + numpy 2.x) |

---

## 6. 프로덕션 상태

### 6.1 DB 마이그레이션 — ✅ 완료
- Phase 38: user_events, users 7컬럼 + 타입 보정
- Phase 47: trailer_key 컬럼 추가 (28,486편 커버)
- Phase 48: Alembic 마이그레이션 체계 전환 (Base.metadata.create_all 제거)
- Phase 53: reco_impressions, reco_interactions, reco_judgments 3테이블 추가

### 6.2 v2.0 ML 파이프라인 — ✅ 배포 완료
- **Two-Tower Retriever**: PyTorch + FAISS (42,917 items in index)
- **LGBM Reranker**: LightGBM CTR 예측 (76dim 피처)
- **A/B 라우팅**: control→hybrid_v1, test_a→twotower_lgbm_v1, test_b→twotower_v1
- **Health**: `/api/v1/health` → two_tower: loaded, reranker: loaded, version: v2.0.0
- **Impression Logging**: 추천 노출 → reco_impressions 자동 기록

### 6.3 A/B 테스트 현황
- Phase 52: Z-test for proportions 통계 유의성 검증 (math.erf, scipy 불필요)
- Wilson score 95% 신뢰구간 (CTR CI)
- 추가 메트릭: 추천 수용률, 재방문율, 세션 이벤트, 전환 퍼널, 일별 활성
- 그룹 가중치 배정: `EXPERIMENT_WEIGHTS` 환경변수 (control:34,test_a:33,test_b:33)
- 이벤트 트래킹: 모든 사용자 상호작용 이벤트에 experiment_group 포함
- 컨텍스트 전파: 추천 섹션 → 상세 페이지 (source_section/source_position)

### 6.4 남은 수동 작업
- **OAuth 환경변수**: Railway/Vercel에 Kakao/Google OAuth 프로덕션 값 설정 필요
- **Kakao Developer Console**: 앱 도메인에 `jnsquery-reflix.vercel.app` 등록 + Redirect URI
- **Google Cloud Console**: 승인된 리디렉션 URI 추가

---

## 7. 향후 작업 후보

우선순위순:
1. **OAuth 앱 등록 완료** — Kakao/Google Developer Console 환경변수 설정 (소셜 로그인 프로덕션 활성화)
2. **PWA 지원** — 오프라인 캐싱, 앱 설치 프롬프트, Service Worker
3. **추천 알고리즘 평가 대시보드** — A/B 테스트 결과 시각화 (CTR, 전환율, 체류시간)
4. **사용자 리뷰/코멘트 기능** — 영화별 한줄평

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
| Railway LFS 413 | `.railwayignore`로 모델 파일 제외 |
| numpy 2.x SVD pickle | `numpy>=2.0.0` 필수 (numpy._core.numeric) |

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
| 아키텍처 | `docs/ARCHITECTURE.md` | 시스템 구조/데이터 흐름/캐시/인증 |
| 진행 상황 | `PROGRESS.md` | Phase 1-50 상세 |
| 변경 이력 | `CHANGELOG.md` | 날짜별 변경사항 |
| 추천 로직 | `docs/RECOMMENDATION_LOGIC.md` | 알고리즘 상세 |
| 아키텍처 결정 | `DECISION.md` | 7개 주요 결정 |
| 프로젝트 리뷰 | `docs/PROJECT_REVIEW.md` | 달성도 분석 + 고도화 로드맵 |
| 스킬 인덱스 | `.claude/skills/INDEX.md` | 8개 도메인 스킬 |
