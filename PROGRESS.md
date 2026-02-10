# RecFlix 개발 진행 상황

**최종 업데이트**: 2026-02-10

---

## 완료된 작업

### Phase 1: 환경 설정 & 데이터

| 항목 | 상태 | 비고 |
|------|------|------|
| PostgreSQL 16 설치 | ✅ | Windows 로컬, 포트 5432 |
| Redis 설치 | ✅ | Memurai, 포트 6379, 암호: recflix123 |
| CSV → DB 마이그레이션 | ✅ | 42,917편 영화 (신규 CSV 적용) |
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
| LLM 캐치프레이즈 | ✅ | `/llm/catchphrase/{movie_id}` (Claude API + Redis 캐싱) |

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

### Phase 9: 프로덕션 배포 (2026-02-03)

| 항목 | 상태 | 비고 |
|------|------|------|
| GitHub 저장소 생성 | ✅ | https://github.com/sky1522/recflix |
| Vercel 프론트엔드 배포 | ✅ | https://jnsquery-reflix.vercel.app |
| Railway 프로젝트 생성 | ✅ | recflix 프로젝트 |
| Railway PostgreSQL | ✅ | 자동 프로비저닝 |
| Railway Redis | ✅ | 캐싱용 |
| Railway Backend 배포 | ✅ | https://backend-production-cff2.up.railway.app |
| 데이터베이스 마이그레이션 | ✅ | pg_dump → Railway (42,917편 영화) |
| 환경변수 설정 | ✅ | DATABASE_URL, REDIS_URL, JWT, CORS 등 |
| CORS 설정 수정 | ✅ | pydantic field_validator로 파싱 |
| 테이블 자동 생성 | ✅ | FastAPI lifespan 이벤트 |

### Phase 10: LLM 캐치프레이즈 & UX 개선 (2026-02-04)

| 항목 | 상태 | 비고 |
|------|------|------|
| LLM 캐치프레이즈 API | ✅ | Claude API 연동, `/api/v1/llm/catchphrase/{id}` |
| Redis 캐싱 (LLM) | ✅ | TTL 24시간, 프로덕션 REDIS_URL 지원 |
| 영화 상세 캐치프레이즈 표시 | ✅ | DB tagline 대신 LLM 생성 캐치프레이즈 |
| 모바일 캐치프레이즈 표시 | ✅ | `hidden sm:block` 제거 |
| 메인 배너 레이아웃 개선 | ✅ | 영화정보 좌하단, MBTI유도 우상단 |
| MBTI 유도 메시지 | ✅ | 랜덤 메시지, 로그인/MBTI 설정 유도 |
| 내 리스트 버튼 기능 | ✅ | 로그인 체크, toggleFavorite 연동 |
| 영화 목록 다양성 | ✅ | 50개로 증가, 랜덤 셔플 |
| 텍스트 정렬 개선 | ✅ | 섹션 타이틀 한줄, 카드 중앙정렬 |
| 무한스크롤 버그 수정 | ✅ | callback ref 패턴, enabled 옵션 |
| 헤더 메뉴명 변경 | ✅ | "영화" → "영화 검색" |
| 콘솔 에러 수정 | ✅ | manifest.json, meta tag, icons |

### Phase 11: emotion_tags 고도화 & 기분 추천 (2026-02-09)

| 항목 | 상태 | 비고 |
|------|------|------|
| LLM emotion_tags 분석 | ✅ | Claude API, 상위 1,000편 |
| 7대 감성 클러스터 정의 | ✅ | healing, tension, energy, romance, deep, fantasy, light |
| 키워드 기반 점수 생성 | ✅ | 31,625편, 0.7 상한 |
| 네거티브 키워드 로직 | ✅ | -0.1/개 감점 |
| 장르 페널티 로직 | ✅ | -0.15/개 감점 |
| 30% LLM 보장 혼합 정렬 | ✅ | 추천 풀에서 LLM 영화 최소 30% |
| 기분 선택 UI | ✅ | 6가지 기분, 2x3 그리드 |
| 품질 필터 적용 | ✅ | vote_count >= 30, vote_average >= 5.0 |
| 섹션 순서 조건부 배치 | ✅ | 로그인: 개인화→범용, 비로그인: 범용→개인화 |
| 로그아웃 즉시 갱신 | ✅ | Zustand 스토어 초기화 + 추천 재요청 |
| 유도 섹션 UI 통일 | ✅ | w-80 너비, 동일 스타일 |
| 추천 로직 문서화 | ✅ | docs/RECOMMENDATION_LOGIC.md |
| 맞춤 추천 영화 수 증가 | ✅ | 10개 → 20개 (풀 40개에서 셔플) |
| 🔄 새로고침 버튼 | ✅ | 모든 섹션 제목 우측, 풀 내 재셔플 |
| .env.example 보안 | ✅ | 민감값 → your-xxx-here 플레이스홀더 |

### Phase 12: 도메인 변경 & CORS 정리 (2026-02-10)

| 항목 | 상태 | 비고 |
|------|------|------|
| Vercel 프로젝트 이름 변경 | ✅ | frontend → jnsquery-reflix |
| 프로덕션 도메인 변경 | ✅ | https://jnsquery-reflix.vercel.app |
| CORS_ORIGINS 업데이트 | ✅ | Railway 환경변수 + 로컬 .env 동기화 |
| Railway 백엔드 재배포 | ✅ | CORS 설정 반영 |
| README 도메인 업데이트 | ✅ | 새 프론트엔드 URL 반영 |

### Phase 13: 신규 데이터 마이그레이션 (2026-02-10)

| 항목 | 상태 | 비고 |
|------|------|------|
| DB 스키마 비교 분석 | ✅ | CSV 43컬럼 vs DB 18컬럼 매핑 |
| Movie 모델 6컬럼 추가 | ✅ | director, director_ko, cast_ko, production_countries_ko, release_season, weighted_score |
| Pydantic 스키마 업데이트 | ✅ | MovieDetail에 신규 필드 반영 |
| 마이그레이션 스크립트 | ✅ | `migrate_add_columns.py` (ALTER TABLE) |
| CSV 임포트 (42,917편) | ✅ | `import_csv_data.py`, `import_relationships.py` |
| LLM emotion_tags 복원 | ✅ | 996/1,000편 복원 (4편은 신규 CSV에 없음) |
| 키워드 기반 emotion_tags 생성 | ✅ | 18,587편 신규 생성 → 전체 100% |
| mbti_scores 생성 | ✅ | 21,180편 신규 생성 → 전체 100% |
| weather_scores 생성 | ✅ | 21,180편 신규 생성 → 전체 100% |
| 프로덕션 DB 적용 | ✅ | pg_dump → pg_restore로 Railway DB 복원 |
| 프로덕션 검증 | ✅ | 42,917편, 점수 100%, API 정상 |
| .gitignore CSV 제외 | ✅ | `*.csv` 패턴 추가 |

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
│   │   │   ├── weather.py
│   │   │   └── llm.py
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

## 프로덕션 URL

| 서비스 | URL |
|--------|-----|
| Frontend (Vercel) | https://jnsquery-reflix.vercel.app |
| Backend API (Railway) | https://backend-production-cff2.up.railway.app |
| API Docs | https://backend-production-cff2.up.railway.app/docs |
| GitHub | https://github.com/sky1522/recflix |

---

## 로컬 실행 방법

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

### 완료됨
- [x] 영화 상세 페이지 (`/movies/[id]`)
- [x] 내 찜 목록 페이지 (`/favorites`)
- [x] 내 평점 목록 페이지 (`/ratings`)
- [x] 검색 자동완성
- [x] 무한 스크롤 (영화 목록)
- [x] 반응형 모바일 최적화
- [x] 배포 설정 (Vercel + Railway)
- [x] **프로덕션 배포 완료** (2026-02-03)
- [x] **LLM 캐치프레이즈** (Claude API 연동) (2026-02-04)
- [x] **메인 배너 UX 개선** (2026-02-04)
- [x] **무한스크롤 버그 수정** (2026-02-04)
- [x] **LLM emotion_tags 분석** (상위 1,000편) (2026-02-09)
- [x] **기분(Mood) 추천 기능** (2026-02-09)
- [x] **emotion_tags 2-Tier 시스템** (LLM + 키워드) (2026-02-09)
- [x] **추천 품질 필터** (2026-02-09)
- [x] **🔄 새로고침 버튼** (풀 내 재셔플) (2026-02-09)
- [x] **맞춤 추천 20개로 증가** (2026-02-09)
- [x] **Vercel 도메인 변경** (jnsquery-reflix.vercel.app) (2026-02-10)
- [x] **CORS 설정 정리** (Railway + 로컬 동기화) (2026-02-10)
- [x] **신규 CSV 42,917편 마이그레이션** (32,625 → 42,917) (2026-02-10)
- [x] **Movie 모델 6컬럼 추가** (director, cast_ko, release_season 등) (2026-02-10)
- [x] **점수 데이터 100% 재생성** (emotion/mbti/weather) (2026-02-10)
- [x] **프로덕션 DB 복원** (pg_dump → pg_restore) (2026-02-10)

### 향후 개선사항
- [ ] 소셜 로그인 (Google, Kakao)
- [ ] PWA 지원
- [ ] CI/CD 파이프라인 (GitHub Actions)
- [ ] 모니터링/로깅 설정 (Sentry 등)

---

## 해결한 주요 이슈

1. **Pydantic extra fields**: `extra = "ignore"` 설정
2. **JSONB 업데이트**: Raw SQL + `CAST(:param AS jsonb)`
3. **bcrypt/passlib 호환성**: bcrypt 직접 사용
4. **JWT sub claim 타입**: str 변환/int 변환
5. **pydantic-settings env_file**: 상대경로 이슈 → backend/.env 직접 복사
6. **Next.js Suspense boundary**: `useSearchParams` 훅을 Suspense로 감싸야 함 (movies/page.tsx)
7. **Railway PORT 변수**: `sh -c` 래퍼로 환경변수 확장 (railway.toml)
8. **CORS_ORIGINS 파싱**: `List[str]`을 `field_validator`로 comma-separated 문자열 파싱
9. **DB 테이블 자동 생성**: FastAPI `lifespan` 이벤트에서 `Base.metadata.create_all()` 호출
10. **Windows nul 파일 충돌**: 예약된 파일명 삭제 후 Railway 배포 진행
11. **Redis 프로덕션 연결**: `REDIS_URL` 환경변수 사용 → `aioredis.from_url()` (2026-02-04)
12. **무한스크롤 중단**: callback ref 패턴 + refs로 stale closure 방지 (2026-02-04)
