# Changelog

All notable changes to RecFlix will be documented in this file.

## [Unreleased]

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
  - Vercel (Frontend): https://frontend-eight-gules-78.vercel.app
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
