# 맞춤 추천(하이브리드) 섹션 품질 및 갱신 문제 조사

## 보고된 증상
1. 맞춤 추천 섹션의 영화가 체감상 마음에 들지 않음 (날씨/기분/MBTI 개별 섹션은 양호)
2. 헤더에서 날씨/기분/MBTI를 변경해도 맞춤 추천 섹션의 영화가 바뀌지 않고 그대로 유지됨

이 두 증상은 연결되어 있을 가능성이 높습니다.
수정은 하지 말고 원인을 정확히 파악해주세요.

---

## 조사 1: 맞춤 추천 섹션이 드롭다운 변경에 반응하지 않는 문제

### 1-1. 백엔드: hybrid_row 생성 시 파라미터 반영 여부
backend/app/api/v1/recommendations.py에서:
- GET /recommendations 엔드포인트가 weather, mood, mbti 쿼리 파라미터를 받을 때
- hybrid_row를 생성하는 로직이 이 파라미터를 실제로 사용하는지 확인
- 아니면 hybrid_row는 user DB 정보(user.mbti, user.preferred_genres)만 사용하고
  쿼리 파라미터(헤더 드롭다운 값)는 개별 섹션(weather_row, mood_row, mbti_row)에만 적용되는지

라이브 검증:
- GET /api/v1/recommendations (로그인 토큰 포함, 파라미터 없음) → hybrid_row 영화 목록 기록
- GET /api/v1/recommendations?weather=rainy&mood=tense&mbti=ENFP (동일 토큰) → hybrid_row 영화 목록 기록
- 두 결과의 hybrid_row가 동일한지 다른지 비교

### 1-2. 백엔드: recommendation_engine.py 하이브리드 스코어링 입력값 추적
- get_hybrid_recommendations() 또는 유사 함수의 시그니처 확인
- 이 함수에 weather/mood/mbti가 인자로 전달되는지
- 아니면 user 객체의 고정 속성만 사용하는지
- 특히 mood 파라미터가 hybrid 계산에 들어가는지 vs mood_row 생성에만 쓰이는지

### 1-3. 프론트엔드: hybrid_row 캐싱/갱신 로직
frontend/app/page.tsx에서:
- 홈 추천 API 호출 시 weather/mood/mbti 파라미터가 모두 포함되는지
- API 응답의 hybrid_row를 캐싱하고 있는지 (useSWR, react-query, 자체 캐시 등)
- 캐시 키에 weather/mood/mbti가 포함되어 있는지
- 드롭다운 변경 시 캐시 키가 바뀌어 re-fetch가 트리거되는지

### 1-4. 프론트엔드: hybrid_row 렌더링 조건
- hybrid_row가 null이면 섹션 자체를 숨기는지
- API 재호출 시 hybrid_row가 새 데이터로 교체되는지
- 아니면 이전 데이터가 stale 상태로 남아있는지

---

## 조사 2: 맞춤 추천 영화 품질 문제

### 2-1. hybrid_row와 개별 섹션의 영화 소스 비교
라이브 호출 (로그인 상태):
- GET /api/v1/recommendations?weather=rainy&mood=tense&mbti=INTJ
- 응답에서 아래 섹션별 영화 10편씩 제목 나열:
  - weather_row (날씨 섹션)
  - mood_row (기분 섹션)  
  - mbti_row (MBTI 섹션)
  - hybrid_row (맞춤 추천 섹션)

비교 기준:
- hybrid_row가 날씨+기분+MBTI를 종합한 결과인지
- 아니면 개별 섹션과 무관한 별도 로직(CF/Personal 위주)인지
- hybrid_row에 날씨/기분/MBTI 조건과 어울리지 않는 영화가 있는지

### 2-2. A/B 그룹별 hybrid_row 생성 경로
각 그룹의 hybrid_row 생성 로직을 코드에서 추적:

control 그룹:
- DB 전체 스캔 → 5축 가중합산 → Top 20
- weather/mood/mbti 파라미터가 점수 계산에 반영되는지

test_a 그룹:
- Two-Tower(200편) → LightGBM(50편) → 5축 블렌딩 → Top 20
- Two-Tower 후보 추출 시 weather/mood/mbti가 반영되는지
- LightGBM 피처에 현재 날씨/기분이 포함되는지

test_b 그룹:
- Two-Tower(200편) → 5축 블렌딩(CF 70%) → Top 20
- CF가 70%이면 날씨/기분/MBTI 영향이 30%뿐 → 조건 변경해도 결과 변화 미미

### 2-3. 현재 로그인 사용자의 A/B 그룹 확인
- 테스트에 사용하는 계정의 experiment_group 확인
- 해당 그룹의 hybrid_row 로직이 어떤 경로인지 확인
- test_b(CF 70%)에 배정되어 있다면 조건 변경 영향이 극히 미미

### 2-4. hybrid 점수에서 각 축의 기여도 분석
로그인 상태에서 hybrid_row 영화 1편을 예시로:
- MBTI 축 기여: x점 × 가중치
- Weather 축 기여: x점 × 가중치
- Mood 축 기여: x점 × 가중치
- Personal 축 기여: x점 × 가중치
- CF 축 기여: x점 × 가중치
- 어느 축이 점수를 지배하는지 확인
- CF나 인기도가 지배적이면 조건 변경이 결과에 영향을 거의 못 미침

---

## 조사 3: 근본 원인 가설 검증

### 가설 A: hybrid_row가 쿼리 파라미터를 무시하고 user DB 값만 사용
검증: recommendations.py에서 hybrid 계산 함수 호출 시 전달하는 인자 목록 확인

### 가설 B: CF/Personal 축이 결과를 지배하여 나머지 축 변경이 무의미
검증: 가중치 합산에서 CF+Personal 비중 확인 (control 40%, test_a 63%, test_b 75%)

### 가설 C: 프론트 캐시가 드롭다운 변경을 반영하지 않음
검증: page.tsx의 캐시 키에 weather/mood/mbti가 포함되는지, API가 실제로 재호출되는지

### 가설 D: 백엔드에서 hybrid_row를 서버 캐시(Redis)하고 있어서 파라미터 변경이 무효
검증: recommendations.py에서 Redis 캐시 키에 weather/mood/mbti가 포함되는지

---

## 리포트 형식
맞춤 추천 섹션 문제 원인 분석
증상 1: 드롭다운 변경 시 hybrid_row 미갱신

근본 원인: [가설 A/B/C/D 중 확인된 것]
코드 위치: [파일:라인]
상세 설명:
영향 범위: [모든 사용자 / 특정 A/B 그룹 / 특정 상태]

증상 2: hybrid_row 영화 품질 낮음

근본 원인:
개별 섹션(날씨/기분/MBTI)과의 차이:
어느 축이 결과를 지배하는지:
실제 점수 분해 예시 (영화 1편):

수정 제안 (우선순위 순)

[가장 임팩트 큰 수정]
[차선 수정]
[장기 개선]


결과를 claude_results.md에 기록해주세요.