# OAuth 콜백 온보딩 분기 수정

## 문제
카카오/Google OAuth 콜백에서 isNew만 보고 라우팅하여,
"기존 사용자이지만 온보딩 미완료" 상태일 때 홈으로 빠져나감

예: 카카오 가입 → 온보딩 건너뛰기(skip) → 다음 로그인 시 isNew=false → 홈 이동
    → onboarding_completed=false인데 온보딩을 다시 볼 기회 없음

## 수정 대상

### 1. frontend/app/auth/kakao/callback/page.tsx:32-33
현재:
  const isNew = socialLogin(response)
  router.replace(isNew ? "/onboarding" : "/")

수정:
  socialLogin(response)
  const user = useAuthStore.getState().user
  const needsOnboarding = !user?.onboarding_completed
  router.replace(needsOnboarding ? "/onboarding" : "/")

### 2. frontend/app/auth/google/callback/page.tsx:32-33
동일한 패턴으로 수정

### 3. 참고: 이메일 signup은 이미 수정 완료
frontend/app/signup/page.tsx:55-57이 onboarding_completed 기준으로 분기하도록 이전 커밋에서 수정됨

## 검증
- 카카오 신규 가입 → 온보딩 진입
- 카카오 기존 사용자(온보딩 완료) → 홈 이동
- 카카오 기존 사용자(온보딩 미완료) → 온보딩 진입
- Google도 동일하게 3가지 시나리오 확인
- 이메일 가입 흐름은 기존대로 동작 (회귀 테스트)

## 완료 후
- 커밋: "fix: use onboarding_completed instead of isNew for OAuth routing"
- push 및 Vercel 배포 확인
- 결과를 claude_results.md에 기록