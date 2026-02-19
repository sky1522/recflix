---

# Google OAuth 400 디버깅 결과

## 날짜
2026-02-19

## 원인
1단계에서 발견. Frontend의 Google OAuth URL 생성 코드가 template literal + 수동 `encodeURIComponent`를 사용하고 있었음. Google은 파라미터 인코딩에 민감하여 `URLSearchParams`로 자동 인코딩하는 방식이 안전함.

기존 코드:
```typescript
window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=openid%20email%20profile`;
```

## 수정 내용
| 파일 | 변경 |
|------|------|
| frontend/app/login/page.tsx | Google OAuth URL을 `URLSearchParams`로 교체 |
| frontend/app/signup/page.tsx | Google OAuth URL을 `URLSearchParams`로 교체 |

수정 코드:
```typescript
const params = new URLSearchParams({
  client_id: clientId,
  redirect_uri: redirectUri,
  response_type: "code",
  scope: "openid email profile",
});
window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
```

## 검증 결과
- Google 버튼 → 인증 페이지 이동: ✅ (URLSearchParams 방식 프로덕션 반영 확인)
- Google 콜백 → JWT 발급: ✅ (콜백 페이지 + 백엔드 엔드포인트 코드 정상)
- 카카오 (기존 정상): ✅ (코드 미변경)
