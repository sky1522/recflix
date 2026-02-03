# RecFlix 배포 가이드

## 현재 배포 상태 (2026-02-03)

| 서비스 | 플랫폼 | URL |
|--------|--------|-----|
| Frontend | Vercel | https://frontend-eight-gules-78.vercel.app |
| Backend API | Railway | https://backend-production-cff2.up.railway.app |
| API Docs | Railway | https://backend-production-cff2.up.railway.app/docs |
| PostgreSQL | Railway | 내부 연결 (32,625편 영화) |
| Redis | Railway | 내부 연결 |

### 설정된 환경변수

**Backend (Railway):**
- `DATABASE_URL` - PostgreSQL 연결 (자동)
- `REDIS_URL` - Redis 연결 (자동)
- `JWT_SECRET_KEY` - JWT 서명 키
- `WEATHER_API_KEY` - OpenWeatherMap API
- `CORS_ORIGINS` - Vercel 프론트엔드 URL
- `APP_ENV` - production

**Frontend (Vercel):**
- `NEXT_PUBLIC_API_URL` - https://backend-production-cff2.up.railway.app/api/v1

---

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐
│  Vercel         │     │  Railway        │
│  (Frontend)     │────▶│  (Backend)      │
│  Next.js 14     │     │  FastAPI        │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │PostgreSQL│ │  Redis   │ │OpenWeather│
              │ (Railway)│ │(Railway) │ │   API    │
              └──────────┘ └──────────┘ └──────────┘
```

---

## 1. Backend 배포 (Railway)

### 1.1 Railway 프로젝트 생성

1. [Railway](https://railway.app) 로그인
2. "New Project" → "Deploy from GitHub Repo"
3. RecFlix 저장소 연결
4. "Add Service" → "Database" → "PostgreSQL" 추가
5. "Add Service" → "Database" → "Redis" 추가

### 1.2 Backend 서비스 설정

1. "Add Service" → "GitHub Repo" → `backend` 폴더 선택
2. Settings에서 Root Directory를 `backend`로 설정
3. Environment Variables 설정:

```env
# 자동 연결됨 (PostgreSQL, Redis 서비스 연결 시)
DATABASE_URL=<자동 설정됨>
REDIS_URL=<자동 설정됨>

# 수동 설정 필요
APP_ENV=production
JWT_SECRET_KEY=<안전한-시크릿-키-생성>
WEATHER_API_KEY=<OpenWeatherMap-API-키>
CORS_ORIGINS=https://your-app.vercel.app
```

### 1.3 JWT Secret Key 생성

```bash
# Python으로 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 또는 OpenSSL
openssl rand -base64 32
```

### 1.4 데이터베이스 마이그레이션

Railway PostgreSQL 연결 후:

```bash
# Railway CLI 설치
npm install -g @railway/cli

# 로그인
railway login

# 프로젝트 연결
railway link

# 마이그레이션 실행
railway run python -m scripts.migrate_data
```

---

## 2. Frontend 배포 (Vercel)

### 2.1 Vercel 프로젝트 생성

1. [Vercel](https://vercel.com) 로그인
2. "Add New" → "Project"
3. GitHub 저장소 Import
4. Framework Preset: **Next.js**
5. Root Directory: `frontend`

### 2.2 Environment Variables 설정

Vercel Dashboard → Project Settings → Environment Variables:

```env
NEXT_PUBLIC_API_URL=https://your-railway-backend.railway.app/api/v1
```

### 2.3 배포 설정

- Build Command: `npm run build`
- Output Directory: `.next`
- Install Command: `npm ci`

### 2.4 도메인 설정 (선택)

1. Vercel Dashboard → Domains
2. 커스텀 도메인 추가
3. DNS 설정

---

## 3. 로컬 Docker 테스트

### 3.1 전체 스택 실행

```bash
# 환경 변수 설정
cp backend/.env.example backend/.env
# .env 파일 수정

# Docker Compose 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3.2 개별 서비스 실행

```bash
# 데이터베이스만 실행
docker-compose up -d db redis

# Backend 로컬 실행
cd backend
uvicorn app.main:app --reload

# Frontend 로컬 실행
cd frontend
npm run dev
```

---

## 4. 환경 변수 체크리스트

### Backend (Railway)

| 변수 | 필수 | 설명 |
|------|------|------|
| DATABASE_URL | ✅ | PostgreSQL 연결 (자동) |
| REDIS_URL | ✅ | Redis 연결 (자동) |
| JWT_SECRET_KEY | ✅ | JWT 서명 키 |
| WEATHER_API_KEY | ✅ | OpenWeatherMap API 키 |
| CORS_ORIGINS | ✅ | 허용 도메인 (Vercel URL) |
| APP_ENV | ⚪ | production 설정 |

### Frontend (Vercel)

| 변수 | 필수 | 설명 |
|------|------|------|
| NEXT_PUBLIC_API_URL | ✅ | Backend API URL |

---

## 5. 배포 후 확인 사항

### Health Check

```bash
# Backend
curl https://your-backend.railway.app/health

# API 테스트
curl https://your-backend.railway.app/api/v1/movies?page_size=1
```

### 로그 모니터링

```bash
# Railway 로그
railway logs

# Vercel 로그
vercel logs
```

---

## 6. 트러블슈팅

### CORS 에러

```
Access to fetch at 'https://api...' has been blocked by CORS policy
```

**해결**: Backend의 `CORS_ORIGINS`에 Frontend URL 추가

### Database Connection 에러

```
connection refused / timeout
```

**해결**:
1. Railway에서 PostgreSQL 서비스 상태 확인
2. DATABASE_URL 환경 변수 확인
3. 서비스 간 연결(Link) 확인

### Build 실패

```
Build failed
```

**해결**:
1. 로컬에서 빌드 테스트: `npm run build` / `docker build`
2. 로그에서 에러 메시지 확인
3. 환경 변수 누락 확인

---

## 7. CI/CD 자동화 (선택)

### GitHub Actions 예시

`.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
```

---

## 8. 비용 예상

### Railway (Backend + DB + Redis)

- Hobby Plan: $5/월 기본
- 사용량 기반 과금
- PostgreSQL: ~$5/월
- Redis: ~$5/월
- **예상 총액**: $10-20/월

### Vercel (Frontend)

- Hobby Plan: 무료
- Pro Plan: $20/월 (팀 기능 필요 시)
- **예상 총액**: $0-20/월

---

## 관련 링크

- [Railway 문서](https://docs.railway.app/)
- [Vercel 문서](https://vercel.com/docs)
- [Next.js 배포 가이드](https://nextjs.org/docs/deployment)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
