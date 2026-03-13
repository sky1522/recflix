# 2026-03-13: 추천 UI 표현 개선 + Mood 기본값 제거

---

## 이슈 1: hybrid_score % 상대 정규화 ✅

### 변경 파일
- `frontend/components/movie/HybridMovieCard.tsx` — `rowMinScore`/`rowMaxScore` prop 추가, 상대 정규화 로직
- `frontend/components/movie/HybridMovieRow.tsx` — displayedMovies에서 min/max 계산 후 Card에 전달

### 핵심 변경
- Row 내 영화들의 hybrid_score를 **65-99%** 범위로 상대 정규화
- 공식: `65 + (score - min) / (max - min) * 34`
- 모든 점수 동일 시: **80%** 고정
- cold start 사용자의 4-6% 같은 오해 유발 수치 완전 제거

### 커밋
- `eb341a6` fix: normalize hybrid score display to 65-99% range

---

## 이슈 2: 기분 미선택 시 mood 섹션 숨김 ✅

### 변경 파일
- `backend/app/api/v1/recommendations.py` — mood 기본값 "relaxed" 제거

### 핵심 변경
- `mood` 파라미터가 null일 때 mood_row를 생성하지 않음
- 프론트엔드 `useMoodStore` 초기값은 이미 `null` → API에 mood 파라미터 미전송
- 사용자가 명시적으로 기분을 선택한 경우에만 기분 섹션 표시

### 커밋
- `fb10029` fix: hide mood section when no mood explicitly selected

---

## 이슈 3: OAuth 콜백 온보딩 분기 ✅ (이전 작업에서 완료)

### 상태
- `kakao/callback/page.tsx`, `google/callback/page.tsx` 모두 `onboarding_completed` 기반 라우팅 확인
- 이전 커밋 `34310cd`에서 이미 수정 완료

---

## 검증
- Frontend build: ✅ 성공 (에러 없음)
- Push: ✅ `fb10029` → main

---
---

# 2026-03-13: 맞춤 추천 % 표시 원인 조사 + 추천 품질 전반 검토

---

## % 표시 조사 결과

% 표시 위치: `frontend/components/movie/HybridMovieCard.tsx:139-144`
사용하는 데이터 필드: `movie.hybrid_score` (HybridMovie 인터페이스, `frontend/types/index.ts:51`)
데이터 원천: `backend/app/api/v1/recommendation_engine.py:284-432` — 5축 가중합산 하이브리드 스코어
실제 값 범위: 0.0~1.0 (×100 하여 0~100% 표시). `Math.round(movie.hybrid_score * 100)}%`
A/B 그룹별 차이: 있음 — control(규칙 기반), test_a(Two-Tower+LGBM+규칙), test_b(Two-Tower+규칙). CF 비중이 test_b에서 70%까지 올라감
표시 조건: `hybrid_score > 0`일 때만. HybridMovieCard(맞춤 추천 Row)에서만 표시, 일반 MovieCard에서는 미표시.
낮은 % 원인: 비로그인 시 hybrid_row=null이므로 해당 없음. 로그인 사용자에서 Personal(0)+CF(0)인 경우 MBTI+Weather+Mood만으로 점수 형성 → quality_factor(0.85~1.0) 적용 → 최종 점수가 0.04~0.06 수준까지 떨어질 수 있음. 특히 온보딩 직후 평점 3편만 있는 사용자는 Personal/CF 축이 거의 0에 수렴.

제안:
- **숨기기**: `HybridMovieCard.tsx:139`의 조건을 `hybrid_score >= 0.5` 등 임계값으로 변경하면 낮은 % 숨김 가능
- **정규화**: 반환된 hybrid_row 내 영화들의 min/max 기준 상대 정규화 (1위=99%, 최하위=60% 등)
- **현재 유지**: 스코어가 실제 매칭도를 반영하므로, 낮은 값이 정상이면 그대로 두되 시연 시 혼동 방지를 위해 숨기는 것을 권장

---

## 1. 추천 결과 실측 분석

### [날씨] 1-1. 날씨 추천 품질
결과: ✅ 양호
상세:
- sunny: 어드벤처/액션/애니메이션 중심 (스파이더맨, 어벤져스, 반지의제왕, 슈렉, 인사이드아웃)
- rainy: 드라마/로맨스/범죄 중심 (기생충, 조커, 프리즈너스, 노트북, 어바웃타임)
- snowy: 애니메이션/판타지/로맨스 중심 (너의이름은, 아멜리에, 하울의움직이는성)
- cloudy: 스릴러/범죄/SF 중심 (스플릿, V포벤데타, 조디악, 엑스마키나)
- 4종 간 중복: 최소 (날씨별 차별화 충분)
시연 영향: 없음

### [MBTI] 1-2. MBTI 추천 품질
결과: ✅ 양호
상세:
- INTJ: 심리스릴러/미스터리 (메멘토, 셔터아일랜드, 나를찾아줘, 겟아웃) — 분석적 성향 부합
- ENFP: 애니메이션/모험/판타지 (탱글드, 겨울왕국, 업, 주토피아) — 열정적 성향 부합
- ISFJ: 가족/힐링 드라마 (와일드로봇, 인사이드아웃, 원더, 나는샘) — 돌봄 성향 부합
- ENTP: 코미디/SF/비정형 (데드풀, 보랏, 돈룩업, 인터스텔라) — 혁신적 성향 부합
- 4종 간 중복: 극소
시연 영향: 없음

### [기분] 1-3. 기분 추천 품질
결과: ✅ 양호
상세:
- relaxed: 힐링/가족 (포레스트검프, 이웃집토토로, 소울, 그린북)
- tense: 호러/스릴러 (샤이닝, 양들의침묵, 겟아웃, 올드보이)
- excited: 액션/블록버스터 (존윅3편, 어벤져스, 익스펜더블즈)
- gloomy: 예술/중후 드라마 (택시드라이버, 쉰들러리스트, 댄서인더다크)
- 4종 간 중복: 최소
시연 영향: 없음

### [조합] 1-4. 조합 추천 품질
결과: ✅ 양호
상세: rainy+gloomy+INFP 호출 시 6개 섹션 반환. 날씨/기분/MBTI 섹션 각각 고유한 영화 목록. 3개 조건이 동시에 반영됨.
시연 영향: 없음

---

## 2. 스코어링 로직 분석

### [가중치] 2-1. 가중치 균형
결과: ⚠️ 개선 필요
상세:
- Control(CF 없음): MBTI 25%, Weather 20%, Mood 30%, Personal 25%
- Control(CF 있음): MBTI 20%, Weather 15%, Mood 25%, Personal 15%, CF 25%
- test_a: MBTI 12%, Weather 10%, Mood 15%, Personal 13%, CF 50%
- test_b: MBTI 8%, Weather 7%, Mood 10%, Personal 5%, CF 70%
- **비로그인 시**: Personal=0, CF=0 → 실질적으로 MBTI+Weather+Mood만 → 점수 범위 좁아짐
- **기분 미선택 시**: 기본값 "relaxed"(healing) 적용 → 항상 힐링 성향 가산
시연 영향: 비로그인 시 hybrid_row=null이므로 % 표시 안 됨. 로그인 직후 낮은 % 가능.
개선 제안: 비로그인 시 Personal/CF 가중치를 MBTI/Weather/Mood에 재분배하면 점수 범위 확대

### [다양성] 2-2. 다양성 후처리 영향
결과: ✅ 양호
상세:
- 장르 캡: 35% (적절)
- 연속 장르 제한: 3편 (적절)
- 최근작 보장: 20% (적절)
- 클래식 보장: 10% (적절)
- 세렌디피티: 10%, /for-you 엔드포인트에서만 적용 (홈 추천에는 미적용)
- 후처리 영향: ±5-15 순위 변동, 상위 영화 보존
시연 영향: 없음

---

## 3. 추천 이유 텍스트 품질

### [추천 이유] 3-1. 생성 로직
결과: ⚠️ 개선 필요
상세:
- 243개 템플릿, 5종 생성 함수 (복합, 기분, 개인화, MBTI, 날씨)
- 선택 우선순위: 복합 > 기분/개인화 > MBTI > 날씨 > 품질 > fallback
- **그러나**: 비로그인 응답(regular rows)에는 recommendation_reason 필드가 없음
- **hybrid_row에만 포함**: 로그인 + hybrid_row가 생성될 때만 추천 이유가 표시됨
- 일반 섹션(인기영화, 날씨추천 등)은 추천 이유 미제공
시연 영향: 비로그인 시연에서 추천 이유 미표시

---

## 4. UI 표출 점검

### [섹션 타이틀] 4-1. 한글화
결과: ✅ 양호
상세: 모든 섹션 타이틀 한글화 완료
- 날씨: "☀️ 맑은 날 추천", "🌧️ 비 오는 날 추천" 등
- 기분: "😌 편안한 기분일 때", "😰 긴장감이 필요할 때" 등
- MBTI: "💜 INTJ 성향 추천" (MBTI 코드는 영어, 자연스러움)
시연 영향: 없음

### [큐레이션 문구] 4-2. 서브타이틀
결과: ✅ 양호
상세:
- 258개 큐레이션 문구가 `lib/curationMessages.ts`에 정의
- 페이지 로드 시 랜덤 인덱스로 선택 (`subtitleIdx`)
- 섹션별 매칭: 인기영화→FIXED, MBTI→MBTI_SUBTITLES, 날씨→계절/기온 기반, 기분→MOOD_SUBTITLES
- 시간대/계절/기온 컨텍스트 반영 (`buildUserContext`)
시연 영향: 없음

### [중복] 4-3. 섹션 간 영화 중복
결과: ✅ 양호
상세: `deduplicate_section` 로직이 동작. hybrid_row → 이후 섹션 순서로 seen_ids 누적. 섹션 간 중복 극소.
시연 영향: 없음

### [카드] 4-4. 영화 카드 정보
결과: ✅ 양호
상세:
- 포스터 실패 시 fallback 처리 있음 (MovieCard)
- 제목: line-clamp-2로 2줄 제한
- 평점/연도: MovieCard에서 호버 시 표시
- 추천 이유: HybridMovieCard에서만 태그로 표시
시연 영향: 없음

---

## 5. 비로그인 vs 로그인 품질 차이

### [비로그인] 5-1. 게스트 추천
결과: ✅ 양호
상세:
- Personal(0) + CF(0) → MBTI+Weather+Mood 3축만 사용
- hybrid_row = null → % 표시 안 됨
- 인기도 부스트(+0.05) + 품질 보정(0.85~1.0)이 적용되어 결과 품질 유지
- 기본 mood="relaxed" → 항상 힐링 성향 가산 (의도된 동작)
시연 영향: 없음

### [로그인 직후] 5-2. 온보딩 직후
결과: ⚠️ 개선 필요
상세:
- 평점 3편 → CF 축이 유의미한 추천 어려움 (SVD는 최소 10+ 평점 권장)
- Personal 축: 선호 장르 3개로 genre matching → 최대 0.9까지 가능
- hybrid_score가 낮을 수 있음 (4~6% 표시 원인)
- Two-Tower 모델은 user embedding이 cold start 시 평균 벡터 사용 → 차별화 부족
시연 영향: 로그인 시연에서 낮은 % 표시 가능
개선 제안: hybrid_score < 0.3일 때 % 숨기기 또는 상대 정규화

---

## 추천 품질 종합 평가

날씨 차별화: **충분** — 4종 간 장르 분포가 명확히 다르고 중복 최소
MBTI 차별화: **충분** — 성향별 영화 선택이 직관적으로 부합
기분 차별화: **충분** — 감정 축별 영화 톤이 명확히 구분됨
비로그인 품질: **양호** — 3축만으로도 의미 있는 추천 결과
로그인 품질: **조건부 양호** — 충분한 평점 데이터 있으면 좋으나, cold start 시 낮은 hybrid_score
UI 표현: **양호** — 한글 타이틀, 큐레이션 문구, 중복 제거 모두 정상

### 가장 시급한 개선점 Top 3

1. **낮은 hybrid_score % 표시 문제**: cold start 사용자에게 4~6% 표시는 역효과. 임계값 도입 또는 상대 정규화 필요
2. **비로그인 시 기본 mood="relaxed" 고정**: 기분 미선택 시 항상 힐링 영화가 가산됨. null 처리하여 mood 축 제외가 더 자연스러울 수 있음
3. **일반 섹션에 추천 이유 미제공**: 날씨/기분/MBTI 섹션에도 간단한 이유 텍스트가 있으면 시연 임팩트 증가

---

# 2026-03-13: OAuth 콜백 온보딩 분기 수정

## 변경 파일
- `frontend/app/auth/kakao/callback/page.tsx:31-34`
- `frontend/app/auth/google/callback/page.tsx:31-34`

## 핵심 변경사항
- 기존: `isNew ? "/onboarding" : "/"` — 신규 여부만으로 분기
- 수정: `!user?.onboarding_completed ? "/onboarding" : "/"` — 온보딩 완료 여부로 분기
- 이제 "기존 사용자이지만 온보딩 미완료" 상태에서도 온보딩 페이지로 진입

## 검증
- Frontend 빌드 성공, push 완료

---

# 2026-03-13: 설정/평점 버그 2건 수정

## 근본 원인
- `fetchAPI()`가 HTTP 204 No Content 응답에서 `response.json()`을 호출하여 파싱 에러 발생
- 백엔드 `DELETE /users/me`와 `DELETE /ratings/{movie_id}` 모두 204를 반환
- 에러가 catch되어 삭제 실패로 처리됨

## 수정 내용

### 1. fetchAPI 204 No Content 처리 + 에러 메시지 파싱 개선
- **파일**: `frontend/lib/api.ts:86-95`
- `response.status === 204` 시 JSON 파싱 건너뛰고 `undefined` 반환
- 에러 메시지: `body.detail`만 → `body.message || body.error || body.detail` 순서로 파싱
- 이 한 줄 수정으로 계정 삭제, 평점 삭제 두 이슈 모두 해결

### 2. 계정 삭제 실패 시 에러 메시지 표시
- **파일**: `frontend/app/settings/page.tsx:103`
- 기존: catch에서 `setDeleting(false)`만 실행 (사용자에게 피드백 없음)
- 수정: `alert("계정 삭제에 실패했습니다. 다시 시도해주세요.")` 추가

## 검증
- Frontend 빌드 성공
- 커밋 분리: fetchAPI 수정 (`668ff0c`) + 설정 에러 메시지 (`dce1238`)
- push 완료, Vercel 자동 배포 예정

---

테스트 1-1: 게스트 홈 첫 로드 섹션 검증
결과: ✅ 통과
방법: 둘 다
상세: 프로덕션 `GET /api/v1/recommendations`가 200을 반환했고, 섹션은 `인기 영화 -> 높은 평점 영화 -> 편안한 기분일 때` 순서로 내려왔으며 각 row가 비어 있지 않았습니다. `backend/app/api/v1/recommendations.py`의 게스트 분기 역시 `popular -> top_rated -> weather -> mood -> mbti` 순서를 사용하므로 현재 응답과 일치합니다. 기본 mood가 없을 때 `relaxed`로 보정되어 mood row가 항상 붙습니다.

테스트 1-2: 날씨 API
결과: ✅ 통과
방법: 둘 다
상세: 프로덕션 `GET /api/v1/weather?lat=37.26&lon=127.03`가 200을 반환했고 `city="수원시"`, `description_ko="맑음"`, `temperature=11.7`, `condition="sunny"`를 확인했습니다. 프런트 `frontend/lib/api.ts`와 `frontend/hooks/useWeather.ts`도 같은 필드를 소비합니다.

테스트 1-3: 헤더 날씨 렌더링
결과: ✅ 통과
방법: 코드 검증
상세: 데스크톱 헤더 `frontend/components/layout/Header.tsx:253`은 `weather.city ? "city · description temperature" : "temperature"` 형태로 렌더링합니다. 모바일 드로어 `frontend/components/layout/HeaderMobileDrawer.tsx:166-168`도 `city + temperature`와 `description_ko`를 함께 보여주며, city가 없으면 온도만 남는 fallback이 있습니다.

테스트 2-1: MBTI 드롭다운 반응성
결과: ✅ 통과
방법: 코드 검증
상세: 게스트 기준으로 `frontend/components/layout/Header.tsx:66-68`, `frontend/components/layout/HeaderMobileDrawer.tsx:89-91`가 모두 `guest_mbti`를 localStorage에 저장하고 `guest_mbti_change`를 dispatch합니다. `frontend/app/page.tsx:58-63`은 이를 수신해 state를 갱신하고, 추천 호출은 `frontend/app/page.tsx:147-148`에서 guest MBTI를 `mbti` query로 전달합니다.

테스트 2-2: 기분 드롭다운 반응성
결과: ✅ 통과
방법: 코드 검증
상세: 데스크톱 헤더 `frontend/components/layout/Header.tsx:148-149`, 모바일 드로어 `frontend/components/layout/HeaderMobileDrawer.tsx:214`가 모두 `useMoodStore`를 갱신합니다. 홈 `frontend/app/page.tsx:127-163`은 `mood`를 effect dependency에 포함하고 `getHomeRecommendations(weather.condition, mood, mbtiParam)`로 API를 다시 호출합니다.

테스트 2-3: 날씨 드롭다운 반응성
결과: ✅ 통과
방법: 코드 검증
상세: `frontend/hooks/useWeather.ts:163-245`에서 `setManualWeather()`가 `manual_weather_change`를 dispatch하고, 다른 `useWeather` 인스턴스가 이를 수신해 동기화합니다. 데스크톱/모바일 헤더는 모두 `setManualWeather()`를 호출하며, 홈 `frontend/app/page.tsx:96-163`은 `weather`를 dependency로 감시하고 `weather.condition`을 추천 API에 넘깁니다.

테스트 2-4: 3개 드롭다운 데스크톱/모바일 동기화 비교
결과: ✅ 통과
방법: 코드 검증
상세: MBTI는 CustomEvent, mood는 Zustand store, weather는 `manual_weather_change` + `useWeather` 동기화로 데스크톱과 모바일이 같은 경로를 탑니다. 이번 점검 기준으로 모바일 드로어도 MBTI 이벤트 dispatch가 추가되어 이전 분리 상태는 해소됐습니다.

테스트 3-1: 날씨별 추천 차이
결과: ✅ 통과
방법: API 호출
상세: `GET /api/v1/recommendations?weather=sunny`와 `?weather=rainy` 모두 200이며, 날씨 row 제목이 각각 `맑은 날 추천`, `비 오는 날 추천`으로 달랐고 첫 영화도 서로 달랐습니다. weather query가 추천 결과에 실제 반영되고 있습니다.

테스트 3-2: MBTI별 추천 차이
결과: ✅ 통과
방법: API 호출
상세: `GET /api/v1/recommendations?mbti=INTJ`와 `?mbti=ENFP` 모두 200이며, MBTI row 제목과 첫 추천 영화가 서로 달랐습니다. `backend/app/api/v1/recommendations.py`의 `mbti_scores` 분기가 실제 응답 차이로 확인됐습니다.

테스트 3-3: 기분별 추천 차이
결과: ❌ 실패
방법: 둘 다
상세: 프롬프트 기준 호출인 `GET /api/v1/recommendations?mood=healing`와 `?mood=tension`은 둘 다 422를 반환했습니다. 현재 홈 추천 엔드포인트는 `relaxed|tense|excited|emotional|imaginative|light|gloomy|stifled`만 허용하며(`backend/app/api/v1/recommendations.py:103-105`), `healing|tension`은 별도 `GET /api/v1/recommendations/emotion`에서만 동작합니다.

테스트 4-1: 이메일 회원가입 후 온보딩 분기
결과: ✅ 통과
방법: 코드 검증
상세: `frontend/app/signup/page.tsx:55-57`가 auto-login 뒤 `useAuthStore.getState().user`를 읽고 `user?.onboarding_completed ? "/" : "/onboarding"`로 분기합니다. 신규 이메일 가입자는 온보딩으로 보내도록 수정돼 있습니다.

테스트 4-2: Kakao OAuth 분기
결과: ❌ 실패
방법: 코드 검증
상세: `frontend/app/auth/kakao/callback/page.tsx:32-33`는 여전히 `const isNew = socialLogin(response); router.replace(isNew ? "/onboarding" : "/")`만 사용합니다. `response.user.onboarding_completed === false`인데 `is_new === false`인 사용자는 온보딩이 필요한 상태여도 홈으로 빠질 수 있습니다.

테스트 4-3: Google OAuth 분기
결과: ❌ 실패
방법: 코드 검증
상세: `frontend/app/auth/google/callback/page.tsx:32-33`도 Kakao와 같은 분기 로직을 사용합니다. 신규 여부만 보고 이동하므로 `onboarding_completed` 상태를 복구하지 못합니다.

테스트 4-4: 온보딩 안정성
결과: ⚠️ 주의
방법: 코드 검증
상세: `frontend/app/onboarding/page.tsx:58-67`는 평점 저장 실패 시 local state를 rollback하고 에러를 노출합니다. `handleComplete()`는 실패 시 홈으로 이동하지 않고 페이지에 남습니다(`70-79`). 다만 `handleSkip()`는 `completeOnboarding([])`를 먼저 호출하도록 수정됐지만(`82-88`), 실패해도 에러 없이 홈으로 이동하므로 `onboarding_completed` 누락을 숨길 수 있습니다.

테스트 5-1: 시맨틱 검색
결과: ✅ 통과
방법: 둘 다
상세: 프로덕션 `GET /api/v1/movies/semantic-search?q=따뜻한 가족 영화`가 200을 반환했고 `total=20`, `fallback=false`였습니다. 결과에 `패밀리`, `인스턴트 패밀리`, `투 이즈 어 패밀리` 등 가족 관련 타이틀이 포함되어 의도한 검색이 동작합니다.

테스트 5-2: 자동완성
결과: ❌ 실패
방법: 둘 다
상세: 프롬프트 그대로 `GET /api/v1/movies/search/autocomplete?q=인터`를 호출하면 422가 납니다. 백엔드 시그니처와 프런트 API 래퍼는 모두 `query` 파라미터를 사용합니다(`backend/app/api/v1/movies.py:40-42`, `frontend/lib/api.ts:394-395`). 실제로 `GET /api/v1/movies/search/autocomplete?query=인터`는 200입니다.

테스트 6-1: 영화 상세 API
결과: ✅ 통과
방법: API 호출
상세: 프로덕션 `GET /api/v1/movies/278`가 200을 반환했고 `title_ko`, `cast_ko`, `genres`, `trailer_key`가 모두 채워져 있었습니다. 이번 응답에서는 `title_ko="쇼생크 탈출"`, `genres=[드라마, 범죄]`, `trailer_key="PLl99DlL6b4"`를 확인했습니다.

테스트 6-2: 유사 영화
결과: ✅ 통과
방법: API 호출
상세: 프로덕션 `GET /api/v1/movies/278/similar`가 200을 반환했고 10개의 유사 영화가 내려왔습니다. 상세 페이지에서 후속 row를 구성할 데이터는 충분합니다.

테스트 6-3: MovieModal 장르 칩 이동
결과: ✅ 통과
방법: 코드 검증
상세: `frontend/components/movie/MovieModal.tsx:240-249`에서 장르 칩이 `button`으로 렌더링되고, 클릭 시 `onClose()` 후 `router.push(`/movies?genre=...`)`를 호출합니다. span-only 구현은 더 이상 아닙니다.

테스트 7-1: Optimistic UI
결과: ✅ 통과
방법: 코드 검증
상세: `frontend/stores/interactionStore.ts:85-154`에서 `toggleFavorite()`와 `setRating()` 모두 먼저 optimistic update를 적용한 뒤 실패 시 이전 상태로 rollback합니다. 성공 시 `interaction_version`을 올려 홈 추천 캐시 무효화까지 연결됩니다.

테스트 7-2: 찜/평점 API 실호출
결과: ⚠️ 주의
방법: 둘 다
상세: 실제 구현된 찜 route는 프롬프트 표기와 달리 `POST /api/v1/interactions/favorite/{movie_id}`입니다(`backend/app/api/v1/interactions.py:114-159`, `frontend/lib/api.ts:332-335`). 공개 무인증 호출 결과 bare path는 404, 실제 path와 `POST /api/v1/ratings`는 403이었으므로 auth guard는 정상입니다. 다만 사용자 토큰이 없어 "성공" 호출까지는 재현하지 못했습니다.

테스트 8-1: 테마 저장
결과: ✅ 통과
방법: 코드 검증
상세: `frontend/stores/themeStore.ts:24-46`가 Zustand persist로 `theme-storage`에 값을 저장하고, `setTheme`/`toggleTheme`에서 즉시 `html.light` 클래스를 반영합니다. `frontend/components/layout/ThemeProvider.tsx:6-18`도 hydration 이후 동일 클래스를 유지합니다.

테스트 8-2: FOUC 방지
결과: ✅ 통과
방법: 코드 검증
상세: `frontend/app/layout.tsx:61-64`의 inline script가 hydration 전에 localStorage의 `theme-storage`를 읽어 light 클래스를 선반영합니다. 라이트 모드 깜빡임 방지 경로가 있습니다.

테스트 9-1: 루트 헬스체크
결과: ✅ 통과
방법: API 호출
상세: 프로덕션 `GET /health`가 200과 `{"status":"healthy"}`를 반환했습니다.

테스트 9-2: 상세 헬스체크
결과: ✅ 통과
방법: 둘 다
상세: 프로덕션 `GET /api/v1/health`가 200과 함께 `database=connected`, `redis=connected`, `semantic_search=enabled`, `cf_model=loaded`, `two_tower=loaded`, `reranker=loaded`를 반환했습니다. 전체 `status` 값은 `healthy`가 아니라 `ok`이지만, 필수 컴포넌트 상태는 모두 양호합니다.

테스트 10-1: CORS
결과: ⚠️ 주의
방법: 둘 다
상세: `backend/app/main.py:94-100`은 CORS를 `settings.CORS_ORIGINS`에 위임하고, 기본값은 `backend/app/config.py:54` 기준 localhost/127.0.0.1만 포함합니다. 다만 프로덕션 `GET /api/v1/health`에 `Origin: https://jnsquery-reflix.vercel.app`를 붙여 호출했을 때 `Access-Control-Allow-Origin: https://jnsquery-reflix.vercel.app`, `Access-Control-Allow-Credentials: true`를 확인했으므로 런타임 환경변수에는 운영 도메인이 들어가 있습니다. 코드 기본값만 보면 운영 구성이 드러나지 않는 점은 주의가 필요합니다.

테스트 10-2: Rate Limiting
결과: ⚠️ 주의
방법: 코드 검증
상세: `backend/app/core/rate_limit.py`에 slowapi `Limiter`가 있고, `backend/app/main.py:139-147`에 429 통합 핸들러가 있습니다. 다만 이번 점검에서는 의도적으로 요청을 연속 발사해 429를 실측하지는 않았습니다.

테스트 11-1: 계정 삭제 경로
결과: ⚠️ 주의
방법: 둘 다
상세: 설정 페이지 `frontend/app/settings/page.tsx:96-101,295-315`에는 확인 모달과 삭제 버튼이 있고, 삭제 시 `DELETE /api/v1/users/me` 후 `logout()`과 홈 이동을 수행합니다. 백엔드 `backend/app/api/v1/users.py:84-118`는 `user_events` 명시 삭제 후 user hard delete를 수행하고 ratings/collections cascade를 전제로 합니다. 다만 프런트 실패 처리가 조용하고, 인증 토큰이 없어 실제 삭제 성공까지는 검증하지 못했습니다.

테스트 11-2: 닉네임 변경
결과: ✅ 통과
방법: 코드 검증
상세: `frontend/app/settings/page.tsx:56-72`가 `PUT /api/v1/users/me`(`frontend/lib/api.ts:250-254`)로 닉네임을 저장하고, 성공 시 `fetchUser()`로 상태를 새로 읽습니다. 실패 시 기존 닉네임으로 되돌립니다.

테스트 11-3: MBTI 변경
결과: ✅ 통과
방법: 코드 검증
상세: 설정 화면은 `MBTIModal`을 열고(`frontend/app/settings/page.tsx:191-197,292`), 모달 내부 `frontend/components/layout/MBTIModal.tsx:93-107`가 인증 사용자의 MBTI를 `updateMBTI()`로 저장합니다. 저장 후 `fetchUser()`가 다시 실행되며, 홈 `frontend/app/page.tsx:163`는 `user?.mbti` 변경을 dependency로 감지합니다.

테스트 11-4: 선호 장르 변경
결과: ⚠️ 주의
방법: 코드 검증
상세: 설정 페이지 `frontend/app/settings/page.tsx:74-89`가 3개 이상 장르를 고르게 하고 `completeOnboarding(selectedGenres)`로 저장한 뒤 `fetchUser()`를 호출합니다. 기능 경로는 존재하지만 실패 시 사용자에게 별도 에러를 보여주지 않습니다.

테스트 11-5: 테마 설정 화면 연동
결과: ✅ 통과
방법: 코드 검증
상세: 설정 페이지 `frontend/app/settings/page.tsx:242-266`의 토글이 `useThemeStore().toggleTheme`에 직접 연결되어 있고, 저장은 `theme-storage`를 통해 유지됩니다. UI와 store 계약은 일치합니다.

테스트 11-6: 로그아웃 후 보호 페이지 처리
결과: ⚠️ 주의
방법: 코드 검증
상세: `frontend/stores/authStore.ts:61-67`는 로그아웃 시 access/refresh token 제거와 interaction cache 초기화를 수행합니다. `/settings`는 `frontend/app/settings/page.tsx:43-47`에서 비로그인 시 `/login`으로 redirect합니다. 다만 `/favorites`는 redirect 대신 비로그인 전용 안내 화면을 렌더링합니다(`frontend/app/favorites/page.tsx:93-184`). 보호 페이지를 모두 redirect해야 하는 시연 기준이라면 동작이 일관되지 않습니다.

시연 준비 상태 요약
- ✅ 통과: 22건
- ⚠️ 주의: 7건
- ❌ 실패: 4건
- 시연 가능 여부: 조건부 가능
- 핵심 보완 우선순위: `4-2 Kakao OAuth 분기`, `4-3 Google OAuth 분기`, `3-3 홈 추천 mood 파라미터 계약`, `5-2 자동완성 q/query 계약`
- 보조 검증: `backend pytest backend/tests -q`는 `10 passed, 4 skipped`, `frontend tsc --noEmit`는 통과했습니다.
