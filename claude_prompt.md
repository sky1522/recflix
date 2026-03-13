# 헤더 날씨 드롭다운 선택 시 추천 섹션 즉시 갱신 안 되는 버그 수정

## 현재 상황
- 헤더의 MBTI 드롭다운: 선택 변경 시 → 홈 화면 영화 섹션 즉시 갱신됨 ✅
- 헤더의 기분 드롭다운: 선택 변경 시 → 홈 화면 영화 섹션 즉시 갱신됨 ✅
- 헤더의 날씨 드롭다운: 선택 변경 시 → 홈 화면 영화 섹션 갱신 안 됨 ❌

## 증상
날씨를 "맑음"에서 "비"로 변경해도 추천 섹션(날씨 추천 Row 등)이 그대로 유지됨
페이지를 새로고침해야 변경된 날씨가 반영됨

## 예상 원인
MBTI와 기분은 드롭다운 변경 시 Zustand store 또는 상태를 업데이트하고,
홈 페이지(page.tsx)가 해당 상태를 구독하여 추천 API를 재호출하는 구조일 것

날씨는 아마 다음 중 하나일 가능성이 높음:
1. 날씨 드롭다운 onChange에서 store 업데이트는 하지만, 홈 페이지가 날씨 상태를 구독하지 않음
2. 날씨 변경 시 추천 API 재호출 트리거가 빠져있음
3. 날씨가 OpenWeatherMap API 응답값만 사용하고, 수동 선택값을 추천 요청에 전달하지 않음

## 수정 방향
1. MBTI와 기분이 드롭다운 변경 → 추천 갱신되는 흐름을 먼저 파악 (참고 패턴)
2. 날씨 드롭다운도 동일한 흐름으로 동작하도록 수정
3. 구체적으로:
   - 날씨 드롭다운 onChange에서 상태(store 또는 state) 업데이트 확인
   - 홈 page.tsx의 useEffect 또는 데이터 fetch 로직에서 날씨 상태를 dependency에 포함
   - 추천 API 호출 시 변경된 날씨값이 파라미터로 전달되는지 확인

## 확인 포인트
- 기분 드롭다운의 onChange 핸들러와 날씨 드롭다운의 onChange 핸들러를 비교
- page.tsx에서 mood/mbti 상태 변경을 감지하는 useEffect가 있다면, weather도 동일하게 포함되어 있는지
- GET /recommendations 호출 시 weather 파라미터가 수동 선택값으로 전달되는지

## 완료 후
- 커밋: "fix: weather dropdown selection now triggers recommendation refresh"
- push 및 Vercel 배포 확인
- 테스트: 날씨 드롭다운에서 맑음→비→눈→흐림 순서로 변경하며 추천 섹션이 즉시 갱신되는지 확인
- MBTI, 기분도 여전히 정상 작동하는지 회귀 테스트
- 결과를 claude_results.md에 기록