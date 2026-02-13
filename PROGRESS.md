# RecFlix 개발 진행 상황

**최종 업데이트**: 2026-02-13

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

### Phase 14: 알고리즘 튜닝 & 연령등급 필터링 (2026-02-10)

| 항목 | 상태 | 비고 |
|------|------|------|
| LLM emotion_tags 재분석 | ✅ | 1,711편, 새 프롬프트 (세밀 점수 분포) |
| 품질 필터 통합 | ✅ | vote_count+vote_average → weighted_score >= 6.0 |
| 연령등급 필터링 | ✅ | age_rating 파라미터 (all/family/teen/adult) |
| AGE_RATING_MAP | ✅ | family: ALL/G/PG/12, teen: +PG-13/15 |
| 등급 배지 UI | ✅ | MovieCard 등급별 색상 배지 |
| 검색 등급 필터 | ✅ | 영화 검색 페이지 드롭다운 |
| Hybrid 가중치 v2 | ✅ | Mood 0.30, MBTI 0.25, Weather 0.20, Personal 0.25 |
| 품질 보정 연속화 | ✅ | binary bonus → ×0.85~1.0 연속 보정 |
| #명작 태그 개선 | ✅ | ws >= 7.5 (태그만, 점수 가산 없음) |
| 분석 스크립트 | ✅ | analyze_hybrid_scores.py |
| DB 덤프 공유 | ✅ | data/recflix_db.dump + 복원 가이드 |

### Phase 15: 보안 대응 & UI/UX 개선 (2026-02-11)

| 항목 | 상태 | 비고 |
|------|------|------|
| DB 비밀번호 노출 대응 | ✅ | Railway DB 교체 (shinkansen), .gitignore 보호 |
| Vercel 포스터 미표시 수정 | ✅ | Image Optimization 비활성화 (unoptimized: true) |
| 제작 국가 한국어 표시 | ✅ | production_countries_ko 우선 사용 |
| 높은 평점 정렬 개선 | ✅ | vote_average → weighted_score 전체 통일 |
| 검색 평점순 정렬 개선 | ✅ | sort_by=weighted_score로 변경 |
| 인기도 로그 스케일 표시 | ✅ | 10점 만점 변환 + 라벨 (초화제작/인기작/주목작) |
| 무한스크롤 수정 | ✅ | observer 훅 개선 + "더 보기" 버튼 fallback |

### Phase 16: Favicon & 날씨 한글화 & 배너 개선 (2026-02-11)

| 항목 | 상태 | 비고 |
|------|------|------|
| Favicon 추가 | ✅ | .ico (Pillow 생성) + .svg, layout.tsx icons 설정 |
| 헤더 로고 아이콘 | ✅ | R 아이콘 + "ecflix" 텍스트 조합 |
| 날씨 한글 도시명 | ✅ | Reverse Geocoding API + 70개+ 매핑 딕셔너리 |
| 날씨 도시명 헤더 표시 | ✅ | WeatherIndicator에 도시명 추가 (데스크톱만) |
| 날씨 dong 문제 해결 | ✅ | 역지오코딩 local_names.ko 사용 |
| FeaturedBanner 여백 축소 | ✅ | 배너 높이/마진 감소, 섹션 간격 개선 |
| FeaturedBanner 제목 전체 표시 | ✅ | truncate 제거, 긴 제목 줄바꿈 표시 |

### Phase 17: DB 스키마 정리 & 프로덕션 동기화 (2026-02-12)

| 항목 | 상태 | 비고 |
|------|------|------|
| overview_ko 컬럼 제거 | ✅ | overview가 한글 통일 → overview_ko 불필요 |
| overview_lang 컬럼 제거 | ✅ | 언어 구분 불필요 (전체 한글) |
| 백엔드 모델/스키마 정리 | ✅ | Movie 모델, MovieDetail 스키마에서 필드 제거 |
| 프론트엔드 타입/로직 정리 | ✅ | types/index.ts, MovieModal, 상세페이지 |
| 스크립트 참조 정리 | ✅ | llm_emotion_tags, regenerate_emotion_tags, llm API |
| 로컬 DB 마이그레이션 | ✅ | ALTER TABLE DROP COLUMN (24 → 22컬럼) |
| 프로덕션 DB 동기화 | ✅ | pg_dump → pg_restore (Railway) |
| Railway 백엔드 재배포 | ✅ | CORS 500 에러 해결 (코드-DB 불일치 해소) |

### Phase 18: cast_ko 한글 음역 변환 & 출연진 표시 개선 (2026-02-12)

| 항목 | 상태 | 비고 |
|------|------|------|
| 영어 배우 이름 분석 | ✅ | 33,529개 고유 영어 이름, 22,451편 영화 |
| Claude API 음역 변환 (1차) | ✅ | 2편+ 등장 배우 9,714개, 49분, $3.33 |
| Claude API 음역 변환 (2차) | ✅ | 1편 등장 배우 23,815개, $8.36 |
| 진행 파일 원자적 쓰기 수정 | ✅ | Windows OSError → tmp+rename 패턴 |
| cast_ko 92.8% 한글화 달성 | ✅ | 33,442개 이름 번역, 22,451편 업데이트 |
| persons 테이블 부분 업데이트 | ✅ | 기존 매핑으로 31,672명 업데이트 |
| 프론트엔드 cast_ko 전환 | ✅ | cast_members(persons) → cast_ko(movies) 사용 |
| 프로덕션 DB 동기화 | ✅ | pg_dump → pg_restore (여러 차례) |
| 프로젝트 리뷰 문서 작성 | ✅ | docs/PROJECT_REVIEW.md 생성 |

### Phase 19: cast_ko 외국어 이름 완전 한글화 (2026-02-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| 외국어 이름 분석 | ✅ | 4,253개 (중국어 1,902, 영어 1,902, 일본어 139 등) |
| Claude API 한글 음역 변환 | ✅ | 2,869개 실제 변환, 4,570편 영화 업데이트, $1.78 |
| Zero-width space 정리 | ✅ | 22편 데이터 정리 |
| Unicode NFC 정규화 | ✅ | 깨진 데이터 14편 제거 |
| cast_ko 100% 한글화 달성 | ✅ | 42,759/42,759편 (98.7% → 100.00%) |
| 프로덕션 DB 동기화 + 배포 | ✅ | Railway + Vercel |

### Phase 20: SEO 동적 OG 메타태그 최적화 (2026-02-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| 영화 상세 페이지 동적 OG 태그 | ✅ | `movies/[id]/layout.tsx` 신규 (generateMetadata) |
| og:title / og:description | ✅ | 한글 제목, 줄거리 160자 제한 |
| og:image | ✅ | TMDB 포스터 (w500) |
| og:type / og:url | ✅ | video.movie, 정규 URL |
| twitter:card | ✅ | summary_large_image (영화), summary (홈) |
| 루트 레이아웃 기본 OG 태그 | ✅ | metadataBase, og:site_name, locale=ko_KR |
| API 실패 시 fallback | ✅ | 기본 "RecFlix" 타이틀 반환 |
| 카카오톡 프리뷰 검증 | ✅ | 포스터/제목/줄거리 정상 표시 확인 |

### Phase 21: 자체 유사 영화 계산 엔진 (2026-02-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| 유사도 계산 스크립트 작성 | ✅ | `backend/scripts/compute_similar_movies.py` |
| 유사도 공식 | ✅ | 0.5×emotion코사인 + 0.3×mbti코사인 + 0.2×장르Jaccard |
| 장르 겹침 필터링 | ✅ | 같은 장르 1개 이상 쌍만 비교 (효율화) |
| 품질 필터 | ✅ | weighted_score >= 6.0 후보만 (39,791편) |
| LLM 분석 영화 우대 | ✅ | +0.05 보너스 (1,711편) |
| 전체 계산 실행 | ✅ | 42,917편, Top 10, 429,170개 유사 관계 (~40분) |
| similar_movies 테이블 갱신 | ✅ | 기존 TMDB 데이터 → 자체 계산 결과로 교체 |
| 에러 바운더리 추가 | ✅ | 전역 error.tsx, 404 not-found.tsx, 영화 상세 error.tsx |
| 프로덕션 DB 동기화 | ✅ | pg_dump → pg_restore (Railway) |

### Phase 22: 검색 자동완성 강화 (2026-02-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| 검색 키워드 하이라이팅 | ✅ | HighlightText 컴포넌트 (볼드+primary 색상) |
| autocomplete Redis 캐싱 | ✅ | TTL 1시간, `autocomplete:{query}:{limit}` 캐시 키 |
| weighted_score 반환 추가 | ✅ | autocomplete API 응답에 품질 점수 포함 |
| 키보드 네비게이션 | ✅ | 방향키 이동, Enter 선택, ESC 닫기 |
| HighlightText 검색어 하이라이팅 | ✅ | 영화 제목 + 영어 제목 + 배우 이름 하이라이팅 |
| Header 검색창 자동완성 통합 | ✅ | 데스크톱/모바일 검색창을 SearchAutocomplete로 교체 |
| 별점(weighted_score) 표시 | ✅ | 자동완성 드롭다운 항목에 별 아이콘 + 점수 |

### Phase 23: 큐레이션 서브타이틀 시스템 (2026-02-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| curationMessages.ts 상수 파일 | ✅ | 날씨/기분/MBTI/고정 서브타이틀 메시지 |
| MovieRow subtitle prop 추가 | ✅ | 제목 아래 보조 설명 텍스트 |
| HybridMovieRow subtitle prop 추가 | ✅ | 맞춤 추천 섹션 서브타이틀 |
| 홈 페이지 서브타이틀 매칭 로직 | ✅ | getRowSubtitle(), getHybridSubtitle() 헬퍼 |
| 날씨 4종 서브타이틀 | ✅ | 맑음/비/흐림/눈별 큐레이션 메시지 |
| 기분 8종 서브타이틀 | ✅ | 8개 기분별 큐레이션 메시지 |
| MBTI 16종 서브타이틀 | ✅ | 16개 유형별 성격 기반 메시지 |
| 고정 서브타이틀 | ✅ | 인기영화, 높은평점, 맞춤추천 기본 |

### Phase 24: 기분(Mood) 8개 카테고리 확장 (2026-02-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| Backend gloomy/stifled 추가 | ✅ | MOOD_EMOTION_MAPPING, MOOD_LABELS, MOOD_SECTION_CONFIG |
| emotion_tags 매핑 | ✅ | gloomy→deep+healing, stifled→tension+energy |
| API 정규식 패턴 확장 | ✅ | 8개 mood 값 허용 |
| Frontend MoodType 확장 | ✅ | types/index.ts에 gloomy, stifled 추가 |
| FeaturedBanner 기분 UI 개선 | ✅ | 2x3 → 2x4 그리드, 8개 기분 버튼 |
| 기분 라벨 개선 | ✅ | 평온한/긴장된/활기찬/몽글몽글한/상상에빠진/유쾌한/울적한/답답한 |

### Phase 25: 서브타이틀 고도화 & 추천 품질 튜닝 (2026-02-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| 서브타이틀 3종 랜덤 표시 | ✅ | 30종 × 3개 = 90개 문구, 페이지 로드마다 랜덤 |
| 하이드레이션 안전 랜덤 | ✅ | useState + useEffect로 클라이언트에서만 인덱스 결정 |
| 서브타이틀 위치 변경 | ✅ | 제목 아래 → 제목 우측 같은 줄 (flex items-baseline) |
| 모바일 서브타이틀 숨김 | ✅ | hidden sm:inline (모바일 공간 절약) |
| MBTI 서브타이틀 매칭 수정 | ✅ | user?.mbti 의존 제거, 타이틀에서 정규식 추출 |
| 맞춤 추천 서브타이틀 수정 | ✅ | MOOD 문구 → FIXED_SUBTITLES.hybrid 전용 문구 |
| stifled 매핑 순서 수정 | ✅ | tension→energy 우선으로 변경 (사이다 영화 추천) |
| gloomy/stifled 추천 품질 검증 | ✅ | gloomy: deep≥0.5 100%, stifled: 액션/모험 위주 확인 |

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
│   │   ├── movies/[id]/layout.tsx
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
│   │   ├── ui/HighlightText.tsx
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
- [x] **LLM emotion_tags 재분석** (1,711편, 새 프롬프트) (2026-02-10)
- [x] **품질 필터 통합** (weighted_score >= 6.0) (2026-02-10)
- [x] **연령등급 필터링** (age_rating: all/family/teen/adult) (2026-02-10)
- [x] **Hybrid 가중치 v2 튜닝** (Mood 0.30 강화) (2026-02-10)
- [x] **품질 보정 연속화** (×0.85~1.0) (2026-02-10)
- [x] **DB 덤프 공유** (data/recflix_db.dump) (2026-02-10)
- [x] **보안: DB 비밀번호 노출 대응** (Railway DB 교체) (2026-02-11)
- [x] **Vercel 포스터 미표시 수정** (Image Optimization off) (2026-02-11)
- [x] **제작 국가 한국어 표시** (production_countries_ko) (2026-02-11)
- [x] **평점 정렬 weighted_score 통일** (홈/검색/API) (2026-02-11)
- [x] **인기도 로그 스케일 변환** (10점 만점 + 라벨) (2026-02-11)
- [x] **무한스크롤 수정** (observer 훅 + 더보기 버튼) (2026-02-11)
- [x] **Favicon 추가** (.ico + .svg, 빨간 배경 R 로고) (2026-02-11)
- [x] **헤더 로고 아이콘** (R 아이콘 + "ecflix" 조합) (2026-02-11)
- [x] **날씨 한글 도시명** (Reverse Geocoding + 매핑) (2026-02-11)
- [x] **FeaturedBanner 개선** (여백 축소 + 제목 전체 표시) (2026-02-11)
- [x] **overview_ko/overview_lang 컬럼 제거** (DB 스키마 정리, 24→22컬럼) (2026-02-12)
- [x] **프로덕션 DB 동기화 + Railway 재배포** (CORS 500 에러 해결) (2026-02-12)
- [x] **cast_ko 한글 음역 변환** (33,442개 이름, Claude API $11.69) (2026-02-12)
- [x] **출연진 표시 cast_ko 전환** (persons → movies.cast_ko, 92.8% 한글) (2026-02-12)
- [x] **프로젝트 리뷰 문서** (docs/PROJECT_REVIEW.md) (2026-02-12)
- [x] **cast_ko 외국어 이름 완전 한글화** (4,253개, 100% 달성) (2026-02-13)
- [x] **SEO 동적 OG 메타태그** (영화 상세 페이지 SNS 프리뷰) (2026-02-13)
- [x] **에러 바운더리** (전역, 404, 영화 상세) (2026-02-13)
- [x] **자체 유사 영화 계산** (42,917편 x Top10, 429,170개 관계) (2026-02-13)
- [x] **검색 키워드 하이라이팅** (HighlightText 컴포넌트) (2026-02-13)
- [x] **검색 자동완성 강화** (키보드 네비게이션, Redis 캐싱, Header 통합) (2026-02-13)
- [x] **큐레이션 서브타이틀** (날씨/기분/MBTI/고정 메시지 시스템) (2026-02-13)
- [x] **기분 8개 카테고리 확장** (gloomy 울적한, stifled 답답한 추가) (2026-02-13)
- [x] **서브타이틀 3종 랜덤** (90개 문구, 제목 우측 배치, MBTI 매칭 수정) (2026-02-13)
- [x] **stifled 매핑 튜닝** (energy 우선 정렬로 사이다 영화 추천) (2026-02-13)

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
13. **GitGuardian DB 비밀번호 노출**: Railway DB 교체 + .gitignore 보호 (2026-02-11)
14. **Vercel 포스터 미표시**: Image Optimization 할당량 초과 → unoptimized 설정 (2026-02-11)
15. **uvicorn --reload 불완전 리로드**: 파일 변경 감지되나 모듈 미갱신 → 수동 재시작 필요 (2026-02-11)
16. **favicon.ico 404**: Next.js `app/icon.tsx` (ImageResponse)는 Windows에서 경로 버그 → `public/favicon.ico` + SVG 정적 파일로 해결 (2026-02-11)
17. **날씨 "dong" 영어 표시**: OpenWeatherMap `name` 필드는 `lang` 파라미터 무관 → Reverse Geocoding API `local_names.ko`로 한글 도시명 추출 (2026-02-11)
18. **날씨 캐시 이전 데이터 잔존**: Redis + localStorage 캐시 키 버전업 (`v2`→`v3`)으로 무효화 (2026-02-11)
19. **CORS 500 에러 (overview_ko 제거 후)**: DB에서 컬럼 삭제 후 코드 미배포 → 500 에러 응답에 CORS 헤더 누락 → Railway 재배포로 해결 (2026-02-12)
