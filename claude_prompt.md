# 설정/평점 버그 2건 수정

## 이슈 1: 계정 탈퇴 확인 눌러도 삭제 안 됨

### 현재 증상
설정 페이지(/settings)에서 계정 탈퇴 버튼 클릭 → 경고 확인창 표시 → 확인 눌러도 계정 삭제 안 됨

### 조사 및 수정
1. frontend/app/settings/page.tsx에서 탈퇴 버튼의 onClick 핸들러 확인
2. 확인 후 호출되는 API 함수 확인 (lib/api.ts의 deleteAccount 또는 유사 함수)
3. 아래 가능한 원인을 순서대로 점검:

   a) API 호출 자체가 실행되지 않는 경우:
      - confirm() 반환값 체크 로직이 잘못되었거나
      - async/await 누락으로 API 호출이 fire-and-forget 되는지

   b) API 호출은 되지만 실패하는 경우:
      - DELETE /api/v1/users/me 엔드포인트가 존재하는지 확인
      - 엔드포인트 경로가 프론트와 백엔드 간 불일치인지
      - JWT 인증 토큰이 헤더에 포함되는지

   c) API 성공하지만 후처리가 없는 경우:
      - 성공 후 authStore.logout() 호출 확인
      - localStorage 정리 확인
      - 로그인 페이지로 리다이렉트 확인

   d) 에러가 catch되어 무시되는 경우:
      - try-catch에서 에러를 삼키고 있는지 확인
      - 에러 메시지가 사용자에게 표시되는지

4. 원인 파악 후 수정:
   - API 호출이 정상 실행되도록 수정
   - 성공 시: authStore 초기화 → localStorage 전체 정리 → router.push("/login")
   - 실패 시: 사용자에게 에러 메시지 표시 ("계정 삭제에 실패했습니다. 다시 시도해주세요")

### 검증
- 설정 → 계정 탈퇴 → 확인 → 로그아웃 + 로그인 페이지 이동
- 탈퇴 후 같은 이메일로 재로그인 시 실패 확인 (실제 삭제 확인)
- 취소 버튼 시 아무 일 없음 확인

---

## 이슈 2: 내 평점 페이지에서 평점 삭제 실패

### 현재 증상
내 평점(/ratings) 페이지에서 평점 삭제 시 "평점 지우기에 실패했습니다" 에러 메시지

### 조사 및 수정
1. frontend/app/ratings/page.tsx에서 삭제 핸들러 확인
2. 호출되는 API 함수 확인 (lib/api.ts의 deleteRating)
3. 아래 원인을 순서대로 점검:

   a) 프론트-백엔드 파라미터 불일치:
      - 프론트가 보내는 것: rating_id? movie_id? 
      - 백엔드가 기대하는 것: DELETE /api/v1/ratings/{rating_id}? 또는 DELETE /api/v1/ratings?movie_id=?
      - 두 경로가 일치하는지 확인

   b) API 경로 불일치:
      - lib/api.ts에 정의된 deleteRating URL과 backend/app/api/v1/ratings.py의 실제 경로 비교
      - /api/v1 prefix 누락 여부

   c) 인증 문제:
      - DELETE 요청에 JWT 토큰이 포함되는지
      - 해당 rating이 현재 로그인 유저의 것인지 백엔드에서 확인하는 로직

   d) 에러 메시지 파싱:
      - Codex 리뷰에서 지적된 fetchAPI의 에러 파싱 문제 (body.detail만 읽고 body.message를 안 읽음)
      - 실제 백엔드 에러 응답 형식과 프론트 파싱 로직이 맞는지

4. 원인 파악 후 수정:
   - API 경로/파라미터 일치시키기
   - 성공 시: 해당 영화의 평점을 목록에서 제거 + interactionStore 업데이트
   - 실패 시: 구체적 에러 메시지 표시

### 검증
- 내 평점 페이지 → 영화 평점 삭제 버튼 클릭 → 평점 제거 확인
- 삭제 후 해당 영화 상세에서 평점이 초기화 상태인지 확인
- 홈으로 돌아가서 해당 영화에 평점이 없는 상태인지 확인

---

## 공통: fetchAPI 에러 파싱 개선 (관련 이슈)

위 2건의 근본 원인이 에러 파싱 문제일 수 있으므로 함께 수정:

frontend/lib/api.ts의 fetchAPI 에러 처리 부분:
- 현재: body.detail만 읽음
- 수정: body.message → body.error → body.detail 순으로 파싱
- AbortError(timeout) 시: "서버 응답이 없습니다. 다시 시도해주세요" 메시지로 변환

---

## 완료 후
- 커밋 분리:
  1. "fix: account deletion not executing after confirmation"
  2. "fix: rating deletion failing on my ratings page"
  3. "fix: improve fetchAPI error message parsing" (필요 시)
- push 및 Vercel/Railway 배포 확인
- 시연 시나리오 점검: 설정 탈퇴 + 평점 삭제 동작 확인
- 결과를 claude_results.md에 기록