# Changelog

All notable changes to RecFlix will be documented in this file.

## [Unreleased]

---

## [2026-02-13]

### Added
- **자체 유사 영화 계산 엔진**: TMDB 데이터 대신 RecFlix 자체 유사도 기반으로 교체
  - 유사도 = 0.5×emotion_tags 코사인 + 0.3×mbti_scores 코사인 + 0.2×장르 Jaccard
  - 품질 필터: `weighted_score >= 6.0` (39,791편 후보)
  - LLM 분석 영화 우대: +0.05 보너스 (1,711편)
  - 장르 겹침 필터링으로 계산 효율화
  - 42,917편 × Top 10 = 429,170개 유사 관계 저장 (~40분)
  - 스크립트: `backend/scripts/compute_similar_movies.py` (`--dry-run` 지원)
- **SEO 동적 OG 메타태그**: 영화 상세 페이지 SNS 공유 프리뷰 최적화
  - `frontend/app/movies/[id]/layout.tsx` 신규 (generateMetadata)
  - og:title(한글 제목), og:description(줄거리 160자), og:image(TMDB 포스터)
  - twitter:card=summary_large_image, API 실패 시 fallback
  - 루트 레이아웃: metadataBase, og:site_name, locale=ko_KR
  - 카카오톡 프리뷰 정상 확인
- **에러 바운더리**: 전역 에러 페이지, 404 페이지, 영화 상세 전용 에러 페이지
  - `frontend/app/error.tsx` - 전역 에러 (다시 시도 버튼)
  - `frontend/app/not-found.tsx` - 404 (홈으로 돌아가기)
  - `frontend/app/movies/[id]/error.tsx` - 영화 상세 에러 (다시 시도 + 홈)
- **cast_ko 외국어 이름 한글 음역 변환**: Claude API로 4,253개 이름 처리 ($1.78)
  - 중국어 1,902개, 영어 1,902개, 일본어 139개, 악센트 라틴 187개, 키릴 64개, 그리스어 11개, 기타 48개
  - 2,869개 실제 변환, 4,570편 영화 업데이트
  - cast_ko 한글화율: 98.7% → **100.00%** (42,759/42,759편)
  - 스크립트: `backend/scripts/transliterate_foreign_names.py`
- Zero-width space 정리 (22편), Unicode NFC 정규화, 깨진 데이터(태국어+데바나가리 혼합) 14편 제거

---

## [2026-02-12]

### Added
- **프로젝트 리뷰 문서**: `docs/PROJECT_REVIEW.md` 생성
  - 초기 기획(Phase 1-8) vs 현재 구현(Phase 17) 달성도 비교
  - 추천 알고리즘 진화 과정 (Phase 6 → 11 → 14)
  - 고도화 제안 로드맵 (단기/중기/장기/데이터 품질)
  - 기술 부채 정리
- **cast_ko 영어 배우 이름 한글 음역 변환**: Claude API로 33,442개 이름 번역
  - 1차: 2편 이상 등장 배우 9,714개 (49분, $3.33)
  - 2차: 1편 등장 배우 23,815개 ($8.36)
  - 총 API 비용: ~$11.69
  - 22,451편 영화의 cast_ko 업데이트 → **92.8% 완전 한글화**
  - 스크립트: `backend/scripts/transliterate_cast_names.py`
- **persons 테이블 부분 한글화**: 기존 번역 매핑 적용으로 31,672명 업데이트
  - 스크립트: `backend/scripts/transliterate_persons.py` (생성, 47,689명 잔여분은 미실행)

### Changed
- **DB 스키마 정리**: `overview_ko`, `overview_lang` 컬럼 제거 (24 → 22컬럼)
  - overview가 모든 영화에 대해 한글로 통일되어 있어 불필요한 컬럼 삭제
  - SQLAlchemy Movie 모델, Pydantic MovieDetail 스키마에서 필드 제거
  - 프론트엔드 `MovieDetail` 타입에서 `overview_ko`, `overview_lang` 제거
  - `movie.overview_ko || movie.overview` 로직 → `movie.overview`로 단순화
  - 스크립트(`llm_emotion_tags.py`, `regenerate_emotion_tags.py`) 참조 정리
  - LLM API(`llm.py`) overview 참조 단순화
- **출연진 표시 데이터 소스 변경**: `persons` 테이블(cast_members) → `movies.cast_ko` 컬럼 사용
  - persons 테이블: 80.9% 영어 → cast_ko: 92.8% 한글화 (품질 우위)
  - 영화 상세 페이지(`/movies/[id]`): cast_members 배열 → cast_ko.split(", ") 그리드 카드
  - 영화 모달(`MovieModal.tsx`): cast_members.map(p.name).join → cast_ko 직접 표시
  - TypeScript 타입: MovieDetail에 `cast_ko: string | null` 추가

### Fixed
- **프로덕션 CORS 500 에러**: DB에서 컬럼 삭제 후 이전 코드가 삭제된 컬럼 참조 → 500 에러 → CORS 헤더 누락으로 표면화. Railway 재배포로 코드-DB 일치시켜 해결
- **진행 파일 저장 실패 (Windows)**: 대용량 JSON 진행 파일 쓰기 시 `OSError: [Errno 22]` → 원자적 쓰기(tmp + rename) 패턴으로 해결

### Technical Details
- `backend/scripts/transliterate_cast_names.py` - Claude API 배치 음역 변환 (50개/배치, resume 지원)
- `backend/scripts/transliterate_persons.py` - persons 테이블 음역 변환 스크립트 (생성만)
- `backend/scripts/cast_transliteration_progress.json` - 33,442개 번역 매핑
- `backend/app/models/movie.py` - overview_ko, overview_lang Column 제거
- `backend/app/schemas/movie.py` - MovieDetail 필드 및 from_orm_with_relations 매핑 제거
- `frontend/types/index.ts` - MovieDetail에 cast_ko 추가, overview_ko/overview_lang 제거
- `frontend/app/movies/[id]/page.tsx` - cast_members → cast_ko, overview fallback 단순화
- `frontend/components/movie/MovieModal.tsx` - cast_members → cast_ko, overview 단순화
- 로컬 DB: `ALTER TABLE movies DROP COLUMN overview_ko, overview_lang`
- 프로덕션 DB: pg_dump → pg_restore (여러 차례 동기화)

---

## [2026-02-11]

### Security
- **DB 비밀번호 노출 대응**: GitGuardian 경고 → Railway PostgreSQL 신규 서비스로 교체
  - `.claude/settings.local.json` git 추적 제거 (노출된 비밀번호 포함)
  - `.gitignore`에 `.claude/settings.local.json`, `*.dump` 추가
  - 새 DB 호스트: `shinkansen.proxy.rlwy.net:20053`

### Added
- **인기도 로그 스케일 변환**: TMDB popularity를 10점 만점으로 변환 (log 기반 정규화)
  - 42,917편의 min(0.007)~max(728) 기준
  - 라벨: 8.0+ 초화제작 (~30편), 6.5+ 인기작 (~420편), 5.0+ 주목작 (~14,500편)
  - `getPopularityScore()` 유틸리티 함수 (`frontend/lib/utils.ts`)
- **무한스크롤 "더 보기" 버튼**: observer 미작동 시 수동 로드 fallback
  - 현재 페이지 / 전체 페이지 표시
- **Favicon 추가**: Pillow로 생성한 .ico (16x16/32x32) + SVG (빨간 배경 흰색 R 로고)
  - `public/favicon.ico`, `public/favicon.svg`
  - `layout.tsx` metadata icons 설정
- **헤더 로고 아이콘**: RecFlix 텍스트 좌측에 R 아이콘 추가 (아이콘 + "ecflix" 조합)
- **날씨 한글 도시명 표시**: OpenWeatherMap Reverse Geocoding API 병렬 호출
  - `local_names.ko`에서 한글 도시명 추출 (예: "수원시")
  - 70개+ 한글 도시명 매핑 딕셔너리 (fallback용)
  - 헤더 WeatherIndicator에 도시명 표시 (데스크톱만, 모바일 생략)

### Changed
- **높은 평점 정렬 기준 변경**: `vote_average` → `weighted_score` (투표수+평점 가중)
  - 홈 "높은 평점 영화" 섹션 + top-rated API + 검색 페이지 평점순 정렬
  - 홈 높은 평점 섹션에 `vote_count >= 100` 최소 조건 추가
- **검색 정렬 옵션 변경**: `vote_average` → `weighted_score` (백엔드 + 프론트엔드)
- **Vercel Image Optimization 비활성화**: `images.unoptimized: true`
  - Hobby 플랜 월 1,000회 제한 초과로 포스터 미표시 문제 해결
  - TMDB CDN에서 직접 로드 (성능 차이 미미)
- **제작 국가 한국어 표시**: `production_countries_ko` 우선 표시 (없으면 영어 fallback)
- **무한스크롤 훅 개선**: `enabled`를 콜백 ref dependency에서 제거, ref로 체크하도록 변경
- **OpenWeatherMap lang 파라미터**: `kr` → `ko` (표준 언어 코드)
- **FeaturedBanner 하단 여백 축소**: 배너 높이 5vh 감소, 마진 `mb-16/mb-20` → `mb-4/mb-6`
- **FeaturedBanner 제목 전체 표시**: `truncate` 제거, 긴 제목도 줄바꿈으로 전체 표시

### Fixed
- **Vercel 포스터 미표시**: Image Optimization 할당량 초과 (402 에러) → unoptimized 설정으로 해결
- **무한스크롤 미작동**: IntersectionObserver 콜백 ref 타이밍 이슈 수정 + 수동 버튼 fallback
- **날씨 도시명 "dong" 표시 문제**: 좌표 기반 조회 시 동(洞) 단위 영어 이름 반환 → 역지오코딩으로 한글 도시명 해결
- **날씨 캐시 무효화**: Redis 캐시 키 + localStorage 캐시 키 버전업으로 이전 데이터 완전 무효화

---

## [2026-02-10]

### Added
- **신규 CSV 데이터 마이그레이션**: 32,625편 → **42,917편** (+10,292편)
- **Movie 모델 6컬럼 추가**: `director`, `director_ko`, `cast_ko`, `production_countries_ko`, `release_season`, `weighted_score`
- **DB 마이그레이션 스크립트**: `backend/scripts/migrate_add_columns.py`
- **CSV 임포트 스크립트**: `backend/scripts/import_csv_data.py`, `import_relationships.py`, `import_production.py`
- **mbti/weather 점수 생성 스크립트**: `backend/scripts/generate_mbti_weather_scores.py`
  - MBTI 16개 유형별 장르+감정 기반 점수 산출
  - 날씨 4개 타입별 장르+감정 기반 점수 산출 (부스트/페널티 로직)
- **LLM emotion_tags 복원**: 백업 JSON에서 996편 복원
- **키워드 기반 emotion_tags**: 18,587편 신규 생성 (overview 컬럼 사용으로 변경)
- **프로덕션 DB 복원**: `pg_dump` → `pg_restore`로 Railway PostgreSQL에 전체 데이터 적용
- **LLM emotion_tags 재분석 (1,711편)**: 새 프롬프트 적용으로 세밀한 점수 분포 (0.35, 0.72 등)
  - 새 스크립트: `backend/scripts/llm_reanalyze_all.py` (배치별 즉시 저장 + resume 지원)
  - 새 스크립트: `backend/scripts/test_llm_prompt.py` (프롬프트 테스트)
- **연령등급 필터링**: `age_rating` 파라미터 (all/family/teen/adult)
  - `AGE_RATING_MAP`: family (ALL/G/PG/12), teen (+PG-13/15)
  - `apply_age_rating_filter()` 함수로 모든 추천/검색 API에 적용
  - NULL 등급(전체의 ~55.6%)은 모든 그룹에 포함
  - Frontend: MovieCard에 등급별 색상 배지, 검색 페이지에 등급 필터 드롭다운
- **Hybrid 점수 분석 스크립트**: `backend/scripts/analyze_hybrid_scores.py`
- **DB 덤프 공유**: `data/recflix_db.dump` (42,917편) + `data/DB_RESTORE_GUIDE.md`

### Changed
- **Vercel 프로젝트 이름 변경**: `frontend` → `jnsquery-reflix`
- **프로덕션 프론트엔드 URL**: `https://jnsquery-reflix.vercel.app`
- **Railway CORS_ORIGINS 업데이트**: 새 도메인 반영
- **로컬 `.env` CORS_ORIGINS**: 명시적으로 추가 및 동기화
- **README**: 프론트엔드 URL 업데이트
- **regenerate_emotion_tags.py**: `overview_ko` → `overview` 사용, LLM 식별을 기존 태그 존재 여부로 변경
- **Pydantic MovieDetail 스키마**: 신규 6개 필드 추가 및 `from_orm_with_relations` 매핑
- **.gitignore**: `*.csv` 패턴 추가 (대용량 CSV 제외)
- **품질 필터 통합**: `vote_count >= 30 AND vote_average >= 5.0` → `weighted_score >= 6.0`
  - 모든 추천 섹션에 통일 적용 (인기, 평점, MBTI, 날씨, 기분, Hybrid)
  - 2차 정렬에 `weighted_score DESC` 추가
- **Hybrid 가중치 v2 튜닝**:
  - Mood: 0.20 → **0.30** (기분 맞춤 추천 강화)
  - MBTI: 0.30 → **0.25** (과잉 지배 완화)
  - Personal: 0.30 → **0.25** (과잉 지배 완화)
- **품질 보정 방식 변경**: binary bonus(+0.1/+0.2) → 연속 보정(×0.85~1.0)
  - `weighted_score` 6.0~9.0 구간에서 0.85~1.0 연속 곱셈
- **#명작 태그 기준**: `weighted_score >= 7.0` → `>= 7.5`, personal_score 가산 제거 (태그만 표시)

### Data Statistics
- 영화: 42,917편
- emotion_tags: 42,917 (100%) — LLM 분석 ~1,711편, 키워드 기반 ~41,206편
- mbti_scores: 42,917 (100%)
- weather_scores: 42,917 (100%)
- 관계: movie_genres 98,767 / movie_cast 252,662 / movie_keywords 77,660 / movie_countries 55,265 / similar_movies 101,386

### Technical Details
- `backend/scripts/llm_reanalyze_all.py` - LLM 재분석 (배치 저장, resume 지원)
- `backend/scripts/analyze_hybrid_scores.py` - Hybrid 점수 분포 분석
- `backend/app/api/v1/recommendations.py` - 품질 필터, 가중치 튜닝, 연속 보정, 연령등급 필터
- `backend/app/api/v1/movies.py` - 영화 검색 연령등급 필터
- `frontend/components/movie/MovieCard.tsx` - 등급 배지 UI
- `frontend/app/movies/page.tsx` - 등급 필터 드롭다운

---

## [2026-02-09]

### Added
- **LLM 기반 emotion_tags 분석**: Claude API를 사용한 상위 1,000편 영화 감성 분석
  - 새 스크립트: `backend/scripts/llm_emotion_tags.py`
  - 모델: claude-sonnet-4-20250514
  - 10편씩 배치 처리로 API 비용 최적화
- **기분(Mood) 선택 UI**: 6가지 기분 2x3 그리드 배치
  - 😌 편안한, 😰 긴장감, 😆 신나는
  - 💕 감성적인, 🔮 상상에빠지고싶은, 😄 가볍게볼래
- **네거티브 키워드 & 장르 페널티 로직**: 클러스터와 반대되는 키워드/장르 감점
- **30% LLM 보장 혼합 정렬**: 추천 풀에서 최소 30% LLM 분석 영화 포함
- **품질 필터**: 모든 추천에 vote_count >= 30, vote_average >= 5.0 적용
- **🔄 새로고침 버튼**: 모든 영화 섹션 제목 우측에 추가
  - 클릭 시 풀(50개) 내에서 20개 재셔플 (API 호출 없음)
  - Fisher-Yates 알고리즘 사용
  - 회전 애니메이션 피드백

### Changed
- **맞춤 추천 영화 수 증가**: 10개 → 20개 (풀 40개에서 셔플)
- **섹션별 표시 영화 수**: 20개 표시, 50개 풀에서 셔플
- **emotion_tags 키워드 점수 상한**: 0.7로 제한 (LLM 영화와의 균형)
- **emotion_tags 7대 클러스터 재정의**: healing, tension, energy, romance, deep, fantasy, light
- **섹션 순서 로그인 상태별 분리**:
  - 로그인: 개인화 우선 (MBTI → 날씨 → 기분 → 인기 → 평점)
  - 비로그인: 범용 우선 (인기 → 평점 → 날씨 → 기분)
- **로그아웃 시 즉시 UI 갱신**: Zustand 스토어 초기화 + 추천 데이터 재요청
- **유도 섹션 UI 통일**: w-80 너비, 동일한 스타일 적용
- **감성적 이모지 변경**: 🥹 → 💕 (크로스 플랫폼 호환성)
- **장르 부스트 강화**: 0.1 → 0.15로 상향
- **light 클러스터 개선**: 부스트 장르에 "가족" 추가, 한국어 키워드 14개 추가
- **healing/deep 분리**: healing에서 "드라마" 제거, deep과 명확히 구분

### Technical Details
- `backend/scripts/llm_emotion_tags.py` - Claude API 기반 emotion_tags 생성
- `backend/scripts/regenerate_emotion_tags.py` - 키워드 기반 emotion_tags 생성 (0.7 상한)
- `backend/app/api/v1/recommendations.py` - 30% LLM 보장 혼합 정렬 구현
- `frontend/components/movie/FeaturedBanner.tsx` - 기분 선택 UI 개선
- `docs/RECOMMENDATION_LOGIC.md` - 추천 로직 상세 문서 업데이트

---

## [2026-02-04]

### Added
- **LLM 캐치프레이즈 기능**: Anthropic Claude API를 사용한 영화별 맞춤 캐치프레이즈 생성
  - 새 API 엔드포인트: `GET /api/v1/llm/catchphrase/{movie_id}`
  - Redis 캐싱 (24시간 TTL)
  - 영화 상세 페이지에 캐치프레이즈 표시
- **메인 배너 MBTI 유도 섹션**: 로그인/MBTI 설정 유도 메시지
- **내 리스트 버튼 기능**: 로그인 체크, 찜하기 토글 연동

### Changed
- **헤더 메뉴명**: "영화" → "영화 검색"
- **메인 배너 레이아웃**: 영화 정보 좌측 하단, MBTI 유도 우측 상단
- **배너 높이**: 70vh → 55vh/60vh/65vh (반응형)
- **영화 목록**: 10개 → 50개로 증가
- **영화 목록 다양성**: 상위 100개에서 랜덤 50개 선택 + 셔플
- **텍스트 정렬**: 섹션 타이틀 한 줄 배치, 영화 카드 중앙 정렬

### Fixed
- **Redis 프로덕션 연결**: `REDIS_URL` 환경변수 지원 (`aioredis.from_url()`)
- **무한스크롤 중단 버그**: callback ref 패턴으로 IntersectionObserver 재구현
- **콘솔 에러**:
  - `manifest.json` 404 → 파일 생성
  - `apple-mobile-web-app-capable` deprecated → `mobile-web-app-capable` 사용
  - `icon-192.png` 404 → icons 배열을 빈 배열로 설정

### Technical Details
- `backend/app/services/llm.py` - Claude API 호출 서비스
- `backend/app/api/v1/llm.py` - 캐치프레이즈 API 엔드포인트
- `backend/app/schemas/llm.py` - CatchphraseResponse 스키마
- `frontend/hooks/useInfiniteScroll.ts` - callback ref 패턴으로 전면 개선

---

## [2026-02-03]

### Added
- **프로덕션 배포**
  - Vercel (Frontend): https://jnsquery-reflix.vercel.app
  - Railway (Backend): https://backend-production-cff2.up.railway.app
  - Railway PostgreSQL + Redis
- GitHub 저장소: https://github.com/sky1522/recflix
- 데이터베이스 마이그레이션: 32,625편 영화

### Fixed
- CORS_ORIGINS 파싱: `field_validator`로 comma-separated 문자열 파싱
- DB 테이블 자동 생성: FastAPI `lifespan` 이벤트 사용
- Railway PORT 변수: `sh -c` 래퍼로 환경변수 확장

---

## [2026-02-02]

### Added
- Phase 1-8 기본 기능 구현 완료
- 하이브리드 추천 엔진 (MBTI 35% + 날씨 25% + 개인취향 40%)
- 반응형 모바일 최적화
- 검색 자동완성
- 무한 스크롤

---

## 개발 일지

자세한 개발 일지는 `docs/devlog/` 폴더에서 확인할 수 있습니다.

- [2026-02-04](docs/devlog/2026-02-04.md) - LLM 캐치프레이즈, 무한스크롤 수정, 배너 UI 개선
