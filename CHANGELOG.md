# Changelog

All notable changes to RecFlix will be documented in this file.

## [Unreleased]

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
