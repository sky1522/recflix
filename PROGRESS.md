# RecFlix 개발 진행 상황

**최종 업데이트**: 2026-02-03

---

## 완료된 작업

### Phase 1: 환경 설정 & 데이터

| 항목 | 상태 | 비고 |
|------|------|------|
| PostgreSQL 16 설치 | ✅ | Windows 로컬, 포트 5432 |
| Redis 설치 | ✅ | Memurai, 포트 6379, 암호: recflix123 |
| CSV → DB 마이그레이션 | ✅ | 32,625편 영화 |
| MBTI/날씨/감정 점수 생성 | ✅ | Rule-based, JSONB 저장 |

### Phase 2: Backend API (FastAPI)

| 항목 | 상태 | 엔드포인트 |
|------|------|-----------|
| 인증 (JWT) | ✅ | `/auth/signup`, `/auth/login`, `/auth/refresh` |
| 사용자 | ✅ | `/users/me`, `/users/me/mbti` |
| 영화 CRUD | ✅ | `/movies`, `/movies/{id}`, `/movies/genres` |
| 추천 | ✅ | `/recommendations`, `/recommendations/mbti`, `/recommendations/weather`, `/recommendations/for-you` |
| 평점 | ✅ | `/ratings`, `/ratings/me`, `/ratings/{movie_id}` |
| 컬렉션 | ✅ | `/collections`, `/collections/{id}/movies` |
| 날씨 | ✅ | `/weather` (OpenWeatherMap + Redis 캐싱) |
| 상호작용 | ✅ | `/interactions/movie/{id}`, `/interactions/favorite/{id}` |

### Phase 3: Frontend (Next.js 14)

| 항목 | 상태 | 경로/파일 |
|------|------|----------|
| 프로젝트 설정 | ✅ | TailwindCSS, Framer Motion, Zustand |
| 홈페이지 | ✅ | `/` - 추천 Row, 날씨 배너 |
| 영화 검색 | ✅ | `/movies` - 필터, 정렬, 페이지네이션 |
| 영화 상세 페이지 | ✅ | `/movies/[id]` - 히어로 배너, 평점, 출연진, 유사 영화 |
| 찜 목록 페이지 | ✅ | `/favorites` - 찜한 영화 그리드, 삭제, 더보기 |
| 내 평점 페이지 | ✅ | `/ratings` - 평점 목록, 통계, 삭제 |
| 로그인/회원가입 | ✅ | `/login`, `/signup` |
| 프로필 | ✅ | `/profile` - MBTI 설정 |
| 영화 상세 모달 | ✅ | `MovieModal.tsx` |
| Header | ✅ | 네비게이션, 날씨 인디케이터 |

### Phase 4: 날씨 연동 & 사용자 피드백

| 항목 | 상태 | 비고 |
|------|------|------|
| OpenWeatherMap 연동 | ✅ | 좌표/도시 기반 조회 |
| Redis 캐싱 | ✅ | TTL 30분 |
| 날씨별 테마 | ✅ | sunny/rainy/cloudy/snowy CSS |
| WeatherBanner | ✅ | 애니메이션 (비/눈/태양) |
| useWeather 훅 | ✅ | Geolocation + 캐싱 |
| 별점 UI | ✅ | 1~5점, 호버 효과 |
| 찜하기 버튼 | ✅ | Heart 토글 |
| interactionStore | ✅ | Optimistic UI |
| 개인화 추천 | ✅ | `/recommendations/for-you` |

### Phase 5: 검색 고도화 & UX 개선

| 항목 | 상태 | 비고 |
|------|------|------|
| 검색 자동완성 API | ✅ | `/movies/search/autocomplete` - 영화, 배우, 감독 |
| 배우/감독 검색 확장 | ✅ | 영화 검색 시 출연진/감독 포함 |
| useDebounce 훅 | ✅ | 300ms 디바운스 |
| SearchAutocomplete | ✅ | 실시간 드롭다운 UI |
| Skeleton 컴포넌트 | ✅ | Framer Motion 애니메이션 |
| 빈 결과 처리 | ✅ | 추천 영화 제안 |
| useInfiniteScroll 훅 | ✅ | Intersection Observer |
| 무한 스크롤 모드 | ✅ | 토글 버튼으로 전환 가능 |

### Phase 6: 하이브리드 추천 엔진

| 항목 | 상태 | 비고 |
|------|------|------|
| 하이브리드 스코어링 | ✅ | MBTI(35%) + 날씨(25%) + 개인취향(40%) |
| 개인취향 분석 | ✅ | 찜 + 평점(4.0↑) 기반 장르 집계 |
| 유사 영화 보너스 | ✅ | similar_movies 테이블 활용 |
| 추천 태그 시스템 | ✅ | #MBTI추천, #비오는날, #취향저격 등 |
| HybridMovieItem 스키마 | ✅ | recommendation_tags, hybrid_score |
| HybridMovieRow | ✅ | 맞춤 추천 섹션 컴포넌트 |
| HybridMovieCard | ✅ | 추천 태그 배지 표시 |
| 홈 UI 개선 | ✅ | 로그인/MBTI 설정 유도 배너 |

### Phase 7: 반응형 모바일 최적화

| 항목 | 상태 | 비고 |
|------|------|------|
| Header 모바일 메뉴 | ✅ | 햄버거 메뉴, 슬라이드 패널 |
| MobileNav | ✅ | 하단 네비게이션 바 |
| WeatherBanner 반응형 | ✅ | 모바일 레이아웃 최적화 |
| 영화 상세 페이지 반응형 | ✅ | 모바일 포스터, 버튼 크기 조정 |
| 로그인 페이지 개선 | ✅ | 아이콘, 비밀번호 토글 |
| Safe Area 지원 | ✅ | 노치 디바이스 대응 |
| 터치 친화적 UI | ✅ | 최소 탭 영역 44px |

### Phase 8: 배포 설정

| 항목 | 상태 | 비고 |
|------|------|------|
| Backend Dockerfile | ✅ | Python 3.11, uvicorn |
| Frontend Dockerfile | ✅ | Node 20, standalone 빌드 |
| docker-compose.yml | ✅ | 로컬 개발/테스트용 |
| Railway 설정 | ✅ | railway.toml, 환경변수 |
| Vercel 설정 | ✅ | vercel.json, 보안 헤더 |
| 환경변수 관리 | ✅ | .env.example 파일 |
| CORS 프로덕션 설정 | ✅ | 동적 CORS 지원 |
| 배포 가이드 | ✅ | DEPLOYMENT.md |

---

## 프로젝트 구조

```
C:\dev\recflix\
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── movies.py
│   │   │   ├── recommendations.py
│   │   │   ├── ratings.py
│   │   │   ├── collections.py
│   │   │   ├── weather.py
│   │   │   ├── interactions.py
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── weather.py
│   │   ├── database.py
│   │   └── main.py
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── login/page.tsx
│   │   ├── signup/page.tsx
│   │   ├── profile/page.tsx
│   │   ├── movies/page.tsx
│   │   ├── movies/[id]/page.tsx
│   │   ├── favorites/page.tsx
│   │   └── ratings/page.tsx
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   └── MobileNav.tsx
│   │   ├── movie/
│   │   │   ├── MovieCard.tsx
│   │   │   ├── MovieRow.tsx
│   │   │   ├── MovieModal.tsx
│   │   │   └── FeaturedBanner.tsx
│   │   ├── weather/WeatherBanner.tsx
│   │   ├── search/SearchAutocomplete.tsx
│   │   ├── ui/Skeleton.tsx
│   │   └── movie/
│   │       ├── HybridMovieRow.tsx
│   │       └── HybridMovieCard.tsx
│   ├── hooks/
│   │   ├── useWeather.ts
│   │   ├── useDebounce.ts
│   │   └── useInfiniteScroll.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   └── interactionStore.ts
│   ├── lib/
│   │   ├── api.ts
│   │   └── utils.ts
│   └── types/index.ts
├── scripts/
├── data/
└── docs/
```

---

## 실행 방법

```bash
# 1. PostgreSQL 실행 확인 (Windows 서비스)

# 2. Redis(Memurai) 실행 확인

# 3. Backend
cd backend
uvicorn app.main:app --reload --port 8000

# 4. Frontend
cd frontend
npm run dev
```

| 서비스 | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

## 환경 설정

**backend/.env**
```env
DATABASE_URL=postgresql://recflix:recflix123@localhost:5432/recflix
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=recflix123
JWT_SECRET_KEY=your-secret-key
WEATHER_API_KEY=e9fcc611acf478ac0ac1e7bddeaea70e
```

---

## 미구현 / TODO

### 우선순위 높음
- [x] 영화 상세 페이지 (`/movies/[id]`) - 완료
- [x] 내 찜 목록 페이지 (`/favorites`) - 완료
- [x] 내 평점 목록 페이지 (`/ratings`) - 완료

### 우선순위 중간
- [x] 검색 자동완성
- [x] 무한 스크롤 (영화 목록)
- [x] 반응형 모바일 최적화 - 완료

### 우선순위 낮음
- [ ] LLM 캐치프레이즈 (GPT 연동)
- [ ] 소셜 로그인 (Google, Kakao)
- [ ] PWA 지원
- [x] 배포 설정 (Vercel + Railway) - 완료

---

## 해결한 주요 이슈

1. **Pydantic extra fields**: `extra = "ignore"` 설정
2. **JSONB 업데이트**: Raw SQL + `CAST(:param AS jsonb)`
3. **bcrypt/passlib 호환성**: bcrypt 직접 사용
4. **JWT sub claim 타입**: str 변환/int 변환
5. **pydantic-settings env_file**: 상대경로 이슈 → backend/.env 직접 복사
