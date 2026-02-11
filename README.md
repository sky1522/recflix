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
- **기분(Mood) 기반 추천** (6가지: 편안한, 긴장감, 신나는, 감성적인, 상상력, 가벼운)
- **감정 태그 기반 큐레이션** (7대 클러스터: healing, tension, energy, romance, deep, fantasy, light)
- **🔄 새로고침 버튼** - 섹션별 영화 재셔플 (API 호출 없음)
- **LLM 캐치프레이즈** - Claude API로 영화별 맞춤 문구 생성
- 별점 평가 & 찜하기 기능
- Netflix/Watcha 스타일 UI

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Next.js 14, TailwindCSS, Framer Motion, Zustand, lucide-react |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Redis |
| **Database** | PostgreSQL 16, Redis (Memurai) |
| **External API** | OpenWeatherMap |

## Quick Start

### Prerequisites

- PostgreSQL 16
- Redis (Windows: Memurai)
- Python 3.11+
- Node.js 20+

### 1. Environment Setup

```bash
cd recflix

# Backend 환경변수 복사 및 수정
cp .env.example backend/.env
# WEATHER_API_KEY 등 설정
```

### 2. Backend

```bash
cd backend

# 의존성 설치
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

### 4. Access

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

## Project Structure

```
recflix/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API 라우터
│   │   ├── core/            # 설정, 보안, 의존성
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── schemas/         # Pydantic 스키마
│   │   └── services/        # 비즈니스 로직 (날씨 등)
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js App Router
│   ├── components/          # React 컴포넌트
│   ├── hooks/               # Custom Hooks
│   ├── stores/              # Zustand 스토어
│   └── lib/                 # API 클라이언트, 유틸
├── scripts/                 # 데이터 마이그레이션
├── data/                    # 영화 데이터 CSV
└── docs/                    # EDA 문서
```

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
- **Mood**: 6가지 기분 → 7대 감성 클러스터 매핑 (v2: 가중치 강화)
- **Personal**: 찜한 영화 장르 기반 개인화
- **Quality**: weighted_score 기반 연속 품질 보정 (×0.85~1.0)
- **Age Rating**: 연령등급 필터링 지원 (all/family/teen/adult)

자세한 추천 로직은 [docs/RECOMMENDATION_LOGIC.md](docs/RECOMMENDATION_LOGIC.md) 참조

## Database

- **Movies**: 42,917편 (TMDB 기반)
- **Scores**: JSONB로 저장 (mbti_scores, weather_scores, emotion_tags)

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://recflix:your-db-password-here@localhost:5432/recflix

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password-here

# JWT (Generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-jwt-secret-key-here

# Weather API (https://openweathermap.org/api)
WEATHER_API_KEY=your-openweathermap-api-key-here

# Anthropic API (for LLM features)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

See `.env.example` for full configuration template.

## License

MIT License
