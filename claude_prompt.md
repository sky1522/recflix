# 소셜 로그인 키 불일치 수정 + Google 400 해결

## 현재 문제

### 카카오 KOE006
Frontend 빌드에 Default REST API 키(0662...)가 들어있고, Redirect URI도 등록됨.
하지만 Backend(Railway)에는 RecFlix 키(f5ba...)와 RecFlix 시크릿(xKK3...)이 등록됨.
→ Frontend가 0662 키로 인가코드를 받아오면, Backend가 f5ba 키로 토큰 교환 시도 → 실패.
→ 또한 카카오는 REST API 키마다 클라이언트 시크릿이 기본 활성화됨. 키와 시크릿이 짝이 맞아야 함.

### Google 400 invalid_request
정확한 원인 미상. URL 생성 로직 또는 파라미터 문제 가능성.

---

먼저 읽을 것:
- CLAUDE.md
- frontend/app/login/page.tsx
- frontend/app/signup/page.tsx
- frontend/app/auth/kakao/callback/page.tsx
- frontend/app/auth/google/callback/page.tsx
- frontend/stores/authStore.ts
- frontend/lib/api.ts
- backend/app/api/v1/auth.py
- backend/app/config.py

---

=== 1단계: Frontend/Backend 환경변수 키 값 대조 ===

```bash
echo "=== Frontend .env.local ==="
cat frontend/.env.local 2>/dev/null || echo "없음"

echo ""
echo "=== Backend .env ==="
cat backend/.env 2>/dev/null | grep -i "KAKAO\|GOOGLE" || echo "없음"

echo ""
echo "=== Backend config.py 기본값 ==="
grep -A1 "KAKAO\|GOOGLE" backend/app/config.py
```

**핵심 체크:** Frontend의 NEXT_PUBLIC_KAKAO_CLIENT_ID와 Backend의 KAKAO_CLIENT_ID가 **동일한 값**인지 확인.
→ 다르면 이게 원인. 반드시 동일한 REST API 키를 사용해야 함.

⚠️ 카카오는 REST API 키마다 독립적인 클라이언트 시크릿이 있음.
→ KAKAO_CLIENT_ID = 특정 REST API 키 → KAKAO_CLIENT_SECRET = 그 키의 시크릿
→ 짝이 안 맞으면 토큰 교환 실패.

---

=== 2단계: 키 통일 방안 결정 ===

현재 빌드에 0662 키가 들어있으므로, **모든 곳을 0662 키로 통일**하는 것이 가장 빠름.

하지만 Vercel/Railway 환경변수는 코드에서 변경 불가.
→ 코드 수정이 아니라 **환경변수 통일이 필요한 상황**임을 인지.

**코드에서 할 수 있는 것:**
- Frontend .env.local의 NEXT_PUBLIC_KAKAO_CLIENT_ID 값 확인 및 기록
- Backend .env의 KAKAO_CLIENT_ID, KAKAO_CLIENT_SECRET 값 확인 및 기록
- 불일치 시 어떤 값으로 통일해야 하는지 결과에 명시

---

=== 3단계: OAuth URL 생성 로직 안전하게 교체 ===

수동 문자열 조립 대신 URLSearchParams 사용으로 교체. 인코딩 실수 원천 차단.

**frontend/app/login/page.tsx의 카카오 버튼:**
```typescript
onClick={() => {
  const clientId = process.env.NEXT_PUBLIC_KAKAO_CLIENT_ID;
  const redirectUri = process.env.NEXT_PUBLIC_KAKAO_REDIRECT_URI;
  if (!clientId || !redirectUri) {
    alert("카카오 로그인 설정이 필요합니다.");
    return;
  }
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
  });
  window.location.href = `https://kauth.kakao.com/oauth/authorize?${params.toString()}`;
}}
```

**Google 버튼:**
```typescript
onClick={() => {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  const redirectUri = process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI;
  if (!clientId || !redirectUri) {
    alert("Google 로그인 설정이 필요합니다.");
    return;
  }
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: "code",
    scope: "openid email profile",
  });
  window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
}}
```

**signup/page.tsx에도 동일한 소셜 버튼이 있으면 같이 수정.**

---

=== 4단계: Backend 토큰 교환 로직 검증 ===

```bash
# auth.py에서 카카오 토큰 교환 코드 확인
grep -B5 -A30 "kauth.kakao.com/oauth/token\|oauth/token" backend/app/api/v1/auth.py

# Google 토큰 교환 코드 확인
grep -B5 -A30 "oauth2.googleapis.com/token\|googleapis.*token" backend/app/api/v1/auth.py
```

**카카오 토큰 교환 시 필수 파라미터 (REST API 문서 기준):**
```python
{
    "grant_type": "authorization_code",
    "client_id": "REST_API_키",          # Frontend와 동일한 키!
    "client_secret": "해당_키의_시크릿",   # 이 키의 시크릿!
    "redirect_uri": "등록된_리다이렉트_URI", # Frontend와 동일!
    "code": "인가코드"
}
```

⚠️ client_id, client_secret, redirect_uri 3개가 모두 같은 REST API 키 기준이어야 함.
⚠️ redirect_uri는 인가 요청 시 사용한 것과 정확히 동일해야 함.

**Google 토큰 교환 시 필수 파라미터:**
```python
{
    "grant_type": "authorization_code",
    "client_id": "전체_클라이언트_ID.apps.googleusercontent.com",
    "client_secret": "클라이언트_보안_비밀번호",
    "redirect_uri": "등록된_리다이렉트_URI",
    "code": "인가코드"
}
```

---

=== 5단계: .env.local 환경변수 값 숨겨진 문자 검사 ===

```bash
# hex로 출력해서 공백, 줄바꿈, 캐리지리턴 확인
if [ -f frontend/.env.local ]; then
  echo "=== KAKAO_CLIENT_ID ==="
  grep "NEXT_PUBLIC_KAKAO_CLIENT_ID" frontend/.env.local | xxd | head -5
  echo ""
  echo "=== KAKAO_REDIRECT_URI ==="
  grep "NEXT_PUBLIC_KAKAO_REDIRECT_URI" frontend/.env.local | xxd | head -5
  echo ""
  echo "=== GOOGLE_CLIENT_ID ==="
  grep "NEXT_PUBLIC_GOOGLE_CLIENT_ID" frontend/.env.local | xxd | head -5
  echo ""
  echo "=== GOOGLE_REDIRECT_URI ==="
  grep "NEXT_PUBLIC_GOOGLE_REDIRECT_URI" frontend/.env.local | xxd | head -5
fi
```

→ 값 끝에 `0d`(캐리지리턴), `20`(공백) 있으면 문제. .env.local 다시 작성.

---

=== 6단계: 콜백 페이지 검증 ===

```bash
cat frontend/app/auth/kakao/callback/page.tsx
cat frontend/app/auth/google/callback/page.tsx
```

체크:
- useSearchParams()로 `code` 파라미터 추출하는지
- code를 Backend API에 POST 전송하는지
- 에러 발생 시 사용자에게 표시하는지 (silent fail 아닌지)

---

=== 7단계: 빌드 + 테스트 ===

```bash
cd frontend && npm run build
```

빌드 후 환경변수가 번들에 포함됐는지 확인:
```bash
grep -r "kauth.kakao.com" frontend/.next/static/ 2>/dev/null | head -2
grep -r "accounts.google.com" frontend/.next/static/ 2>/dev/null | head -2
```

---

=== 건드리지 말 것 ===
- recommendation 관련 코드 전체
- 이벤트 시스템
- 기존 이메일 로그인 로직 (추가만, 기존 변경 금지)
- 모든 .md 문서 파일

---

결과를 claude_results.md에 **기존 내용을 전부 지우고 새로 작성** (덮어쓰기):

```markdown
# 소셜 로그인 키 불일치 수정 결과

## 날짜
YYYY-MM-DD

## 1단계: 환경변수 대조 결과
| 위치 | KAKAO_CLIENT_ID | KAKAO_CLIENT_SECRET | 일치 |
|------|----------------|--------------------|----|
| Frontend .env.local | (값) | - | |
| Backend .env | (값) | (값) | |
| Vercel | (값) | - | |
| Railway | (값) | (값) | |

## 2단계: 키 통일 필요 여부
(일치/불일치 — 불일치면 어떤 값으로 통일해야 하는지)

## 3단계: URL 생성 로직 수정
| 파일 | 변경 |
|------|------|
| (파일) | (변경) |

## 4단계: Backend 토큰 교환 검증
- client_id 일치: ✅/❌
- client_secret 짝 맞음: ✅/❌
- redirect_uri 일치: ✅/❌

## 5단계: .env.local 숨겨진 문자
(발견 여부)

## 수동 조치 필요 사항
(Vercel/Railway 환경변수 변경이 필요하면 여기에 명시)
```

⚠️ 환경변수 변경이 필요한 경우 커밋하지 말고 결과만 저장. 환경변수 수정 후 재배포 필요.
⚠️ 코드 수정만 있는 경우:
git add -A && git commit -m 'fix: 소셜 로그인 OAuth URL 안전하게 교체 (URLSearchParams) + 키 통일' && git push origin HEAD:main