# 배포

## 핵심 파일
→ `DEPLOYMENT.md` (상세 배포 가이드)
→ `backend/railway.toml`
→ `frontend/vercel.json`

## 프로덕션 URL
| 서비스 | URL |
|--------|-----|
| Frontend | https://jnsquery-reflix.vercel.app |
| Backend API | https://backend-production-cff2.up.railway.app |
| API Docs | https://backend-production-cff2.up.railway.app/docs |
| GitHub | https://github.com/sky1522/recflix |

## 환경변수
→ `backend/.env.example`, `frontend/.env.example` 참조

### Backend 필수 환경변수
- `DATABASE_URL`: PostgreSQL 연결 URL
- `REDIS_URL` / `REDIS_PASSWORD`: Redis 연결
- `JWT_SECRET_KEY`: JWT 시크릿
- `OPENWEATHER_API_KEY`: OpenWeatherMap API
- `ANTHROPIC_API_KEY`: Claude API (캐치프레이즈)
- `CORS_ORIGINS`: 허용 도메인 (쉼표 구분)

### Frontend 필수 환경변수
- `NEXT_PUBLIC_API_URL`: Backend API URL

## 배포 프로세스
- main 브랜치 push → Railway/Vercel 자동 배포
- CORS: `backend/app/config.py`의 `CORS_ORIGINS`에 도메인 추가

## DB 마이그레이션
→ `DEPLOYMENT.md`의 마이그레이션 섹션 참조
```bash
# 로컬 → Railway
PGPASSWORD=recflix123 pg_dump -h localhost -U recflix -d recflix --no-owner --no-acl -Fc -f dump.dump
PGPASSWORD=<railway_pw> pg_restore -h shinkansen.proxy.rlwy.net -p 20053 -U postgres -d railway --clean --if-exists --no-owner --no-acl dump.dump
```

## 배포 시 체크리스트
1. 로컬 빌드 성공 확인
2. 환경변수 누락 확인
3. CORS_ORIGINS 확인
4. `git push origin HEAD:main` → 자동 배포
5. `/health` 엔드포인트 확인
6. 프론트엔드 주요 기능 수동 확인
