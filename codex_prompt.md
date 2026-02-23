codex --reasoning high "RecFlix 프로젝트 전체 코드 점검 및 최적화 포인트 분석.

=== 점검 범위 ===

1. Frontend 성능
   - app/ 내 모든 page.tsx: 불필요한 'use client' 남용 여부, SSR/SSG 활용 가능한 페이지
   - components/ 전체: 불필요한 리렌더링, memo/useMemo/useCallback 누락
   - lib/api.ts: 에러 핸들링 일관성, 타임아웃 설정, 중복 요청 방지
   - next.config.js: 이미지 최적화, 번들 분석 설정
   - 번들 사이즈: 큰 라이브러리 import 방식 (tree-shaking 가능 여부)
   - Framer Motion 사용 패턴: 불필요한 애니메이션이 성능 저하 유발하는지

2. Backend 성능
   - recommendations.py + recommendation_engine.py: N+1 쿼리, 불필요한 DB 호출
   - movies.py: 검색 쿼리 최적화, 인덱스 활용 여부
   - semantic_search.py: 임베딩 로드/검색 병목
   - Redis 캐시 활용: 캐시 미스 시 성능, 캐시 키 설계
   - SQLAlchemy 쿼리 패턴: eager/lazy loading, joinedload 활용
   - 각 엔드포인트의 DB 쿼리 횟수 추정

3. 코드 품질
   - 파일별 LOC 확인: 500줄 초과 파일 식별
   - 함수별 LOC: 50줄 초과 함수 식별
   - 중복 코드: 백엔드/프론트엔드 내 유사 패턴 반복
   - 타입 안전성: any 사용, 타입 힌트 누락
   - 에러 핸들링: bare except, 무시된 에러
   - 미사용 코드: import되지만 사용 안 되는 모듈/함수

4. 보안
   - CORS 설정 적절성
   - Rate limiting 커버리지 (보호 안 된 엔드포인트)
   - SQL injection 가능성 (raw SQL 사용처)
   - JWT 설정 (만료 시간, 리프레시 토큰 로직)

5. UX/접근성
   - 로딩 상태 처리: 스켈레톤/스피너 누락된 곳
   - 에러 상태 UI: API 실패 시 사용자에게 보이는 것
   - 모바일 반응형: 깨지는 레이아웃
   - SEO: 메타태그 누락 페이지

=== 출력 형식 ===
우선순위별로 정리 (Critical / Important / Nice-to-have):

각 항목마다:
- 파일 경로
- 현재 문제
- 개선 방안
- 예상 효과 (성능 수치 or 코드 품질 개선도)

마지막에 리팩토링 Phase 순서 제안 (묶어서 작업하기 좋은 단위로).

결과를 codex_results.md에 기존 내용을 전부 지우고 새로 작성 (덮어쓰기)."