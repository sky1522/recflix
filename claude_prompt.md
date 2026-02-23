claude "Phase 41: 안전/정확성 리팩토링 — Critical 이슈 수정.

=== Research ===
먼저 codex_results.md를 읽고 Critical 항목을 확인할 것.
그리고 다음 파일들을 읽을 것:
- backend/app/api/v1/movies.py (장르 필터 쿼리: 162, 184, 194번 라인 근처)
- backend/app/core/security.py (refresh 토큰: 49, 64번 라인)
- backend/app/api/v1/auth.py (refresh 엔드포인트: 96~100번 라인)
- backend/app/core/rate_limit.py (rate limit key 함수)
- backend/app/core/config.py (Redis 설정)

=== 1단계: /movies 장르 필터 distinct 수정 ===
movies.py에서 장르 필터 적용 시:
- JOIN 후 count 쿼리: count(distinct(Movie.id))로 변경
- 페이지 데이터 쿼리: distinct(Movie.id) 적용 또는 서브쿼리 2-step 분리
- 기존 정렬/페이지네이션 로직 유지
⚠️ 장르 필터 미사용 시 기존 동작 변경 금지

=== 2단계: Refresh 토큰 회전(Rotate) 구현 ===
security.py + auth.py:
- refresh 토큰 생성 시 jti(JWT ID) 부여 (uuid4)
- Redis에 활성 refresh 토큰 jti 저장 (키: refresh_token:{user_id}, 값: jti, TTL: refresh 만료시간)
- /auth/refresh 호출 시:
  1. jti 검증 (Redis에 저장된 값과 일치하는지)
  2. 새 access + refresh 토큰 발급
  3. 이전 jti 즉시 삭제, 새 jti 저장
  4. 불일치 시 401 + 해당 user의 모든 refresh 토큰 무효화 (탈취 의심)
- Redis 미연결 시 기존 방식으로 graceful fallback (서비스 중단 방지)

=== 3단계: Rate limit 프록시 인식 ===
rate_limit.py:
- key 함수를 커스텀으로 변경:
  1. X-Forwarded-For 헤더에서 첫 번째 IP 추출 (신뢰 체인)
  2. CF-Connecting-IP 헤더 우선 (Cloudflare 사용 시)
  3. 인증 사용자면 user_id 기반 키 병행
  4. 헤더 없으면 기존 get_remote_address fallback
- 설정에 TRUSTED_PROXIES 리스트 추가 (config.py)

=== 규칙 ===
- 추천 로직(recommendations.py, recommendation_engine.py) 수정 금지
- 기존 API 응답 형식 변경 금지
- Redis 의존 기능은 반드시 fallback 포함
- 함수 50줄 이내, 파일 500줄 이내 유지

=== 검증 ===
1. cd backend && ruff check app/api/v1/movies.py app/core/security.py app/core/rate_limit.py app/api/v1/auth.py
2. 장르 필터 테스트:
   curl 'http://localhost:8000/api/v1/movies?genres=28&page_size=5' → total 정확, 중복 없음
   curl 'http://localhost:8000/api/v1/movies?genres=28,12&page_size=5' → 다중 장르도 정확
3. Refresh 토큰 테스트:
   - 로그인 → refresh → 새 토큰 발급 확인
   - 같은 refresh 토큰 재사용 → 401
4. Rate limit: X-Forwarded-For 헤더 포함 요청이 정상 처리되는지
5. cd frontend && npm run build
6. git add -A && git commit -m 'fix: Phase 41 안전/정확성 (distinct 쿼리, 토큰 회전, rate limit)' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기."