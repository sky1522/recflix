# 코드 품질 원칙

## Karpathy 4원칙
1. **한 번에 하나만**: 각 함수/컴포넌트는 한 가지 역할만 수행
2. **작게 유지**: 파일 500줄 이하, 함수 50줄 이하
3. **명확한 이름**: 함수/변수명으로 역할이 드러나야 (약어 지양)
4. **부작용 최소화**: 순수 함수 선호, 상태 변경은 명시적으로

## 파일 크기 관리
- 500줄 이상: 분리 필수
- 300~499줄: 분리 검토
- 300줄 미만: 양호

### 분리 기준
- 역할별: 상수/유틸/컴포넌트/로직
- 도메인별: 추천/날씨/인증/영화
- 레이어별: UI/비즈니스 로직/데이터

### 현재 500줄+ 파일 (리팩토링 대상)
- `backend/app/api/v1/recommendations.py` (770줄)
  - calculate_hybrid_scores() 133줄 → 스코어별 함수 분리
  - 가중치 상수, 태그 로직, 개인화 로직 분리 검토
- `frontend/app/movies/[id]/page.tsx` (622줄)
  - 히어로 배너, 상세 정보, 출연진, 유사 영화 → 서브 컴포넌트 분리 검토
- `backend/scripts/transliterate_foreign_names.py` (520줄)
  - 일회성 스크립트, 우선순위 낮음

### 현재 300~499줄 파일 (분리 검토 대상)
- `frontend/app/movies/page.tsx` (436줄) — 검색 필터/정렬/무한스크롤
- `backend/app/services/weather.py` (420줄) — API 호출 + 역지오코딩 + 70개 도시명
- `frontend/lib/curationMessages.ts` (415줄) — 258개 문구 데이터 (상수 파일, 분리 불필요)
- `frontend/app/ratings/page.tsx` (413줄) — 평점 목록 페이지
- `frontend/components/movie/FeaturedBanner.tsx` (407줄) — 배너 컴포넌트
- `frontend/components/layout/Header.tsx` (373줄) — 네비게이션 + 모바일 메뉴
- `frontend/components/search/SearchAutocomplete.tsx` (359줄) — 자동완성 검색

## 중복 제거
- 두 파일에서 같은 로직 발견 시 → 공통 유틸로 추출
- 매직넘버 → constants.ts 또는 Python 상수 모듈
- 캐시 키 → 중앙 관리 (frontend/lib/constants.ts)

## 함수 작성 규칙
- 함수 50줄 이하 (넘으면 헬퍼 분리)
- 인자 4개 이하 (넘으면 객체/DTO로 묶기)
- 중첩 3단계 이하 (넘으면 early return)
- 주석 대신 함수명으로 의도 표현

## 리팩토링 프로세스
1. Research: `find + wc -l` 로 500줄+ 파일 식별, 중복 검사
2. 우선순위: 저위험(유틸 추출) → 중위험(모듈 분리) → 고위험(구조 통합)
3. 실행: 기능 변경 없음 (순수 리팩토링), 각 단계 빌드 확인, 한 번에 한 파일

## Python 고유
- logging 사용 (print 금지) → Ruff T201 규칙
- ruff check + ruff format 통과
- 타입 힌트 필수 (함수 인자, 반환값)
- selectinload로 N+1 방지

## TypeScript 고유
- any 타입 사용 금지 → 구체적 타입 또는 unknown
- 모듈 레벨 mutable 변수 금지 → useRef/useState
- ESLint core-web-vitals 통과
- 상수는 constants.ts에서 import
