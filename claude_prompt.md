# 시연 차단 버그 3건 일괄 수정

시연 발표가 내일입니다. 아래 3개 이슈가 시연을 차단합니다. 우선순위 순서대로 수정해주세요.

---

## 이슈 1: 날씨 드롭다운 변경 시 홈 추천 + 모바일 드로어 동기화 (❌ 차단)

### 현재 상태
- useWeather.ts에 CustomEvent(manual_weather_change, weather_reset)를 추가했으나
- HeaderMobileDrawer.tsx가 별도 useWeather() 인스턴스를 사용하고 있어
  모바일에서 날씨 변경 시 홈 추천이 갱신되지 않음
- 또한 body weather theme(body의 data-weather 속성 등)도 동기화 안 됨

### 수정 사항
1. HeaderMobileDrawer.tsx에서도 날씨 변경 시 동일한 CustomEvent를 dispatch하도록 수정
   - Header.tsx의 handleWeatherChange 패턴을 참고
2. 홈 page.tsx의 useEffect dependency에 weather 상태가 포함되어 있는지 확인
   - weather 변경 → 추천 API 재호출 → 섹션 갱신 흐름이 완전한지 검증
3. weather theme(body class 또는 data attribute)도 날씨 변경 시 즉시 업데이트

### 검증 방법
- 데스크톱: 헤더 날씨 드롭다운 맑음→비→눈→흐림 변경 시 추천 섹션 즉시 갱신
- 모바일: 드로어에서 날씨 변경 시 동일하게 갱신
- MBTI, 기분 드롭다운도 여전히 정상 작동 (회귀 테스트)

---

## 이슈 2: 이메일 회원가입 후 온보딩 미진입 (❌ 차단)

### 현재 상태
- 카카오/Google OAuth 콜백: `is_new ? "/onboarding" : "/"` 분기 있음 ✅
- 이메일 signup: `signup() → login() → router.push("/")` → 온보딩 건너뜀 ❌

### 수정 사항
frontend/app/signup/page.tsx 수정:
1. signup() 성공 후 login() 호출
2. login 응답에서 사용자 정보의 onboarding_completed 확인
3. onboarding_completed가 false이면 router.push("/onboarding")
4. true이면 router.push("/") (기존 사용자가 재가입하는 경우는 없겠지만 방어)

### 참고 패턴
frontend/app/auth/kakao/callback/page.tsx:30-33 의 분기 로직을 참고

### 검증 방법
- 새 이메일로 회원가입 → 자동 로그인 → /onboarding 페이지 진입 확인
- 온보딩 완료 후 다시 로그인 시 바로 홈으로 이동 확인
- 카카오/Google 로그인 흐름은 기존대로 작동하는지 확인

---

## 이슈 3: 온보딩 저장 실패 시 무시하고 홈 이동 (❌ 차단)

### 현재 상태
frontend/app/onboarding/page.tsx:
- handleRate(): API 실패해도 UI 카운트는 올라감
- handleComplete(): completeOnboarding() 실패해도 router.replace("/")
- 건너뛰기: onboarding_completed 플래그 업데이트 없이 홈 이동

### 수정 사항

1. handleRate() 수정:
   - API 호출을 try-catch로 감싸기
   - 실패 시 UI 카운트를 롤백하고 토스트/에러 메시지 표시
   - "평점 저장에 실패했습니다. 다시 시도해주세요"

2. handleComplete() 수정:
   - completeOnboarding() 성공 시에만 router.replace("/")
   - 실패 시 이동하지 않고 에러 메시지 표시
   - "온보딩 완료에 실패했습니다. 다시 시도해주세요"

3. 건너뛰기(skip) 수정:
   - skip 시에도 completeOnboarding() API를 호출하여 플래그 업데이트
   - 또는 최소한 다음 로그인 시 온보딩이 다시 뜨지 않도록 처리
   - 실패 시에도 홈으로는 이동 허용 (skip은 사용자 의도이므로)

### 검증 방법
- 온보딩에서 영화 3편 평점 → 완료 → 홈 이동 확인
- 네트워크 끊고 평점 → 에러 메시지 표시 + 카운트 미증가 확인
- 건너뛰기 → 홈 이동 → 재로그인 시 온보딩 다시 안 뜨는지 확인

---

## 완료 후
- 각 이슈별 커밋 분리:
  1. "fix: sync weather state across header, mobile drawer, and home page"
  2. "fix: redirect email signup users to onboarding"
  3. "fix: handle onboarding save failures gracefully"
- push 및 Vercel/Railway 배포 확인
- 시연 시나리오 전체 재점검 (비로그인 → MBTI → 기분 → 날씨 → 검색 → 로그인 → 개인화)
- 결과를 claude_results.md에 기록