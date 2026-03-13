맞춤 추천 섹션 문제 원인 분석

참고
- 프로덕션 로그인 토큰이 없어 프롬프트에 적힌 "동일 토큰 live call"은 직접 수행하지 못했습니다.
- 대신 현재 코드 경로, 로컬 DB, 로컬 Two-Tower/LightGBM 모델 파일, 공개 API 계약을 기준으로 동일 로직을 재현했습니다.
- 이번 결론은 프런트 캐시 문제보다 백엔드 A/B 하이브리드 설계 문제에 가깝습니다.

증상 1: 드롭다운 변경 시 hybrid_row 미갱신

근본 원인: 가설 B 확인, 가설 A 부분 확인, 가설 C/D 기각
코드 위치: `frontend/app/page.tsx:127-163`, `backend/app/api/v1/recommendations.py:121-203`, `backend/app/services/two_tower_retriever.py:63-69`, `backend/app/services/reranker.py:33-37`, `backend/app/services/reranker.py:106-155`, `backend/app/api/v1/recommendation_engine.py:304-410`
상세 설명:
1. 프론트엔드는 드롭다운 변경을 정상 반영합니다. 홈은 `weather`, `mood`, `user?.mbti/guestMBTI`, `interaction_version`을 포함한 키로 캐시를 구분하고(`frontend/app/page.tsx:135-153`), 키가 바뀌면 `getHomeRecommendations(weather.condition, mood, mbtiParam)`를 다시 호출합니다(`frontend/app/page.tsx:147-163`). 따라서 가설 C는 성립하지 않습니다.
2. 서버 쪽 `recommendations.py`에는 hybrid_row용 Redis 캐시가 없습니다. 캐시 관련 로직은 시맨틱 검색 등에만 있고, 추천 홈 엔드포인트는 매 요청마다 `calculate_hybrid_scores()`를 다시 호출합니다. 따라서 가설 D도 성립하지 않습니다.
3. 다만 로그인 사용자의 `mbti` 쿼리 파라미터는 무시됩니다. `backend/app/api/v1/recommendations.py:121-123`에서 `mbti = current_user.mbti if current_user else mbti`로 덮어쓰므로, 인증된 요청에서 `?mbti=ENFP`를 붙여도 DB의 `user.mbti`가 우선입니다. 즉 가설 A는 "weather/mood는 반영되지만 로그인 사용자의 mbti 쿼리 override는 무시된다"는 형태로 부분적으로만 맞습니다.
4. 실제 반응성 저하는 A/B 하이브리드 경로에서 발생합니다. `test_a`/`test_b`는 Two-Tower 후보 추출을 쓰는데, `retrieve()` 입력이 `mbti`, `preferred_genres`뿐입니다(`backend/app/services/two_tower_retriever.py:63-69`). weather/mood는 후보 추출에 전혀 들어가지 않습니다. 따라서 같은 MBTI라면 날씨/기분을 바꿔도 후보 200편이 그대로 유지됩니다.
5. 로컬 DB 재현 결과가 이를 그대로 보여줍니다. 같은 `INTJ`에서 `sunny+relaxed`와 `rainy+tense`를 비교했을 때:
- `control`: top10 overlap `1/10`
- `test_a`: top10 overlap `9/10`, Two-Tower 후보 overlap `200/200`
- `test_b`: top10 overlap `9/10`, Two-Tower 후보 overlap `200/200`
즉 control은 컨텍스트 변화에 반응하지만, `test_a/test_b`는 거의 같은 영화를 유지합니다.
6. MBTI는 Two-Tower 후보 추출에 들어가므로 영향이 있습니다. 같은 `rainy+tense`에서 `INTJ -> ENFP`로 바꾸면 Two-Tower 후보 overlap이 `51/200`까지 내려갑니다. 다만 로그인 사용자라면 쿼리 mbti가 아니라 `user.mbti`를 실제로 바꿔야만 이 경로가 작동합니다.
7. `test_a`는 여기서 한 번 더 문제가 있습니다. LightGBM 재랭커의 mood vocabulary는 `happy/sad/excited/calm/tired/emotional`인데(`backend/app/services/reranker.py:36-37`), 앱이 실제로 넘기는 mood는 `relaxed/tense/excited/emotional/imaginative/light/gloomy/stifled`입니다(`frontend/types/index.ts:167`). 이 중 `excited`, `emotional`만 공통이고 `relaxed`, `tense`, `imaginative`, `light`, `gloomy`, `stifled`는 `MOOD_TO_IDX.get()`에서 `None`이 되어 mood one-hot이 전부 0으로 들어갑니다(`backend/app/services/reranker.py:106-155`). 즉 `test_a`에서는 상당수 mood 변경이 재랭커 단계에서 사실상 무효입니다.
8. 현재 사용자의 A/B 그룹을 `users.experiment_group`로 확인하는 것도 정확하지 않습니다. 추천 API는 그 컬럼을 쓰지 않고 `user_id/session_id` 해시로 그룹을 다시 계산합니다(`backend/app/api/v1/recommendations.py:44-65`, `111-118`). 로컬 DB 샘플 3명 기준 저장값과 런타임 그룹이 `3/3` 전부 불일치했습니다. 따라서 "현재 로그인 계정의 experiment_group 확인"은 DB 컬럼만 보면 오판할 수 있습니다.
영향 범위: 로그인 사용자 중 `test_a`와 `test_b`가 직접적인 영향권입니다. `test_b`가 가장 심하고, `test_a`는 weather는 약하게 반영되더라도 mood 반영이 절반 이상 깨져 있습니다. 추가로 인증 요청에서 `mbti` 쿼리 override를 기대하는 모든 디버그/QA 시나리오도 영향받습니다.

증상 2: hybrid_row 영화 품질 낮음

근본 원인:
- `test_a/test_b`의 hybrid_row는 날씨/기분/MBTI row를 합친 결과가 아니라, Two-Tower + CF 중심의 별도 후보군을 다시 점수화한 결과입니다.
- 특히 `test_b`는 `cf=0.70`이어서 조건축(`mbti+weather+mood`) 합계가 `0.25`뿐입니다(`backend/app/api/v1/recommendation_constants.py:48-54`).
- `test_a`도 `cf=0.50`이고, 앞서 설명한 mood feature mismatch 때문에 컨텍스트 품질이 더 떨어집니다(`backend/app/api/v1/recommendation_constants.py:40-46`, `backend/app/services/reranker.py:36-37`).

개별 섹션(날씨/기분/MBTI)과의 차이:
- `weather_row rainy` top10: `다크 나이트`, `기생충`, `시티 오브 갓`, `피아니스트`, `언터처블: 1%의 우정` ...
- `mood_row tension` top10: `인셉션`, `샤이닝`, `유주얼 서스펙트`, `죠스`, `새` ...
- `mbti_row INTJ` top10: `셔터 아일랜드`, `프레스티지`, `메멘토`, `인비저블 게스트`, `나를 찾아줘` ...
- 반면 같은 `rainy+tense+INTJ` 조건에서 `test_b` hybrid top10은 `Out of Print`, `Adjust Your Tracking`, `화해의 조건`, `핑크 리본 주식회사`, `The Murder of Fred Hampton` ...처럼 다큐멘터리/CF 편향 리스트가 나왔습니다.
- `control`에서는 같은 조건의 hybrid top10이 `다크 나이트`, `기생충`, `조커`, `사일런트 힐`, `메이즈 러너` 등으로 개별 row와 더 잘 맞물립니다. 품질 저하는 전체 공통 문제가 아니라 `test_a/test_b` 경로에 집중돼 있습니다.

어느 축이 결과를 지배하는지:
- `control`은 상대적으로 균형적입니다. mood, weather, mbti, cf가 모두 눈에 띄게 기여합니다.
- `test_a`는 CF가 절반을 가져가고, weather/mood/mbti가 후보 재정렬에서 크게 작동하지 않습니다. 특히 mood는 vocabulary mismatch 때문에 실제 입력 손실이 큽니다.
- `test_b`는 CF가 `70%`라 사실상 CF가 점수를 지배합니다. weather/mood/mbti를 바꿔도 top10 overlap이 `9/10`인 이유가 여기 있습니다.

실제 점수 분해 예시 (영화 1편):
- 시나리오: `test_b`, `INTJ`, `rainy`, `tense`
- 1위 영화: `Out of Print`
- 기여도:
  - MBTI 축: `0.12 * 0.08 = 0.0096`
  - Weather 축: `0.04 * 0.07 = 0.0028`
  - Mood 축: `0.0 * 0.10 = 0.0000`
  - Personal 축: `0.0 * 0.05 = 0.0000`
  - CF 축: `1.0 * 0.70 = 0.7000`
  - Quality factor: `0.8642`
  - 최종 hybrid_score: `0.6156`
- 같은 조건에서 `control` 1위 `다크 나이트`는 `mbti_contrib=0.106`, `weather_contrib=0.150`, `mood_contrib=0.225`, `cf_contrib=0.2041`로 훨씬 균형적입니다.

수정 제안 (우선순위 순)

[가장 임팩트 큰 수정]
- 홈 `hybrid_row`에 대해서는 일단 `test_b`를 중단하거나 `control/hybrid_v1`로 강제 fallback 하세요. 현재 재현 결과상 `control`만 컨텍스트 변화에 의미 있게 반응했고(`top10 overlap 1/10`), `test_a/test_b`는 반응성이 거의 없습니다(`9/10`). 사용자 체감 문제를 가장 빨리 줄이는 조치입니다.

[차선 수정]
- Two-Tower/Reranker의 feature contract를 현재 UI 컨텍스트와 맞추세요.
- 구체적으로는:
  - `TwoTowerRetriever.retrieve()` 입력에 weather/mood를 포함하거나, 적어도 후보 추출 이후 weather/mood-aware candidate filtering을 추가
  - `backend/app/services/reranker.py`의 mood vocabulary를 프런트 mood enum과 통일하거나 서버에서 명시적으로 매핑
  - 로그인 사용자의 `mbti` 쿼리 override를 디버그/QA용으로 허용할지 명확히 결정하고, 허용한다면 `current_user.mbti` 덮어쓰기를 제거

[장기 개선]
- A/B 그룹의 단일 source of truth를 정리하세요. 지금처럼 `users.experiment_group`는 저장하고 추천 API는 해시로 다시 계산하면 운영/분석/QA가 계속 헷갈립니다.
- 추천 응답이나 내부 로그에서 `effective_experiment_group`, `algorithm_version`, 축별 점수 분해를 쉽게 확인 가능하게 만들고, 자동 회귀 테스트를 추가해 `weather/mood/mbti` 변경 시 hybrid top-N overlap이 임계값 이하로 떨어지는지 검증하는 편이 좋습니다.
