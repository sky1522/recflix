# RecFlix

**실시간 컨텍스트(날씨/기분)와 성격 특성(MBTI)을 결합한 초개인화 영화 큐레이션 플랫폼**

## Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | https://jnsquery-reflix.vercel.app |
| **Backend API** | https://backend-production-cff2.up.railway.app |
| **API Docs** | https://backend-production-cff2.up.railway.app/docs |

## Features

- **MBTI 기반 영화 추천** (16개 유형별)
- **실시간 날씨 연동 추천** (OpenWeatherMap)
- **기분(Mood) 기반 추천** (8가지: 평온한, 긴장된, 활기찬, 몽글몽글한, 상상에빠진, 유쾌한, 울적한, 답답한)
- **감정 태그 기반 큐레이션** (7대 클러스터: healing, tension, energy, romance, deep, fantasy, light)
- **새로고침 버튼** - 섹션별 영화 재셔플 (API 호출 없음)
- **LLM 캐치프레이즈** - Claude API로 영화별 맞춤 문구 생성
- **컨텍스트 큐레이션** - 시간대/계절/기온 기반 동적 서브타이틀 (258개 문구)
- **검색 자동완성** - 키보드 네비게이션, Redis 캐싱, 키워드 하이라이팅
- **SEO 동적 OG 태그** - SNS 공유 시 포스터/제목/줄거리 프리뷰
- 별점 평가 & 찜하기 기능
- Netflix/Watcha 스타일 UI

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, TailwindCSS, Framer Motion, Zustand, lucide-react |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Redis |
| **Database** | PostgreSQL 16, Redis (Memurai) |
| **External API** | OpenWeatherMap, Claude API (Anthropic) |
| **Deployment** | Vercel (Frontend), Railway (Backend + PostgreSQL + Redis) |

---

## Quick Start (팀원용 로컬 환경 세팅)

### Prerequisites

- **PostgreSQL 16** ([다운로드](https://www.postgresql.org/download/))
- **Redis** (Windows: [Memurai](https://www.memurai.com/get-memurai) / macOS: `brew install redis`)
- **Python 3.11+**
- **Node.js 20+**

### Step 1. 저장소 클론

```bash
git clone https://github.com/sky1522/recflix.git
cd recflix
```

### Step 2. DB 생성 및 데이터 복원

프로젝트에 42,917편의 영화 데이터가 포함된 DB dump 파일이 있습니다.

```bash
# PostgreSQL 접속 후 DB/유저 생성
psql -U postgres
```

```sql
CREATE USER recflix WITH PASSWORD 'recflix123';
CREATE DATABASE recflix OWNER recflix;
\q
```

```bash
# DB 복원 (42,917편 영화 + 추천 점수 + 감성 태그)
# macOS / Linux
PGPASSWORD=recflix123 pg_restore -h localhost -U recflix -d recflix \
  --clean --if-exists --no-owner --no-acl data/recflix_db.dump

# Windows (Git Bash 또는 PowerShell)
$env:PGPASSWORD="recflix123"; & "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" `
  -h localhost -U recflix -d recflix `
  --clean --if-exists --no-owner --no-acl data/recflix_db.dump
```

복원 확인:
```bash
PGPASSWORD=recflix123 psql -h localhost -U recflix -d recflix -c "SELECT COUNT(*) FROM movies;"
# 결과: 42917
```

> DB 스키마 및 컬럼 상세 설명은 [data/DB_RESTORE_GUIDE.md](data/DB_RESTORE_GUIDE.md) 참조

### Step 3. Backend 환경 설정 및 실행

```bash
cd backend

# 환경변수 설정
cp .env.example .env
```

`.env` 파일을 열어 아래 값을 설정:

```env
DATABASE_URL=postgresql://recflix:recflix123@localhost:5432/recflix
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=recflix123
JWT_SECRET_KEY=your-secret-key-here        # openssl rand -hex 32 로 생성
WEATHER_API_KEY=your-openweathermap-key     # https://openweathermap.org/api 에서 발급
ANTHROPIC_API_KEY=your-anthropic-key        # (선택) LLM 캐치프레이즈 기능용
```

```bash
# Python 가상환경 생성 및 의존성 설치
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Step 4. Frontend 환경 설정 및 실행

```bash
cd frontend

# 환경변수 설정
cp .env.example .env.local
```

`.env.local` 내용 확인 (기본값 그대로 사용 가능):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

```bash
# 의존성 설치 및 실행
npm install
npm run dev
```

### Step 5. 접속 확인

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 기존 팀원: 최신 코드 & DB 업데이트

이미 로컬 환경이 있는 팀원은 아래 명령어로 최신화:

```bash
# 1. 최신 코드 받기
git pull origin main

# 2. DB 최신화 (cast_ko 100% 한글화 등 데이터 변경 반영)
# macOS / Linux
PGPASSWORD=recflix123 pg_restore -h localhost -U recflix -d recflix \
  --clean --if-exists --no-owner --no-acl data/recflix_db.dump

# Windows
$env:PGPASSWORD="recflix123"; & "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe" `
  -h localhost -U recflix -d recflix `
  --clean --if-exists --no-owner --no-acl data/recflix_db.dump

# 3. Backend 의존성 업데이트 (새 패키지 추가 시)
cd backend && pip install -r requirements.txt

# 4. Frontend 의존성 업데이트 (새 패키지 추가 시)
cd frontend && npm install
```

> **주의**: `pg_restore --clean`은 기존 테이블을 삭제 후 재생성합니다.
> 로컬에서 테스트한 평점/찜 데이터 등이 초기화됩니다.

---

## Project Structure

```
recflix/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 라우터 (auth, movies, recommendations 등)
│   │   ├── core/            # 설정, 보안, 의존성
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── schemas/         # Pydantic 스키마
│   │   └── services/        # 비즈니스 로직 (날씨, LLM 등)
│   ├── scripts/             # DB 마이그레이션, 음역 변환 스크립트
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js App Router (페이지)
│   ├── components/          # React 컴포넌트
│   ├── hooks/               # Custom Hooks (useWeather, useDebounce 등)
│   ├── stores/              # Zustand 스토어
│   ├── lib/                 # API 클라이언트, 유틸
│   └── types/               # TypeScript 타입 정의
├── data/
│   ├── recflix_db.dump      # DB 덤프 (42,917편, 22MB)
│   └── DB_RESTORE_GUIDE.md  # DB 복원 상세 가이드
└── docs/
    ├── RECOMMENDATION_LOGIC.md  # 추천 알고리즘 상세
    └── PROJECT_REVIEW.md        # 프로젝트 리뷰 & 로드맵
```

## Database

- **영화**: 42,917편 (TMDB 기반, 22컬럼)
- **출연진**: cast_ko 100% 한글화 (42,759편)
- **추천 점수**: JSONB (mbti_scores, weather_scores, emotion_tags)
- **감성 분석**: LLM 1,711편 + 키워드 기반 41,206편

상세 스키마: [data/DB_RESTORE_GUIDE.md](data/DB_RESTORE_GUIDE.md)

## Recommendation Algorithm

**Mood 선택 시:**
```
Score = (0.25 × MBTI) + (0.20 × Weather) + (0.30 × Mood) + (0.25 × Personal)
```

**Mood 미선택 시:**
```
Score = (0.35 × MBTI) + (0.25 × Weather) + (0.40 × Personal)
```

- **MBTI**: 16개 유형별 장르 선호도 매칭
- **Weather**: 날씨 조건별 영화 분위기 매칭
- **Mood**: 8가지 기분 → 7대 감성 클러스터 매핑
- **Personal**: 찜한 영화 장르 기반 개인화
- **Quality**: weighted_score 기반 연속 품질 보정 (×0.85~1.0)
- **Age Rating**: 연령등급 필터링 지원 (all/family/teen/adult)

자세한 추천 로직은 [docs/RECOMMENDATION_LOGIC.md](docs/RECOMMENDATION_LOGIC.md) 참조

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://recflix:recflix123@localhost:5432/recflix

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=recflix123

# JWT (Generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-jwt-secret-key-here

# Weather API (https://openweathermap.org/api)
WEATHER_API_KEY=your-openweathermap-api-key-here

# Anthropic API (for LLM features, optional)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

See `backend/.env.example` and `frontend/.env.example` for full templates.

## License

MIT License
