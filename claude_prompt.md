claude "Phase 48A: async 블로킹 I/O 수정.

=== Research ===
다음 파일들을 읽을 것:
- backend/app/api/v1/auth.py (전체 — bcrypt 호출 지점, httpx.Client 사용 지점)
- backend/app/core/security.py (verify_password, get_password_hash)
- backend/app/core/deps.py (get_current_user)
- backend/app/main.py (lifespan)

=== 1단계: bcrypt 블로킹 해소 ===

1-1. backend/app/core/security.py:
  - verify_password()를 async로 변경하지 말 것 (동기 유틸 유지)
  
1-2. backend/app/api/v1/auth.py의 bcrypt 호출 지점:
  - login 엔드포인트에서 verify_password() 호출 부분
  - signup 엔드포인트에서 get_password_hash() 호출 부분
  - 각각 asyncio.to_thread()로 래핑:
    is_valid = await asyncio.to_thread(verify_password, password, user.hashed_password)
    hashed = await asyncio.to_thread(get_password_hash, password)
  
⚠️ asyncio.to_thread는 Python 3.9+ (프로젝트 호환성 확인)

=== 2단계: httpx.AsyncClient 싱글턴 ===

2-1. backend/app/core/http_client.py 생성 (신규):
  - 모듈 레벨 AsyncClient 싱글턴
  - lifespan에서 초기화/정리:
    startup: http_client = httpx.AsyncClient(timeout=10.0)
    shutdown: await http_client.aclose()
  - get_http_client() 함수 export

2-2. backend/app/api/v1/auth.py의 OAuth 부분:
  - 현재: httpx.Client()를 매 요청마다 with 블록으로 생성
  - 변경: get_http_client()로 싱글턴 사용, await client.post(...) / await client.get(...)
  - Kakao, Google 양쪽 모두 적용

2-3. backend/app/main.py lifespan:
  - startup에 http_client 초기화 추가
  - shutdown에 http_client.aclose() 추가

⚠️ httpx.AsyncClient는 자동으로 커넥션 풀 관리
⚠️ 기존 동기 httpx.Client 호출을 async로 전환하면서 응답 처리 로직은 동일하게 유지

=== 규칙 ===
- verify_password, get_password_hash 함수 시그니처는 동기 유지 (호출부에서 to_thread)
- OAuth 토큰 교환/프로필 조회 로직 자체는 변경 금지 (HTTP 클라이언트만 교체)
- 에러 핸들링 기존 패턴 유지

=== 검증 ===
1. cd backend && ruff check app/ → 0 issues
2. cd backend && python -c 'from app.main import app; print(app.title)'
3. cd backend && python -c 'import asyncio; from app.core.security import verify_password; print(asyncio.run(asyncio.to_thread(verify_password, \"test\", \"$2b$12$test\")))'
4. git add -A && git commit -m 'perf: Phase 48A bcrypt to_thread + httpx AsyncClient 싱글턴' && git push origin HEAD:main

결과를 claude_results.md에 덮어쓰기:
- bcrypt to_thread 적용 지점 목록
- httpx 변경 전/후 (Client → AsyncClient)
- lifespan 변경 내용
- http_client.py 구조"