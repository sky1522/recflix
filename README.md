# RecFlix

**MBTI x 날씨 x 기분 기반 초개인화 영화 추천 플랫폼**

42,917편 영화 데이터베이스에서 사용자의 성격(MBTI), 실시간 날씨, 현재 기분을 조합하여
개인 맞춤 영화를 추천하는 풀스택 웹 서비스입니다.

| 서비스 | URL |
|--------|-----|
| **Frontend** | https://jnsquery-reflix.vercel.app |
| **Backend API** | https://backend-production-cff2.up.railway.app |
| **API Docs** | https://backend-production-cff2.up.railway.app/docs |
| **GitHub** | https://github.com/sky1522/recflix |

---

## 주요 기능

### 추천 시스템
- **하이브리드 추천 엔진** — MBTI + Weather + Mood + CF + Personal 5축 스코어링
- **SVD 협업 필터링** — MovieLens 25M 기반 (50K users x 17.5K items, RMSE 0.8768)
- **시맨틱 검색** — Voyage AI 임베딩 42,917편, NumPy 코사인 유사도
- **다양성 후처리** — 장르 캡, 신선도 보장, 세렌디피티 삽입, 섹션 간 중복 제거
- **추천 이유 생성** — 43개 템플릿 기반 한국어 추천 이유 ($0, 0ms)
- **자체 유사 영화** — emotion/mbti/장르 복합 유사도 (429,170개 관계)
- **콜드스타트 대응** — 인기도 fallback + 온보딩 2단계

### 콘텐츠
- **42,917편 영화 DB** — TMDB 기반, 22컬럼, 100% 한글화
- **YouTube 트레일러** — 28,486편 커버 (66.4%)
- **감정 태그** — LLM 1,711편 + 키워드 41,206편 (7대 클러스터)
- **258개 큐레이션 문구** — 시간대/계절/기온/날씨/기분/MBTI별 동적 서브타이틀

### 사용자 기능
- **소셜 로그인** — 카카오, Google OAuth
- **MBTI 프로필** — 16유형별 추천 가중치
- **별점 평가** — 0.5~5.0 (Optimistic UI)
- **찜하기** — 컬렉션 관리
- **온보딩** — 장르 선택 + 영화 평가 2단계

### 인프라
- **CI/CD** — GitHub Actions (lint + test + build + Railway CD)
- **구조화 로깅** — structlog (prod: JSON, dev: colored console) + X-Request-ID
- **에러 모니터링** — Sentry (backend + frontend)
- **Rate Limiting** — slowapi (39개 엔드포인트)
- **A/B 테스트** — 3그룹 분기 (control/test_a/test_b)
- **Alembic 마이그레이션** — DB 스키마 버전 관리

---

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| **Frontend** | Next.js 14 (App Router), TypeScript, TailwindCSS, Framer Motion, Zustand |
| **Backend** | FastAPI, SQLAlchemy 2.0, Pydantic v2, structlog |
| **Database** | PostgreSQL 16, Redis (캐싱) |
| **AI/ML** | Voyage AI (임베딩), Claude API (감정 태그/캐치프레이즈), SVD (협업 필터링) |
| **Search** | pg_trgm GIN 인덱스, NumPy 코사인 유사도 |
| **Infra** | Vercel, Railway, GitHub Actions, Sentry, Alembic |

---

## 시스템 아키텍처

```
┌─────────┐     ┌──────────────┐     ┌──────────────────┐
│  User   │────▶│  Vercel      │────▶│  Railway         │
│ Browser │◀────│  (Next.js)   │◀────│  (FastAPI)       │
└─────────┘     └──────────────┘     └────────┬─────────┘
                                              │
                          ┌───────────────────┼───────────────────┐
                          │                   │                   │
                    ┌─────▼─────┐     ┌───────▼──────┐   ┌───────▼──────┐
                    │ PostgreSQL│     │    Redis     │   │  External   │
                    │ (Railway) │     │  (Railway)   │   │  APIs       │
                    │ 42,917편  │     │  캐시/세션    │   │ Voyage AI   │
                    └───────────┘     └──────────────┘   │ Claude API  │
                                                         │ TMDB API    │
                                                         │ KMA 날씨    │
                                                         └─────────────┘
```

---

## 추천 알고리즘

### 하이브리드 스코어링 (v3)

**CF 활성화 + Mood 선택 시:**
```
Score = (0.20 x MBTI) + (0.15 x Weather) + (0.25 x Mood) + (0.15 x Personal) + (0.25 x CF)
```

**CF 비활성화 시 (fallback v2):**
```
Score = (0.25 x MBTI) + (0.20 x Weather) + (0.30 x Mood) + (0.25 x Personal)
```

| 신호 | 설명 |
|------|------|
| **MBTI** | 16유형별 장르 선호도 JSONB 매칭 |
| **Weather** | 실시간 날씨 조건별 영화 분위기 매칭 |
| **Mood** | 8가지 기분 → 7대 감성 클러스터 매핑 |
| **Personal** | 찜/고평점 영화 장르 기반 개인화 |
| **CF** | MovieLens SVD item_bias 품질 시그널 |

후처리: 품질 보정 (x0.85~1.0) → 장르 다양성 → 신선도 → 세렌디피티 → 중복 제거

상세 로직: [docs/RECOMMENDATION_LOGIC.md](docs/RECOMMENDATION_LOGIC.md) |
아키텍처: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 프로젝트 구조

```
recflix/
├── backend/
│   ├── app/
│   │   ├── api/v1/                # API 라우터 (15개 모듈)
│   │   │   ├── recommendations.py         # 홈 추천 API
│   │   │   ├── recommendation_engine.py   # Hybrid 스코어링 엔진
│   │   │   ├── recommendation_cf.py       # SVD 협업 필터링
│   │   │   ├── recommendation_reason.py   # 추천 이유 생성 (43개 템플릿)
│   │   │   ├── diversity.py               # 다양성 후처리
│   │   │   ├── semantic_search.py         # 시맨틱 검색 (인메모리 벡터)
│   │   │   ├── movies.py                  # 검색, 상세, 자동완성, 장르
│   │   │   ├── auth.py                    # JWT + Kakao/Google OAuth
│   │   │   ├── events.py                  # 사용자 행동 이벤트 (10종)
│   │   │   └── health.py                  # 헬스체크 (DB/Redis/SVD/임베딩)
│   │   ├── core/                  # 설정, 보안, DI, Rate Limiting, 로깅
│   │   ├── middleware/            # X-Request-ID 미들웨어
│   │   ├── models/                # SQLAlchemy 모델 (6개 테이블)
│   │   ├── schemas/               # Pydantic 스키마
│   │   └── services/              # 외부 서비스 (날씨, LLM)
│   ├── alembic/                   # DB 마이그레이션
│   ├── scripts/                   # 배치 스크립트 (16개)
│   ├── tests/                     # pytest (14건)
│   └── requirements.txt
├── frontend/
│   ├── app/                       # Next.js App Router (10개 페이지)
│   ├── components/                # React 컴포넌트
│   ├── hooks/                     # Custom Hooks (4개)
│   ├── stores/                    # Zustand 스토어 (2개)
│   ├── lib/                       # API 클라이언트, 이벤트 트래커, 유틸
│   └── types/                     # TypeScript 타입 정의
├── .github/workflows/ci.yml      # CI/CD (lint + test + build + Railway CD)
├── docs/                          # 프로젝트 문서
└── data/                          # DB 덤프 + 복원 가이드
```

---

## 로컬 개발 환경 설정

### 사전 요구사항

- PostgreSQL 16
- Redis (Windows: Memurai / macOS: `brew install redis`)
- Python 3.11+
- Node.js 20+

### 1. 저장소 클론

```bash
git clone https://github.com/sky1522/recflix.git
cd recflix
```

### 2. DB 생성 및 데이터 복원

```bash
psql -U postgres -c "CREATE USER recflix WITH PASSWORD 'recflix123';"
psql -U postgres -c "CREATE DATABASE recflix OWNER recflix;"

# 42,917편 영화 데이터 복원
PGPASSWORD=recflix123 pg_restore -h localhost -U recflix -d recflix \
  --clean --if-exists --no-owner --no-acl data/recflix_db.dump
```

### 3. Backend 실행

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 환경변수 설정
uvicorn app.main:app --reload --port 8000
```

**필수 환경변수** (`backend/.env`):
```env
DATABASE_URL=postgresql://recflix:recflix123@localhost:5432/recflix
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET_KEY=<openssl rand -hex 32>
WEATHER_API_KEY=<OpenWeatherMap API Key>
```

### 4. Frontend 실행

```bash
cd frontend
npm install
cp .env.example .env.local  # 기본값 사용 가능
npm run dev
```

### 5. 접속 확인

| 서비스 | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

## 배포

| 서비스 | 플랫폼 | 방식 |
|--------|--------|------|
| Frontend | Vercel | GitHub 연동 자동 배포 (push 시) |
| Backend | Railway | GitHub Actions CD (`railway up`) |
| Database | Railway | PostgreSQL 16 + Redis |

---

## API 문서

Swagger UI: https://backend-production-cff2.up.railway.app/docs

주요 엔드포인트:
- `GET /api/v1/recommendations` — 홈 추천 (MBTI + Weather + Mood)
- `GET /api/v1/movies` — 영화 검색 (필터, 정렬, 페이지네이션)
- `GET /api/v1/movies/search/semantic` — 시맨틱 검색
- `POST /api/v1/auth/signup` / `login` / `refresh` — 인증
- `GET /api/v1/health` — 헬스체크

---

## Phase 이력

| Phase | 날짜 | 내용 |
|-------|------|------|
| 1-8 | 02-02~03 | 기본 기능 구현 + 프로덕션 배포 (Vercel + Railway) |
| 9 | 02-03 | 프로덕션 배포 (GitHub + Vercel + Railway + PostgreSQL) |
| 10 | 02-04 | LLM 캐치프레이즈 (Claude API + Redis) + UX 개선 |
| 11 | 02-09 | emotion_tags 7대 클러스터 + 기분 추천 + LLM 2-Tier |
| 12 | 02-10 | 도메인 변경 + CORS 정리 |
| 13 | 02-10 | 신규 CSV 42,917편 마이그레이션 + 6컬럼 추가 |
| 14 | 02-10 | 알고리즘 v2 튜닝 + 연령등급 필터링 + 품질 보정 연속화 |
| 15 | 02-11 | 보안 대응 (DB 교체) + Vercel Image Optimization + 인기도 로그 스케일 |
| 16 | 02-11 | Favicon + 로고 + 날씨 한글 도시명 + 배너 개선 |
| 17 | 02-12 | DB 스키마 정리 (24→22컬럼) + overview 통합 |
| 18 | 02-12 | cast_ko 한글 음역 변환 (33,442개, Claude API $11.69) |
| 19 | 02-13 | cast_ko 100% 한글화 (외국어 4,253개 추가) |
| 20 | 02-13 | SEO 동적 OG 메타태그 (카카오톡 프리뷰) |
| 21 | 02-13 | 자체 유사 영화 계산 (429,170개 관계) + 에러 바운더리 |
| 22 | 02-13 | 검색 자동완성 강화 (키보드, Redis 캐싱, 하이라이팅) |
| 23 | 02-13 | 큐레이션 서브타이틀 시스템 (186개 문구) |
| 24 | 02-13 | 기분 8개 카테고리 확장 (울적한, 답답한 추가) |
| 25 | 02-13 | 서브타이틀 고도화 (3종 랜덤, 제목 우측 배치) |
| 26 | 02-13 | 컨텍스트 큐레이션 (시간대/계절/기온, 258개 문구) |
| 27 | 02-19 | CLAUDE.md + .claude/skills/ 8개 도메인 스킬 |
| 28 | 02-19 | 코드 리팩토링 (recommendations 770→347줄, movies/[id] 622→263줄) |
| 29 | 02-19 | Sentry + Rate Limiting + 에러 핸들링 표준화 |
| 30 | 02-19 | 사용자 행동 이벤트 (10종, eventTracker, Beacon API) |
| 31 | 02-19 | SVD 협업 필터링 (MovieLens 25M, CF 25% 통합) |
| 32 | 02-19 | A/B 테스트 + 소셜 로그인 (Kakao/Google) + 온보딩 |
| 33 | 02-20 | 시맨틱 검색 (Voyage AI 임베딩 42,917편) |
| 34 | 02-20 | 추천 다양성/신선도 정책 |
| 35 | 02-20 | SVD 모델 프로덕션 배포 (Dockerfile LFS + numpy 2.x) |
| 36 | 02-20 | 헬스체크 + CI/CD 파이프라인 (GitHub Actions) |
| 37 | 02-20 | 추천 이유 생성 (43개 템플릿, $0 비용) |
| 38 | 02-23 | 프로덕션 DB 마이그레이션 (user_events + users 7컬럼) |
| 39 | 02-23 | 문서 업데이트 (Phase 33~38 반영) |
| 40 | 02-23 | 설정 경량화 (skills/hooks/docs 고도화) |
| 41 | 02-23 | 안전/정확성 (distinct 쿼리, 토큰 회전, rate limit 강화) |
| 42 | 02-23 | DB 성능 (N+1 제거, 쿼리 통합, pg_trgm GIN) |
| 43 | 02-23 | API 내결함성 + 검색 병렬화 + 파일 분할 + 애니메이션 경량화 |
| 44 | 02-23 | SEO 메타데이터 + loading.tsx + 접근성 + 캐시 키 |
| 45 | 02-23 | 코드 품질 (ruff 143→0, any 8→0, except 구체화, focus trap) |
| 46 | 02-23 | 추천 콜드스타트 + 피드백 루프 + GDPR 계정 삭제 + 보안 강화 |
| 47 | 02-23 | TMDB 트레일러 수집 (28,486편) + YouTube 임베드 UI |
| 48 | 02-24 | async 블로킹 해소 (bcrypt to_thread) + Alembic + Dockerfile 체크섬 |
| 49 | 02-24 | 시맨틱 재랭킹 v2 + pytest (14건) + 구조화 로깅 (structlog) |
| **50** | **02-24** | **문서 최종화 + v1.0.0 릴리스** |

---

## 라이선스

MIT License
