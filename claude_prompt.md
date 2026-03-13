# 추천 UI 표현 개선 2건 + OAuth 온보딩 분기 수정

---

## 이슈 1: 낮은 hybrid_score % 표시 문제

### 현재 상태
- HybridMovieCard.tsx:139-144에서 hybrid_score * 100을 % 표시
- cold start 사용자(평점 3편)는 Personal=0, CF=0 → 4~6% 표시
- 청중이 "추천 정확도 4%"로 오해

### 수정: 상대 정규화 방식 적용
HybridMovieCard.tsx 또는 hybrid_row를 렌더링하는 부모 컴포넌트에서:

1. hybrid_row 내 영화들의 점수를 상대 정규화:
   - row 내 최고 점수 = 99%, 최저 점수 = 65%
   - 공식: normalizedScore = 65 + (score - minScore) / (maxScore - minScore) * 34
   - maxScore === minScore인 경우 (모두 같은 점수): 80% 고정

2. 정규화 위치: 
   - 프론트에서 처리 (백엔드 수정 불필요)
   - page.tsx에서 hybrid_row 데이터를 받은 후, 렌더링 전에 정규화
   - 또는 HybridMovieCard에 row 내 min/max를 prop으로 전달

3. 대안 (더 간단): hybrid_score < 0.3이면 % 숨기기
   - HybridMovieCard.tsx:139의 조건을 hybrid_score >= 0.3으로 변경
   - 이 방법이 가장 안전하고 빠름

### 검증
- 로그인 후 맞춤 추천 섹션: 65~99% 범위 또는 % 미표시
- 4~6% 같은 낮은 수치 노출 없음

---

## 이슈 2: 기분 미선택 시 기본 mood="relaxed" 고정

### 현재 상태
- 사용자가 기분을 선택하지 않아도 기본값 "relaxed" 적용
- 홈 화면에 "편안한 기분일 때" 섹션이 항상 표시됨
- 사용자 입장에서 "나는 기분을 선택한 적 없는데 왜 이게 나오지?"

### 수정
backend/app/api/v1/recommendations.py에서:
1. mood 파라미터가 null/빈값이면 mood_row를 생성하지 않음
2. 기분 섹션은 사용자가 명시적으로 기분을 선택했을 때만 표시

프론트에서:
1. page.tsx: mood가 null/undefined일 때 API 호출 시 mood 파라미터를 보내지 않음
2. moodStore 초기값 확인: 초기 상태가 "relaxed"이면 null로 변경

### 주의사항
- 기분을 선택한 후에는 정상적으로 mood_row 표시
- 기분을 "초기화"하는 버튼이 있다면 null로 되돌리기
- 비로그인 첫 접속: 날씨 섹션만 표시 (기분/MBTI는 선택 시에만)

### 검증
- 첫 접속(기분 미선택): 기분 섹션 미표시
- 기분 "긴장감" 선택: "긴장감이 필요할 때" 섹션 표시
- 기분 변경/초기화: 섹션 업데이트 또는 제거

---

## 이슈 3: OAuth 콜백 온보딩 분기 (이전 테스트 ❌ 건)

### 수정 대상
1. frontend/app/auth/kakao/callback/page.tsx:32-33
2. frontend/app/auth/google/callback/page.tsx:32-33

### 현재:
const isNew = socialLogin(response)
router.replace(isNew ? "/onboarding" : "/")

### 수정:
socialLogin(response)
const user = useAuthStore.getState().user
const needsOnboarding = !user?.onboarding_completed
router.replace(needsOnboarding ? "/onboarding" : "/")

### 검증
- 카카오 신규 가입 → 온보딩 진입
- 카카오 기존(온보딩 완료) → 홈 이동
- 카카오 기존(온보딩 미완료) → 온보딩 진입
- Google도 동일 3가지 확인

---

## 완료 후
- 커밋 분리:
  1. "fix: normalize hybrid score display to 65-99% range"
  2. "fix: hide mood section when no mood explicitly selected"
  3. "fix: use onboarding_completed for OAuth callback routing"
- push 및 배포 확인
- 시연 시나리오 재점검
- 결과를 claude_results.md에 기록