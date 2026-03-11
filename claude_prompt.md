# 비로그인 시 MBTI 추천 섹션 홈 화면 노출

## 현재 상황
- 헤더의 MBTI 드롭다운은 비로그인 시에도 선택 가능 (guest_mbti → localStorage 저장)
- 그러나 홈 페이지(page.tsx)의 추천 섹션에서 MBTI 섹션은 로그인 사용자에게만 표시됨
- 비로그인 시 홈 화면 섹션: 인기영화, 높은 평점 영화, 날씨 추천, 기분 추천, 한국인기영화 (MBTI 섹션 없음)

## 요구사항
비로그인 상태에서 헤더의 MBTI 드롭다운으로 MBTI를 선택하면(또는 localStorage에 guest_mbti가 있으면), 홈 화면에 MBTI 추천 섹션이 나타나도록 수정

## 구현 방향
1. `frontend/app/page.tsx`에서 MBTI 추천 섹션 렌더링 조건 확인
   - 현재: 로그인 사용자의 user.mbti가 있을 때만 MBTI 섹션 표시하는 로직이 있을 것
   - 변경: localStorage의 guest_mbti도 함께 확인하여, 둘 중 하나라도 있으면 MBTI 섹션 표시

2. MBTI 값 소스 우선순위:
   - 로그인 사용자 → user.mbti 사용 (기존 그대로)
   - 비로그인 사용자 → localStorage의 guest_mbti 사용

3. MBTI 추천 API 호출 시 mbti 파라미터를 전달하는 부분에서도 같은 우선순위 적용
   - GET /recommendations/mbti?mbti=INTJ 형태로 호출될 것으로 예상

4. 헤더에서 guest_mbti를 변경하면 홈의 MBTI 섹션도 즉시 갱신되어야 함
   - 이미 헤더 드롭다운 변경 시 상태 업데이트 로직이 있을 것이므로, 해당 상태를 MBTI 섹션이 구독하도록 연결

## 주의사항
- 기존 로그인 사용자의 MBTI 추천 로직은 변경하지 않음
- MBTI가 선택되지 않은 비로그인 사용자에게는 MBTI 섹션을 표시하지 않음 (guest_mbti가 null이면 기존처럼 미표시)
- 섹션 제목은 "INTJ 성향 추천" 같은 기존 포맷 그대로 사용

## 완료 후
- 커밋 메시지: "feat: show MBTI recommendation section for guest users with guest_mbti"
- push 및 Vercel 배포 확인
- 비로그인 상태에서 MBTI 선택 → MBTI 섹션 나타남 → MBTI 변경 → 섹션 갱신 확인
- 결과를 claude_results.md에 기록