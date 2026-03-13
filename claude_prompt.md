# 맞춤 추천 영화 카드의 % 표시 원인 조사

## 현상
- 맞춤 추천(하이브리드) 섹션의 영화 카드 우측 상단에 % 수치가 표시됨
- 일부 영화에서 4~6%와 같이 매우 낮은 수치가 나옴
- 다른 섹션(인기영화, 높은평점 등)에서도 표시되는지 확인 필요

## 조사 항목

### 1. 프론트엔드: % 표시하는 컴포넌트 특정
- MovieCard.tsx 또는 MovieRow.tsx에서 % 관련 렌더링 코드 찾기
- 어떤 prop/데이터 필드를 % 로 표시하고 있는지 확인
  (match_score? score? relevance? rating? hybrid_score? ctr?)
- 해당 필드가 0~1 범위인지, 0~100 범위인지
- 0~1 범위를 그대로 × 100 하여 표시하는지, 아니면 원본 그대로 표시하는지

### 2. 백엔드: 해당 점수가 어디서 오는지 추적
- GET /api/v1/recommendations 응답의 각 영화 객체에 포함된 점수 관련 필드 전부 확인
- 실제 라이브 호출로 응답 샘플 확인:
  - GET /api/v1/recommendations (비로그인)
  - GET /api/v1/recommendations?weather=sunny&mood=relaxed&mbti=INTJ (파라미터 포함)
- 각 영화의 점수 필드값 범위 확인 (0.04 같은 값이 있는지)

### 3. 점수 계산 로직 추적
- backend/app/api/v1/recommendations.py에서 각 영화에 점수를 부여하는 로직
- backend/app/api/v1/recommendation_engine.py의 하이브리드 스코어링
- A/B 그룹별로 다른 점수가 나오는지:
  - control: 5축 하이브리드 스코어 (0~1)
  - test_a: Two-Tower → LightGBM CTR → 하이브리드 블렌딩
  - test_b: Two-Tower → 하이브리드 블렌딩
- 각 그룹에서 최종 점수의 실제 범위 (min, max, 평균)

### 4. 표시 조건
- 모든 섹션에서 % 가 표시되는지, 특정 섹션(맞춤추천)에서만 표시되는지
- 비로그인 vs 로그인 상태에서 차이가 있는지
- % 표시 여부를 결정하는 조건문이 있는지

## 리포트 형식
조사 결과

% 표시 위치: [파일:라인]
사용하는 데이터 필드: [필드명]
데이터 원천: [백엔드 파일:라인, 어떤 계산]
실제 값 범위: [min ~ max, 샘플 5개]
A/B 그룹별 차이: [있음/없음, 상세]
표시 조건: [모든 섹션/특정 섹션, 조건문]
낮은 % 원인: [구체적 원인]
제안:

숨기기 (어떤 코드를 변경해야 하는지)
정규화 (어떤 범위로, 어떤 공식으로)
현재 유지 (이유)

# 추천 알고리즘 품질 및 UI 표출 전반 검토

현재 추천 결과의 체감 품질이 낮다는 피드백이 있습니다.
알고리즘 로직 → 데이터 품질 → API 응답 → 프론트 표출까지 전체 파이프라인을 점검해주세요.
수정은 하지 말고 분석 결과만 리포트해주세요.

---

## 1. 추천 결과 실측 분석

### 1-1. 날씨 추천 품질
아래 4종을 실제 호출하고, 반환된 영화 10편의 제목과 장르를 나열:
- GET /api/v1/recommendations?weather=sunny
- GET /api/v1/recommendations?weather=rainy
- GET /api/v1/recommendations?weather=snowy
- GET /api/v1/recommendations?weather=cloudy

점검 기준:
- "비 오는 날"에 액션/SF가 나오지 않는지 (힐링/로맨스/드라마가 나와야 자연스러움)
- "맑은 날"에 호러/스릴러가 나오지 않는지
- 4종 간에 영화 중복이 얼마나 되는지 (50% 이상 겹치면 차별화 부족)

### 1-2. MBTI 추천 품질
아래 4종을 실제 호출:
- GET /api/v1/recommendations?mbti=INTJ
- GET /api/v1/recommendations?mbti=ENFP
- GET /api/v1/recommendations?mbti=ISFJ
- GET /api/v1/recommendations?mbti=ENTP

점검 기준:
- INTJ(분석적)에 지적 영화/SF/스릴러가 나오는지
- ENFP(열정적)에 모험/코미디/판타지가 나오는지
- 4종 간 중복률 확인

### 1-3. 기분 추천 품질
아래 4종을 실제 호출:
- GET /api/v1/recommendations?mood=relaxed
- GET /api/v1/recommendations?mood=tense
- GET /api/v1/recommendations?mood=excited
- GET /api/v1/recommendations?mood=gloomy

점검 기준:
- "편안한"에 힐링/가족 영화가 나오는지
- "긴장감"에 스릴러/범죄가 나오는지
- "신나는"에 액션/어드벤처가 나오는지
- "울적한"에 위로 + 카타르시스 영화가 나오는지

### 1-4. 조합 추천 품질
- GET /api/v1/recommendations?weather=rainy&mood=gloomy&mbti=INFP
- 3개 조건이 동시에 반영된 결과인지, 아니면 하나만 지배적인지 확인

---

## 2. 스코어링 로직 분석

### 2-1. 영화별 사전 계산 점수 분포
movies 테이블에서 실제 데이터 확인:
- mbti_scores JSONB: INTJ/ENFP 등 각 키의 값 분포 (min, max, avg, 표준편차)
- weather_scores JSONB: sunny/rainy 등 각 키의 값 분포
- emotion_tags JSONB: healing/tension 등 각 키의 값 분포

점검 기준:
- 값이 0.4~0.6에 몰려있으면 차별화 불가 (모든 영화가 비슷한 점수)
- 값이 0 또는 1로 양극화되어 있으면 순위 결정력이 높음
- null이나 빈 JSONB가 많으면 해당 축이 무의미

### 2-2. 가중치 균형
backend/app/api/v1/recommendation_engine.py 확인:
- 현재 가중치: MBTI 20% + Weather 15% + Mood 25% + Personal 15% + CF 25%
- Mood가 25%로 가장 높은데, 기분을 선택하지 않은 기본 상태에서 어떤 mood가 적용되는지
- 비로그인 사용자에게 Personal(15%) + CF(25%) = 40%가 어떻게 처리되는지
  (fallback이 0이면 나머지 축만으로 경쟁 → 점수 범위가 좁아짐)

### 2-3. 다양성 후처리 영향
backend/app/api/v1/diversity.py 확인:
- diversify_by_genre: 장르 셔플 후 원래 점수 순위가 크게 뒤바뀌는지
- apply_genre_cap: cap이 너무 작아서 좋은 영화가 잘리는지
- inject_serendipity: 랜덤 삽입이 결과 품질을 떨어뜨리는지
- 후처리 전/후 Top 20 비교 (후처리가 상위 영화를 밀어내는 정도)

---

## 3. 추천 이유 텍스트 품질

### 3-1. 추천 이유 생성 로직
backend/app/api/v1/recommendation_reason.py 확인:
- 43개 템플릿 중 실제로 어떤 기준으로 선택되는지
- 영화의 실제 특성과 추천 이유가 일치하는지

### 3-2. 실측 확인
위 1번에서 받은 영화들의 추천 이유(reason) 텍스트를 나열:
- 추천 이유가 해당 조건(날씨/기분/MBTI)과 연관되는지
- "비 오는 날" 추천인데 이유가 "인기 영화라서"이면 불일치
- 같은 문구가 반복되는지

---

## 4. UI 표출 점검

### 4-1. 섹션 타이틀
각 추천 섹션의 제목 확인:
- 날씨 섹션: "비 오는 날의 영화" vs "rainy 추천" (한글화 여부)
- 기분 섹션: "편안한 기분일 때" vs "relaxed 추천"
- MBTI 섹션: "INTJ 성향 추천" vs 그냥 "MBTI 추천"
- 타이틀이 현재 조건을 정확히 반영하는지

### 4-2. 큐레이션 문구
258개 큐레이션 문구가 실제로 표시되는지:
- 프론트에서 큐레이션 문구를 어디서 가져오는지
- 시간대/계절/날씨 조건에 맞는 문구가 선택되는지
- 아니면 고정 텍스트만 사용되는지

### 4-3. 섹션 간 영화 중복
홈 화면에 동시에 표시되는 섹션들 간 중복 확인:
- 인기영화 Row와 날씨추천 Row에 같은 영화가 있는지
- deduplicate_section 로직이 실제로 동작하는지
- 중복이 있다면 몇 편 수준인지

### 4-4. 영화 카드 정보 충실도
MovieCard에 표시되는 정보:
- 포스터 이미지 로딩 실패 시 fallback 처리
- 제목이 잘리는 경우 (긴 한글 제목)
- 평점/연도 표시 여부
- 추천 이유가 카드에 표시되는지, 아니면 호버/클릭 시에만 보이는지

---

## 5. 비로그인 vs 로그인 품질 차이

### 5-1. 비로그인 추천
- Personal(15%) + CF(25%) 축이 데이터 없이 어떻게 처리되는지
- 결과적으로 MBTI+Weather+Mood 3축만으로 추천되는지
- 그렇다면 인기도/평점 보정이 충분한지

### 5-2. 로그인 후 즉시
- 온보딩에서 장르 3개 + 영화 3편 평점을 준 직후
- Personal 축이 즉시 반영되는지 (찜/평점 데이터가 3편뿐)
- CF 축이 3편 평점으로 의미 있는 추천을 하는지

---

## 리포트 형식

각 항목별로:
[영역] 항목명

결과: ✅ 양호 / ⚠️ 개선 필요 / ❌ 문제
상세: 구체적 수치와 예시
시연 영향: 있음/없음
개선 제안: (문제인 경우)


마지막에:
추천 품질 종합 평가

날씨 차별화: 충분 / 부족
MBTI 차별화: 충분 / 부족
기분 차별화: 충분 / 부족
비로그인 품질: 양호 / 미흡
로그인 품질: 양호 / 미흡
UI 표현: 양호 / 미흡
가장 시급한 개선점 Top 3

결과를 claude_results.md에 기록해주세요.