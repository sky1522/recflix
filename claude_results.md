# Phase 48A: async 블로킹 I/O 수정

**날짜**: 2026-02-24

## 변경/생성 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/core/http_client.py` | httpx.AsyncClient 싱글턴 (신규) |
| `backend/app/api/v1/auth.py` | bcrypt to_thread + httpx AsyncClient 전환 |
| `backend/app/main.py` | lifespan에 http_client 초기화/정리 추가 |

## 1단계: bcrypt to_thread 적용 지점

| 함수 | 변경 |
|------|------|
| `signup` | `def` → `async def`, `get_password_hash()` → `await asyncio.to_thread(get_password_hash, ...)` |
| `login` | `verify_password()` → `await asyncio.to_thread(verify_password, ...)` |
| `kakao_login` | 신규 유저 생성 시 `get_password_hash()` → `await asyncio.to_thread(...)` |
| `google_login` | 신규 유저 생성 시 `get_password_hash()` → `await asyncio.to_thread(...)` |

## 2단계: httpx 변경 전/후

**Before** (매 요청마다 동기 클라이언트 생성):
```python
with httpx.Client(timeout=10.0) as client:
    token_resp = client.post(...)
```

**After** (싱글턴 AsyncClient 재사용):
```python
client = get_http_client()
token_resp = await client.post(...)
```

적용 위치: Kakao OAuth (token + userinfo), Google OAuth (token + userinfo) — 총 4곳

## http_client.py 구조

- `init_http_client()`: AsyncClient 생성 (lifespan startup)
- `close_http_client()`: AsyncClient 종료 (lifespan shutdown)
- `get_http_client()`: 싱글턴 반환

## lifespan 변경

```python
# startup
await init_http_client()

# shutdown
await close_http_client()
```

## 검증 결과

| 항목 | 결과 |
|------|------|
| `ruff check app/` | 0 issues |
| `from app.main import app` | 정상 import |
| `asyncio.to_thread` roundtrip | hash→verify True, wrong→False |
