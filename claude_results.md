# Phase 46B: 보안 강화 + GDPR 계정 삭제

**날짜**: 2026-02-23

## 1단계: TRUSTED_PROXIES 기본값 수정

### 변경 파일
- `backend/app/core/rate_limit.py`

### 변경 전/후
| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| TRUSTED_PROXIES 미설정 시 | X-Forwarded-For 무조건 신뢰 (`return True`) | X-Forwarded-For 무시 (`return False`) |
| 동작 | 공격자가 XFF 헤더로 IP 위조 가능 | `request.client.host`만 사용 |
| 시작 시 로그 | 없음 | WARNING 레벨 경고 출력 |
| TRUSTED_PROXIES 설정 시 | 기존 CIDR 매칭 로직 | 변경 없음 |

## 2단계: OAuth state 검증 (CSRF 방지)

### 변경 파일
- `backend/app/api/v1/auth.py` — authorize URL 생성 + state 검증
- `backend/app/schemas/user.py` — SocialLoginRequest에 `state` 필드 추가
- `frontend/lib/api.ts` — `getOAuthAuthorizeUrl()` 함수 추가
- `frontend/app/login/page.tsx` — 백엔드 authorize URL 사용
- `frontend/app/signup/page.tsx` — 백엔드 authorize URL 사용
- `frontend/app/auth/kakao/callback/page.tsx` — state 전달
- `frontend/app/auth/google/callback/page.tsx` — state 전달

### OAuth state 흐름
```
1. [Frontend] 카카오/Google 버튼 클릭
2. [Frontend] GET /auth/{provider}/authorize 호출
3. [Backend] state = secrets.token_urlsafe(32) 생성
4. [Backend] Redis: oauth_state:{state} → TTL 600초 저장
5. [Backend] authorize URL에 state 포함하여 반환
6. [Frontend] window.location.href = authorize URL
7. [OAuth Provider] 사용자 인증 후 콜백으로 리디렉트 (code + state 포함)
8. [Frontend Callback] code + state 추출
9. [Frontend] POST /auth/{provider} { code, state } 전송
10. [Backend] Redis에서 oauth_state:{state} 확인
11. [Backend] 존재 → 삭제 후 진행 / 불일치 → 400 반환
```

### Redis 미연결 시 동작
- state 생성 실패: authorize URL에 state 미포함 (하위 호환)
- state 검증 시 Redis 미연결: 검증 스킵 + WARNING 로그 (서비스 가용성 우선)
- state 미전송: 검증 스킵 (하위 호환)

## 3단계: GDPR 계정 삭제

### 변경 파일
- `backend/app/api/v1/users.py` — `DELETE /users/me` 엔드포인트 추가
- `frontend/lib/api.ts` — `deleteAccount()` 함수 추가

### Cascade 삭제 순서 (실제 테이블 기준)
| 순서 | 테이블 | FK 설정 | 삭제 방식 |
|------|--------|---------|-----------|
| 1 | user_events | `ondelete='SET NULL'` | 명시적 DELETE (GDPR 완전 삭제) |
| 2 | ratings | `ondelete='CASCADE'` | User 삭제 시 자동 cascade |
| 3 | collections | `ondelete='CASCADE'` | User 삭제 시 자동 cascade |
| 3-1 | collection_movies | `ondelete='CASCADE'` (collection_id FK) | Collection 삭제 시 자동 cascade |
| 4 | users | - | `db.delete(user)` |

### Redis 정리 대상 키
| 키 패턴 | 설명 |
|---------|------|
| `refresh_token:{user_id}` | 활성 refresh token jti (revoke_refresh_token 호출) |

### 응답
- 성공: `204 No Content`
- 실패: `500 Internal Server Error` + 로깅 (트랜잭션 롤백)
- Rate limit: `3/minute`

## 검증 결과
| 검증 항목 | 결과 |
|-----------|------|
| `ruff check app/` | All checks passed! |
| `python -c "from app.main import app"` | OK (RecFlix) |
| `npx tsc --noEmit` | 0 errors |
| `npm run build` | 13/13 pages |
| `npm run lint` | 0 warnings/errors (via build) |
