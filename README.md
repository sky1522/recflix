# RecFlix

**실시간 컨텍스트(날씨/기분)와 성격 특성(MBTI)을 결합한 초개인화 영화 큐레이션 플랫폼**

## Features

- MBTI 기반 영화 추천 (16개 유형별)
- 실시간 날씨 연동 추천 (OpenWeatherMap)
- 감정 태그 기반 큐레이션 (힐링, 긴장감 등)
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

```
Score = (0.35 × MBTI) + (0.25 × Weather) + (0.40 × Personal)
```

- **MBTI**: 16개 유형별 장르 선호도 매칭
- **Weather**: 날씨 조건별 영화 분위기 매칭
- **Personal**: 찜한 영화 장르 기반 개인화

## Database

- **Movies**: 32,625편 (TMDB 기반)
- **Scores**: JSONB로 저장 (mbti_scores, weather_scores, emotion_tags)

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://recflix:recflix123@localhost:5432/recflix

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=recflix123

# JWT
JWT_SECRET_KEY=your-secret-key

# Weather API
WEATHER_API_KEY=your-openweathermap-key
```

## License

MIT License
