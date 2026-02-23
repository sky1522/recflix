# Phase 41: 안전/정확성 리팩토링 — 결과

## 날짜
2026-02-23

## 변경 파일 목록

| # | 파일 | 주요 변경 |
|---|------|----------|
| 1 | `backend/app/api/v1/movies.py` | 장르 필터 distinct 서브쿼리로 중복 제거 |
| 2 | `backend/app/core/security.py` | refresh 토큰 jti 생성 + Redis 기반 회전/검증 함수 |
| 3 | `backend/app/api/v1/auth.py` | refresh 회전 적용 (login/refresh/social 전 엔드포인트) |
| 4 | `backend/app/core/rate_limit.py` | 프록시 인식 key 함수 (CF-Connecting-IP > XFF > remote) |
| 5 | `backend/app/config.py` | TRUSTED_PROXIES 설정 추가 |

## 1단계: /movies 장르 필터 distinct 수정

**문제**: `JOIN(Movie.genres)` 후 `q.count()`/`q.all()` → 다대다 중복 카운트/데이터 발생

**해결**: 장르 필터를 서브쿼리 2-step으로 분리
```python
# Before: q = q.join(Movie.genres).filter(Genre.name.in_(genre_list))
# After:
genre_movie_ids = (
    db.query(Movie.id).join(Movie.genres)
    .filter(Genre.name.in_(genre_list)).distinct().subquery()
)
q = q.filter(Movie.id.in_(select(genre_movie_ids)))
```

**테스트 결과**:
- `genres=액션&page_size=5` → total=8389, items=5, unique=5, dup=0
- `genres=액션,모험&page_size=5` → total=10674, items=5, unique=5, dup=0

## 2단계: Refresh 토큰 회전(Rotate) 구현

**문제**: refresh 토큰 서명/만료만 검증, 탈취 토큰 재사용 방어 없음

**해결**:
- `security.py`: refresh 토큰에 `jti` (uuid4) 부여
- `security.py`: `store_refresh_jti()` — Redis에 활성 jti 저장 (TTL = refresh 만료시간)
- `security.py`: `validate_and_rotate_refresh()` — jti 일치 검증 + 즉시 삭제 + 탈취 감지
- `auth.py`: login/refresh/kakao/google 전 엔드포인트에서 jti 저장/검증
- Redis 미연결 시 graceful fallback (기존 방식 유지)

**보안 흐름**:
1. 로그인 → jti=A 생성, Redis에 저장
2. refresh(jti=A) → 일치 확인, jti=A 삭제, jti=B 생성/저장
3. 재사용(jti=A) → jti=B와 불일치 → 401 "Token reuse detected" + 모든 토큰 무효화

**테스트 결과**:
- 로그인 → refresh → 새 토큰 발급: OK (200)
- 같은 refresh 토큰 재사용 → 401 "Token reuse detected. Please login again.": OK

## 3단계: Rate limit 프록시 인식

**문제**: `get_remote_address` 단일 IP → 리버스 프록시 뒤에서 모든 사용자가 같은 IP

**해결**: `get_rate_limit_key()` 커스텀 함수
- 우선순위: CF-Connecting-IP > X-Forwarded-For (첫 번째 IP) > remote address
- `TRUSTED_PROXIES` 설정: CIDR/IP 리스트로 신뢰 프록시 지정 (빈 리스트 = 모든 프록시 신뢰)
- `ipaddress` 모듈로 CIDR 네트워크 매칭 지원

## 검증 결과
- `ruff check` (E,F,W,I): 수정 파일 기준 0 errors
- `ast.parse()`: 구문 오류 없음
- `npm run build`: 성공 (프론트엔드 변경 없음)
- 장르 필터 테스트: 단일/다중 장르 모두 정확
- 토큰 회전 테스트: 재사용 시 401 정상 차단
