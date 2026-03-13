# RecFlix 개발 진행 상황

**최종 업데이트**: 2026-03-13 (v2.0.0 + 시연 품질 개선)

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

### Phase 26: 컨텍스트 큐레이션 시스템 (2026-02-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| 큐레이션 문구 3→6개 확장 | ✅ | 31종 × 6개 = 186개 (기존 90개 → 186개) |
| contextCuration.ts 신규 생성 | ✅ | 시간대/계절/기온 감지 로직 분리 |
| TIME_SUBTITLES 추가 | ✅ | 아침/오후/저녁/심야 4종 × 6개 = 24개 |
| SEASON_SUBTITLES 추가 | ✅ | 봄/여름/가을/겨울 4종 × 6개 = 24개 |
| TEMP_SUBTITLES 추가 | ✅ | 영하/추움/서늘/온화/따뜻/더움 6종 × 4개 = 24개 |
| 기존 문구 중립화 | ✅ | 시간/계절/기온 종속 표현 제거 (날씨 섹션 포함) |
| 맞춤 추천 → 시간대 적용 | ✅ | TIME_SUBTITLES[timeOfDay] |
| 날씨 추천 → 계절+기온 교대 | ✅ | 짝수 idx=계절, 홀수 idx=기온 |
| weather.temperature 연동 | ✅ | OpenWeatherMap 기온 → TempRange 변환 |
| 하이드레이션 안전 | ✅ | useEffect에서만 컨텍스트 설정 |

### Phase 27: 프로젝트 컨텍스트 & 코드 품질 환경 구축 (2026-02-19)

| 항목 | 상태 | 비고 |
|------|------|------|
| CLAUDE.md 재작성 | ✅ | 플레이북 표준 형식 (173줄), 기술스택/구조/규칙 통합 |
| DECISION.md 생성 | ✅ | 7개 아키텍처 의사결정 기록 |
| .claude/skills/ 7개 스킬 | ✅ | workflow, recommendation, curation, weather, database, deployment, frontend-patterns |
| code-quality 스킬 추가 | ✅ | Karpathy 원칙, 500줄+ 파일 현황, 분리 가이드 |
| .claude/settings.json | ✅ | context7, security-guidance MCP 설정 |

### Phase 28: 코드 품질 리팩토링 (2026-02-19)

| 항목 | 상태 | 비고 |
|------|------|------|
| movies/[id]/page.tsx 분리 | ✅ | 622줄 → 231줄 + 4개 서브 컴포넌트 (MovieHero, MovieSidebar, SimilarMovies, MovieDetailSkeleton) |
| recommendations.py 분리 | ✅ | 770줄 → 347줄 + recommendation_engine.py(330줄) + recommendation_constants.py(76줄) |

### Phase 29: 운영 안정성 강화 (2026-02-19)

| 항목 | 상태 | 비고 |
|------|------|------|
| Sentry 연동 | ✅ | Backend/Frontend SDK, DSN 없으면 비활성화, traces 10% |
| 에러 핸들링 표준화 | ✅ | AppException, 글로벌 핸들러 4개, 통일 에러 포맷 {error, message} |
| Rate Limiting (slowapi) | ✅ | 39개 엔드포인트 (인증 5/분, 추천 15/분, 검색 30/분, 조회 60/분) |
| 환경변수 검증 강화 | ✅ | DATABASE_URL, JWT_SECRET_KEY 필수 validator |
| lifespan 시작 로그 | ✅ | 환경, DB, Redis, Sentry, Weather API 상태 요약 |

### Phase 30: 사용자 행동 이벤트 분석 기반 (2026-02-19)

| 항목 | 상태 | 비고 |
|------|------|------|
| user_events 테이블 | ✅ | 10종 이벤트, JSONB metadata, 복합 인덱스 3개 |
| 이벤트 API (Backend) | ✅ | POST /events, POST /events/batch(최대 50), GET /events/stats |
| eventTracker.ts 싱글톤 | ✅ | 배치 큐 + 5초 auto-flush + Beacon API (페이지 이탈 시) |
| useImpressionTracker 훅 | ✅ | IntersectionObserver 기반 섹션 노출 감지 |
| 프론트엔드 9개 이벤트 삽입 | ✅ | movie_click, detail_view/leave, impression, search/click, rating, favorite |

### Phase 31: 추천 고도화 - 협업 필터링 (2026-02-19)

| 항목 | 상태 | 비고 |
|------|------|------|
| MovieLens 25M TMDB 매핑 | ✅ | 20,372편 매핑 (47.5%), 22.5M 평점, 162K 사용자 |
| 오프라인 평가 프레임워크 | ✅ | 3 베이스라인 (Popularity, Global Mean, Item Mean) |
| SVD 모델 학습 (scipy) | ✅ | 50K users × 17.5K items, k=100, RMSE 0.8768 (-9.2%) |
| CF 프로덕션 통합 | ✅ | item_bias 기반 품질 시그널, 25% 가중치 (v3) |
| recommendation_cf.py | ✅ | SVD 모델 로드 + CF 점수 예측 모듈 |

### Phase 32: A/B 테스트 & 소셜 로그인 (2026-02-19)

| 항목 | 상태 | 비고 |
|------|------|------|
| A/B 테스트 프레임워크 | ✅ | experiment_group (control/test_a/test_b), 가중치 분기 |
| AB Report 엔드포인트 | ✅ | GET /events/ab-report (그룹별 CTR, 전환율 집계) |
| not_interested 이벤트 | ✅ | 10번째 이벤트 타입 추가 |
| Kakao OAuth 로그인 | ✅ | POST /auth/kakao + 콜백 페이지 |
| Google OAuth 로그인 | ✅ | POST /auth/google + 콜백 페이지 |
| 온보딩 2단계 | ✅ | 장르 선택(3~5개) + 영화 평가(40편 중 5편 이상), /onboarding |
| DB 마이그레이션 SQL | ✅ | migrate_phase4.sql (experiment_group + 소셜/온보딩 컬럼) |
| **OAuth 400 에러 수정** | ✅ | Vercel 환경변수 `\n` 제거 + `.trim()` 안전장치 |
| **Pydantic 이메일 수정** | ✅ | `@recflix.local` → `@noreply.example.com` |
| **OAuth 콜백 에러 전달** | ✅ | 카카오/Google 콜백에서 detail 파라미터로 에러 상세 전달 |
| **프로덕션 검증** | ✅ | 카카오 로그인 ✅, Google 로그인 ✅ |

### Phase 33: 시맨틱 검색 (2026-02-20)

| 항목 | 상태 | 비고 |
|------|------|------|
| Voyage AI 임베딩 생성 | ✅ | voyage-multilingual-2, 42,917편, git-lfs 저장 |
| 시맨틱 검색 Backend API | ✅ | NumPy 인메모리 코사인 유사도, `/movies/search/semantic` |
| 시맨틱 검색 Frontend UI | ✅ | 자연어 감지 + AI 추천 섹션 (검색 페이지 통합) |
| 프로덕션 배포 + 타이밍 로그 | ✅ | Railway 배포, 응답시간 측정 로그 추가 |
| 재랭킹 개선 | ✅ | 인기도+품질 복합점수 + match_reason 필드 추가 |
| Voyage AI RPM 제한 대응 | ✅ | 3 RPM 제한에 맞춘 딜레이 조정 |

### Phase 34: 추천 다양성/신선도 정책 (2026-02-20)

| 항목 | 상태 | 비고 |
|------|------|------|
| 장르 다양성 보장 | ✅ | 동일 장르 연속 제한 알고리즘 |
| 신선도 가중치 | ✅ | 최신 영화 우대 보정 |
| Serendipity 삽입 | ✅ | 의외의 발견 영화 혼합 |
| 중복 제거 | ✅ | 섹션 간 영화 중복 방지 |

### Phase 35: SVD 모델 프로덕션 배포 (2026-02-20)

| 항목 | 상태 | 비고 |
|------|------|------|
| Dockerfile LFS 다운로드 | ✅ | git-lfs로 SVD 모델 + 임베딩 다운로드 |
| .dockerignore 최적화 | ✅ | 불필요 파일 제외 (빌드 속도 개선) |
| Railway 빌드 설정 수정 | ✅ | 루트 railway.toml + Dockerfile 경로 보정 |
| startCommand 수정 | ✅ | `sh -c` 래퍼 (PORT 변수 확장) |
| numpy 2.x 호환성 | ✅ | SVD 모델 pickle 호환 + pandas/scipy 버전 제약 완화 |
| 프로덕션 검증 | ✅ | Railway 배포 + 헬스체크 정상 |

### Phase 36: 헬스체크 + CI/CD 파이프라인 (2026-02-20)

| 항목 | 상태 | 비고 |
|------|------|------|
| 헬스체크 엔드포인트 | ✅ | `GET /health` (DB, Redis, SVD, 임베딩 상태 체크) |
| GitHub Actions CI | ✅ | Backend Lint (ruff) + Frontend Build (next build) |
| CD 자동 배포 (Railway) | ✅ | `railway up --service backend --environment production --detach` |
| Vercel 자동 배포 | ✅ | GitHub 연동으로 push 시 자동 배포 (Actions 불필요) |
| Railway Project Token 설정 | ✅ | GitHub Secrets 등록 + 프로덕션 배포 검증 |
| ruff 버전 고정 | ✅ | 0.1.13, critical 규칙만 체크 |

### Phase 37: 추천 이유 생성 (2026-02-20)

| 항목 | 상태 | 비고 |
|------|------|------|
| 템플릿 기반 추천 이유 모듈 | ✅ | `recommendation_reason.py` (228줄, 43개 템플릿) |
| HybridMovieItem 스키마 확장 | ✅ | `recommendation_reason: str = ""` 필드 추가 |
| 추천 API 연동 | ✅ | `generate_reason()` 호출, 홈/hybrid 엔드포인트 |
| Frontend 타입 확장 | ✅ | `HybridMovie.recommendation_reason?: string` |
| HybridMovieCard 추천 이유 표시 | ✅ | 태그 아래 이탤릭 텍스트 (line-clamp-2) |
| 프로덕션 배포 + 검증 | ✅ | CI/CD 자동 배포 성공, 헬스체크 정상 |

### Phase 38: 프로덕션 DB 마이그레이션 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| users 7컬럼 추가 | ✅ | experiment_group, kakao_id, google_id, profile_image, auth_provider, onboarding_completed, preferred_genres |
| user_events 테이블 생성 | ✅ | 7컬럼 + 5개 인덱스 (멱등 실행) |
| 타입/제약조건 보정 | ✅ | preferred_genres text[]→TEXT, auth_provider/onboarding_completed NOT NULL |
| A/B 그룹 재배정 | ✅ | 기존 8명 사용자 id%3 기반 3등분 |
| events.py 버그 수정 | ✅ | ab-report raw SQL `metadata_` → `metadata` (4곳) |
| 프로덕션 스모크 테스트 | ✅ | /health, /movies, /recommendations, /semantic-search 정상 |

### Phase 39: 문서 업데이트 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| Phase 33~38 문서 반영 | ✅ | CHANGELOG, PROGRESS, CLAUDE.md 동기화 |

### Phase 40: 설정 경량화 및 고도화 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| skills/hooks/docs 고도화 | ✅ | clean_project.py, Makefile, gitignore 업데이트 |

### Phase 41: 안전/정확성 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| distinct 쿼리 수정 | ✅ | 중복 결과 제거 |
| refresh 토큰 회전 강화 | ✅ | JTI Redis 검증 + 탈취 감지 |
| rate limit 강화 | ✅ | 프록시 인식 IP 추출 |

### Phase 42: DB 성능 최적화 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| N+1 쿼리 제거 | ✅ | selectinload 적용 |
| 쿼리 통합 | ✅ | 다중 쿼리 → 단일 쿼리 |
| pg_trgm GIN 인덱스 | ✅ | 자동완성 성능 개선 |

### Phase 43: API 내결함성 + 파일 분할 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| API 클라이언트 내결함성 | ✅ | 재시도, 타임아웃, fallback |
| 검색 병렬화 | ✅ | Promise.all 병렬 API 호출 |
| 파일 분할 | ✅ | 대형 컴포넌트 분리 |
| 애니메이션 경량화 | ✅ | Framer Motion 최적화 |

### Phase 44: SEO + 접근성 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| SEO 메타데이터 강화 | ✅ | 동적 OG 태그 개선 |
| loading.tsx 추가 | ✅ | 스켈레톤 로딩 UI |
| 접근성 개선 | ✅ | aria-label, role, focus 관리 |
| 캐시 키 표준화 | ✅ | 캐시 키 네이밍 통일 |

### Phase 45: 코드 품질 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| ruff 이슈 제거 | ✅ | 143→0 이슈 |
| any 타입 제거 | ✅ | 8→0개 |
| except 구체화 | ✅ | bare except → 구체적 예외 |
| focus trap | ✅ | 모달/메뉴 키보드 트랩 |

### Phase 46: 추천 콜드스타트 + GDPR + 보안 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| 추천 콜드스타트 | ✅ | preferred_genres 기반 fallback |
| 피드백 루프 | ✅ | 클릭/평점 반영 |
| GDPR 계정 삭제 | ✅ | DELETE /users/me |
| 보안 강화 | ✅ | JWT/CORS 검증 강화 |
| Error Boundary 개선 | ✅ | 전역 에러 처리 개선 |

### Phase 47: TMDB 트레일러 연동 (2026-02-23)

| 항목 | 상태 | 비고 |
|------|------|------|
| 트레일러 수집 스크립트 | ✅ | collect_trailers.py (28,486편, 66.4%) |
| DB 스키마 | ✅ | trailer_key 컬럼 추가 |
| API 스키마 | ✅ | MovieDetail/MovieListItem에 trailer_key 포함 |
| YouTube 임베드 UI | ✅ | TrailerModal 컴포넌트 |
| MovieHero/Sidebar 버튼 | ✅ | 트레일러 재생 버튼 추가 |

### Phase 48: async 최적화 + Alembic (2026-02-24)

| 항목 | 상태 | 비고 |
|------|------|------|
| bcrypt to_thread | ✅ | asyncio.to_thread() 래핑 |
| httpx AsyncClient 싱글턴 | ✅ | lifespan 관리 + OAuth 통합 |
| Alembic 초기화 | ✅ | Base.metadata.create_all() 제거, 빈 baseline |
| Dockerfile 체크섬 | ✅ | SHA256 무결성 검증 (4개 파일) |

### Phase 49: 시맨틱 재랭킹 + pytest + structlog (2026-02-24)

| 항목 | 상태 | 비고 |
|------|------|------|
| 시맨틱 재랭킹 v2 | ✅ | semantic 60%, popularity 15% (log), quality 25% |
| 스크립트 문서화 | ✅ | backend/scripts/README.md (16개) |
| pytest 기본 스위트 | ✅ | 14건 (10 passed, 4 skipped) |
| structlog 구조화 로깅 | ✅ | JSON (prod) / colored (dev) |
| X-Request-ID 미들웨어 | ✅ | structlog contextvars 바인딩 |
| CI pytest 추가 | ✅ | backend-test job (배포 필수 게이트) |

### Phase 50: 문서 최종화 + v1.0.0 릴리스 (2026-02-24)

| 항목 | 상태 | 비고 |
|------|------|------|
| README.md 전체 재작성 | ✅ | Phase 이력, 아키텍처, 기술 스택 |
| CHANGELOG.md Phase 46~50 | ✅ | v1.0.0 릴리스 항목 |
| docs/ARCHITECTURE.md 신규 | ✅ | 시스템 구조, 데이터 흐름, DB 스키마, 캐시, 인증 |
| PROGRESS.md Phase 39~50 | ✅ | 전체 완료 표시 |
| .claude/skills/ 동기화 | ✅ | Phase 46~50 변경사항 반영 |
| git tag v1.0.0 | ✅ | 프로덕션 릴리스 태그 |

### Phase 51: 모바일 UI/UX 개선 (2026-02-24)

| 항목 | 상태 | 비고 |
|------|------|------|
| 터치 영역 44px 점검 | ✅ | Apple HIG 기준, 15개 파일 수정 |
| 유도섹션 thumb zone | ✅ | 모바일 하단 고정, 데스크톱 기존 위치 |
| hover-only 대응 | ✅ | opacity-100 sm:opacity-0 sm:group-hover:opacity-100 |
| 배너 버튼 flex-wrap | ✅ | 360px overflow 방지 |

### Phase 52: A/B 테스트 강화 (2026-02-25)

| 항목 | 상태 | 비고 |
|------|------|------|
| FeaturedBanner 이벤트 추가 | ✅ | 상세보기 click + 트레일러 click |
| MovieModal 이벤트 보완 | ✅ | favorite_add/remove + rating (누락 해소) |
| 추천 컨텍스트 전파 | ✅ | from/pos URL 파라미터 → source_section/source_position |
| preferred_genres 가중치 3배 | ✅ | 콜드스타트 온보딩 장르 1 → 3 |
| Z-test 통계 유의성 | ✅ | ab_stats.py 신규 (math.erf 기반, scipy 불필요) |
| Wilson score 95% CI | ✅ | CTR 신뢰구간 |
| 추가 메트릭 7종 | ✅ | avg_rating_from_recs, return_rate, avg_session_events, funnel, daily_active_users, comparisons, ctr_ci |
| 실험 그룹 가중치 배정 | ✅ | EXPERIMENT_WEIGHTS 환경변수, _weighted_random_group() |
| events.py 리팩토링 | ✅ | ab-report 7개 헬퍼 함수 분리 |
| ABReport 스키마 확장 | ✅ | ABComparison, funnel, daily_active_users 등 |

### Phase 53: v2.0 ML 파이프라인 프로덕션 배포 (2026-02-27)

| 항목 | 상태 | 비고 |
|------|------|------|
| requirements.txt ML 패키지 | ✅ | torch==2.10.0+cpu, lightgbm==4.6.0, faiss-cpu==1.13.2 |
| Dockerfile v2.0 모델 다운로드 | ✅ | Two-Tower 4파일 + LGBM 1파일, SHA256 검증 |
| Git LFS 모델 파일 등록 | ✅ | .gitattributes 4패턴, 5파일 (~45MB) |
| Alembic 마이그레이션 | ✅ | reco_impressions, reco_interactions, reco_judgments 3테이블 |
| Railway 환경변수 | ✅ | TWO_TOWER_ENABLED=true, RERANKER_ENABLED=true |
| CI ML 패키지 제외 | ✅ | grep -v torch/lightgbm/faiss-cpu |
| CI 환경변수 추가 | ✅ | DATABASE_URL, JWT_SECRET_KEY |
| conftest.py UUID 호환성 | ✅ | PG_UUID → String(36) SQLite 변환 |
| lazy imports (torch/faiss/lgb) | ✅ | two_tower_retriever.py, reranker.py |
| Railway CLI npx 전환 | ✅ | npx @railway/cli@4.30.5 (npm install -g 불안정) |
| .railwayignore 추가 | ✅ | LFS 모델 파일 업로드 제외 (413 방지) |
| Dockerfile SHA256 수정 | ✅ | embedding_metadata.json 체크섬 업데이트 |
| numpy 2.x 업그레이드 | ✅ | SVD pickle 호환성 (numpy._core.numeric) |
| health 엔드포인트 v2.0 | ✅ | two_tower, reranker 상태 추가 |
| Railway 배포 성공 | ✅ | 모든 모델 로드 확인 (v2.0.0) |

### Phase 54: 프론트엔드 UI 개선 + 다크/라이트 모드 (2026-03-03)

| 항목 | 상태 | 비고 |
|------|------|------|
| 트레일러 새 탭 열기 | ✅ | YouTube 임베드 → 새 탭 링크 |
| 홈 한국 인기 영화 섹션 | ✅ | 한국 제작 영화 전용 섹션 추가 |
| 히어로 유도 UI 개선 | ✅ | 날씨/기분 유도 UI 헤더 드롭다운 이동 |
| 트레일러 UI 일관성 통일 | ✅ | 카드/모달/상세 트레일러 버튼 스타일 통일 |
| 날씨/기분 헤더 드롭다운 | ✅ | FeaturedBanner → Header 인라인 드롭다운 이동 |
| MBTI 헤더 인라인 모달 | ✅ | 별도 모달 → 헤더 드롭다운으로 변경 |
| CSS 변수 기반 테마 시스템 | ✅ | 6개 시맨틱 토큰 (surface/fg/overlay/divider) |
| 다크/라이트 모드 | ✅ | 40개+ 컴포넌트 시맨틱 토큰 적용, FOUC 방지 |
| themeStore | ✅ | Zustand persist, localStorage 영속화 |
| MBTI 비로그인 지원 | ✅ | localStorage("guest_mbti") 저장, 헤더 배지 표시 |
| 프로필 드롭다운 | ✅ | 아바타 클릭 → 설정/로그아웃 메뉴 |
| 설정 페이지 (/settings) | ✅ | 닉네임, MBTI, 장르, 테마 토글, 계정 삭제 |
| MBTI 드롭다운 일관성 | ✅ | 날씨/기분과 동일한 드롭다운 패턴 (4x4 그리드) |
| 프로필 드롭다운 중복 제거 | ✅ | 찜/평점 제거 (헤더 메뉴와 중복) |
| 설정 바로가기 제거 | ✅ | 중복 바로가기 섹션 삭제 |
| 모바일 드로어 MBTI 그리드 | ✅ | 날씨/기분과 동일한 그리드 패턴 |

### Phase 55: 시연 품질 개선 + 추천 알고리즘 조정 (2026-03-13)

| 항목 | 상태 | 비고 |
|------|------|------|
| 날씨 드롭다운 교차 동기화 | ✅ | CustomEvent("manual_weather_change") 패턴 |
| 온보딩 에러 처리 + 롤백 | ✅ | 평점 실패 시 UI 롤백, 에러 메시지 표시 |
| 204 No Content 응답 처리 | ✅ | fetchAPI에서 204 시 undefined 반환 (삭제 API 정상화) |
| 에러 메시지 파싱 개선 | ✅ | body.message/error/detail 순서 파싱 |
| MovieModal 장르 태그 클릭 | ✅ | 장르 클릭 시 /movies?genre= 이동 |
| 날씨 도시명 표시 | ✅ | Header에 "서울 · 맑음 15°C" 형식 |
| OAuth onboarding 분기 수정 | ✅ | isNew → onboarding_completed 기반 라우팅 |
| 계정 삭제 에러 피드백 | ✅ | alert()로 실패 알림 |
| hybrid_score % 정규화 | ✅ | Row 내 상대 정규화 65-99% (cold-start 4-6% 방지) |
| 기분 미선택 시 섹션 숨김 | ✅ | 기본값 "relaxed" 제거, mood=null이면 mood_row 미생성 |
| hybrid_row control 강제 | ✅ | Two-Tower/LGBM 비활성화, 항상 5축 가중합산 사용 |
| Reranker mood 매핑 | ✅ | 프론트 8종 → reranker 6종 vocabulary 변환 |
| MBTI 쿼리 override | ✅ | 쿼리 파라미터 우선, 없으면 user.mbti fallback |
| 한국 인기 영화 백엔드 이동 | ✅ | Top 100 → sample 50 + shuffle + dedup, weighted_score 필터 제거 |

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
│   │   │   ├── recommendation_engine.py
│   │   │   ├── recommendation_constants.py
│   │   │   ├── recommendation_cf.py
│   │   │   ├── recommendation_reason.py
│   │   │   ├── events.py
│   │   │   ├── ratings.py
│   │   │   ├── collections.py
│   │   │   ├── weather.py
│   │   │   ├── health.py
│   │   │   ├── interactions.py
│   │   │   └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── deps.py
│   │   │   ├── exceptions.py
│   │   │   └── rate_limit.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── weather.py
│   │   │   ├── llm.py
│   │   │   ├── two_tower_retriever.py
│   │   │   ├── reranker.py
│   │   │   ├── reco_logger.py
│   │   │   ├── interleaving.py
│   │   │   └── embedding.py
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
│   │   ├── settings/page.tsx
│   │   ├── movies/page.tsx
│   │   ├── movies/[id]/layout.tsx
│   │   ├── movies/[id]/page.tsx
│   │   ├── movies/[id]/components/
│   │   │   ├── MovieHero.tsx
│   │   │   ├── MovieSidebar.tsx
│   │   │   ├── SimilarMovies.tsx
│   │   │   └── MovieDetailSkeleton.tsx
│   │   ├── auth/kakao/callback/page.tsx
│   │   ├── auth/google/callback/page.tsx
│   │   ├── onboarding/page.tsx
│   │   ├── favorites/page.tsx
│   │   └── ratings/page.tsx
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── HeaderMobileDrawer.tsx
│   │   │   ├── MobileNav.tsx
│   │   │   ├── MBTIModal.tsx
│   │   │   └── ThemeProvider.tsx
│   │   ├── movie/
│   │   │   ├── MovieCard.tsx
│   │   │   ├── MovieRow.tsx
│   │   │   ├── MovieModal.tsx
│   │   │   ├── FeaturedBanner.tsx
│   │   │   ├── HybridMovieRow.tsx
│   │   │   ├── HybridMovieCard.tsx
│   │   │   ├── MovieGrid.tsx
│   │   │   ├── MovieFilters.tsx
│   │   │   └── TrailerModal.tsx
│   │   ├── weather/WeatherBanner.tsx
│   │   ├── search/
│   │   │   ├── SearchAutocomplete.tsx
│   │   │   └── SearchResults.tsx
│   │   ├── ui/
│   │   │   ├── HighlightText.tsx
│   │   │   └── Skeleton.tsx
│   │   └── ErrorBoundary.tsx
│   ├── hooks/
│   │   ├── useWeather.ts
│   │   ├── useDebounce.ts
│   │   ├── useInfiniteScroll.ts
│   │   └── useImpressionTracker.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── interactionStore.ts
│   │   ├── themeStore.ts
│   │   └── useMoodStore.ts
│   ├── lib/
│   │   ├── api.ts
│   │   ├── eventTracker.ts
│   │   ├── curationMessages.ts
│   │   ├── contextCuration.ts
│   │   ├── searchUtils.ts
│   │   ├── constants.ts
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
- [x] **CLAUDE.md + skills 환경 구축** (플레이북 표준, 7개 도메인 스킬) (2026-02-19)
- [x] **코드 리팩토링** (movies/[id] 622→231줄, recommendations 770→347줄) (2026-02-19)
- [x] **Sentry 연동 + 에러 핸들링 표준화** (글로벌 핸들러 4개, 통일 포맷) (2026-02-19)
- [x] **Rate Limiting** (slowapi, 39개 엔드포인트) (2026-02-19)
- [x] **사용자 행동 이벤트 로깅** (Backend API + Frontend 트래킹 + Beacon API) (2026-02-19)
- [x] **MovieLens 25M 매핑 + 오프라인 평가** (20,372편, 3 베이스라인) (2026-02-19)
- [x] **협업 필터링 SVD** (RMSE 0.8768, CF 25% 가중치 통합) (2026-02-19)
- [x] **A/B 테스트 프레임워크** (3그룹 분기, AB Report) (2026-02-19)
- [x] **소셜 로그인** (Kakao/Google OAuth + 콜백) (2026-02-19)
- [x] **온보딩** (장르 선택 + 영화 평가 2단계) (2026-02-19)
- [x] **시맨틱 검색** (Voyage AI 임베딩 + NumPy 코사인 유사도 + 재랭킹) (2026-02-20)
- [x] **추천 다양성/신선도** (장르 다양성 + 신선도 + serendipity + 중복 제거) (2026-02-20)
- [x] **SVD 모델 프로덕션 배포** (Dockerfile LFS + numpy 2.x 호환) (2026-02-20)
- [x] **헬스체크 엔드포인트** (`GET /health`, DB/Redis/SVD/임베딩 상태) (2026-02-20)
- [x] **CI/CD 파이프라인** (GitHub Actions CI + Railway CD 자동 배포) (2026-02-20)
- [x] **추천 이유 생성** (템플릿 기반 43개 패턴, $0 비용) (2026-02-20)
- [x] **프로덕션 DB 마이그레이션** (user_events + users 7컬럼 + 타입 보정) (2026-02-23)
- [x] **설정 경량화 + 안전/정확성 강화** (Phase 39-41) (2026-02-23)
- [x] **DB 성능 최적화** (N+1 제거, pg_trgm GIN) (2026-02-23)
- [x] **API 내결함성 + 파일 분할** (재시도, 병렬화, 애니메이션 경량화) (2026-02-23)
- [x] **SEO + 접근성 + 코드 품질** (loading.tsx, ruff 0이슈, any 0개) (2026-02-23)
- [x] **추천 콜드스타트 + GDPR 계정 삭제 + 보안 강화** (Phase 46) (2026-02-23)
- [x] **TMDB 트레일러 연동** (28,486편, YouTube 임베드 UI) (2026-02-23)
- [x] **async 블로킹 해소 + Alembic 마이그레이션** (Phase 48) (2026-02-24)
- [x] **pytest 14건 + structlog 구조화 로깅 + 시맨틱 재랭킹 v2** (Phase 49) (2026-02-24)
- [x] **문서 최종화 + v1.0.0 릴리스** (Phase 50) (2026-02-24)
- [x] **모바일 UI/UX 개선** (터치 영역 44px + 유도섹션 thumb zone + hover-only 대응) (2026-02-24)
- [x] **A/B 테스트 강화** (이벤트 사각지대 해소 + 통계 유의성 Z-test + 추가 메트릭 + 그룹 가중치) (2026-02-25)
- [x] **v2.0 ML 파이프라인 프로덕션 배포** (Two-Tower + LGBM + FAISS + reco_* 테이블 + CI/CD 수정) (2026-02-27)
- [x] **프론트엔드 UI 개선** (트레일러 새 탭, 한국 인기 영화, 헤더 드롭다운) (2026-03-03)
- [x] **다크/라이트 모드** (CSS 변수 시맨틱 토큰, 40개+ 컴포넌트 적용, FOUC 방지) (2026-03-03)
- [x] **MBTI 비로그인 + 프로필 드롭다운 + 설정 페이지** (2026-03-03)
- [x] **MBTI 드롭다운 일관성 + 중복 메뉴 제거** (날씨/기분과 동일 패턴, 프로필/설정 중복 정리) (2026-03-03)

### 향후 개선사항
- [ ] PWA 지원
- [ ] 추천 알고리즘 평가 대시보드 (A/B 테스트 결과 시각화)
- [ ] 사용자 리뷰/코멘트 기능
- [ ] PostgreSQL CI 테스트 (JSONB/pg_trgm 포함)

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
20. **소셜 로그인 OAuth 400**: Vercel 환경변수 값 끝에 `\n` 포함 → URLSearchParams가 `%0A`로 인코딩 → OAuth 제공자 400 에러. `.trim()` 추가 + Vercel 환경변수 `printf`로 재등록 (2026-02-19)
21. **Pydantic EmailStr `.local` 도메인 거부**: 이메일 없는 소셜 사용자 `@recflix.local` → `@noreply.example.com` 변경 (2026-02-19)
22. **Railway CD "Invalid RAILWAY_TOKEN"**: Account Token이 아닌 **Project Token** 필요 → Railway Dashboard에서 프로젝트 설정 > Tokens에서 생성 (2026-02-20)
23. **numpy 2.x pickle 호환성**: SVD 모델(numpy 1.x로 학습)이 numpy 2.x에서 로드 실패 → numpy/pandas/scipy 버전 업데이트로 해결 (2026-02-20)
24. **Dockerfile SHA256 불일치**: embedding_metadata.json 파일 변경 후 체크섬 미갱신 → 체크섬 재계산 (2026-02-27)
25. **Railway 413 Payload Too Large**: LFS 모델 파일 포함 258MB 업로드 → `.railwayignore`로 모델 파일 제외 (2026-02-27)
26. **Railway CLI npm install 실패**: `npm install -g @railway/cli` CI 불안정 → `npx @railway/cli@4.30.5` 직접 실행 (2026-02-27)
27. **numpy._core.numeric ModuleNotFoundError**: SVD 모델이 numpy 2.x로 피클 → 프로덕션 numpy 1.26 → 2.x 업그레이드 (2026-02-27)
