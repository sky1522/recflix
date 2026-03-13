# 2026-03-13: 한국 인기 영화 섹션 백엔드 이동 + 랜덤 셔플

---

## 변경 파일
| 파일 | 변경 |
|------|------|
| `backend/app/api/v1/recommendations.py` | korean_popular_row 추가 (Top 100 → sample 50 + shuffle + dedup) |
| `frontend/app/page.tsx` | getMovies() 별도 호출 제거, rows에서 통합 렌더링 |

## 핵심 변경
- 한국 인기 영화를 `recommendations.py`에서 인기/높은평점과 동일한 랜덤 셔플 패턴으로 처리
- `production_countries_ko ILIKE '%대한민국%'` 필터 (weighted_score 필터 제거 — 한국 영화는 미계산)
- `popularity DESC, vote_average DESC` 정렬 → Top 100 풀 → `random.sample(50)` + `random.shuffle()`
- `deduplicate_section`으로 인기 영화와 중복 제거
- 프론트: 별도 API 호출 제거, `React.Fragment` wrapper 제거, `getSectionFromTitle`에 "korean_popular" 추가

## 검증 결과
- 3회 호출 시 한국 인기 영화 구성/순서 **매번 다름** ✅
- 4개 섹션 간 중복: **0건** ✅ (인기 vs 한국 vs 높은평점 vs 날씨 모두 겹침 없음)
- 한국 인기 영화 50편 정상 반환 ✅

## 커밋
- `9504363` feat: move Korean popular movies to recommendations with random sampling
- `8f2b155` fix: remove weighted_score filter for Korean movies (not computed for KR)

---
---

# 2026-03-13: 인기/높은평점 고정 섹션 다양성 조사

---

## 조사 결과

### 1. 백엔드 로직 현황

**인기 영화** (`recommendations.py:264-281`):
- `weighted_score >= 6.0` 필터 → `popularity DESC, weighted_score DESC` 정렬 → Top 100 풀
- `random.sample(pool, 50)` → `random.shuffle()` → 50편 반환
- **이미 랜덤 요소가 있음**: Top 100에서 50편을 무작위 추출 + 셔플

**높은 평점 영화** (`recommendations.py:283-298`):
- `weighted_score >= 6.0, vote_count >= 100` → `weighted_score DESC, vote_average DESC` → Top 100 풀
- 동일하게 `random.sample(pool, 50)` → `random.shuffle()` → 50편 반환
- **이미 랜덤 요소가 있음**

**한국 인기 영화** (`page.tsx:122`, `movies.py:109`):
- 프론트엔드에서 `getMovies({ country: "대한민국", sort_by: "popularity", page_size: 40 })` 직접 호출
- **movies.py의 GET /movies 엔드포인트**: `popularity DESC` 고정 정렬, 랜덤 요소 없음
- **캐시 없음** — 하지만 DB 순서가 고정이므로 매번 동일 결과

**Redis 캐시**: 3개 섹션 모두 Redis 캐시 없음. 매 요청마다 DB 조회.

### 2. "항상 동일" 증상의 원인

| 섹션 | 백엔드 랜덤 | 프론트 캐시 | 동일하게 보이는 이유 |
|------|------------|------------|---------------------|
| 인기 영화 | ✅ 100→50 랜덤 | ✅ `cachedKey` | **프론트 캐시 히트** — 같은 key면 API 재호출 안 함 |
| 높은 평점 | ✅ 100→50 랜덤 | ✅ `cachedKey` | 동일 |
| 한국 인기 | ❌ 고정 정렬 | ❌ (일회성) | **DB 순서가 고정** — 랜덤 요소 없음 |

**핵심**: 인기/높은평점은 백엔드에서 이미 셔플하고 있으나, 프론트엔드의 module-level 캐시(`page.tsx:38-40`)가 동일 세션 내에서 API를 재호출하지 않아 사용자가 "항상 같다"고 느낌. 페이지를 완전히 새로고침(F5)하면 다른 영화가 나옴.

### 3. 개선 방안 평가

| 방안 | 코드 변경량 | 시연 임팩트 | 추천 |
|------|-----------|-----------|------|
| **(a) 시간대별 시드 셔플** | 중 (백엔드) | 낮 (시간대 안 바뀌면 동일) | ❌ |
| **(b) 상위 100→50 랜덤** | 0 (이미 구현됨) | - | 이미 있음 |
| **(c) 인기도+랜덤 가산점** | 중 (백엔드) | 중 | △ |
| **(d) 현재 유지** | 0 | - | **✅ 추천** |

### 4. 결론 및 추천: **(d) 현재 유지**

**이유:**
1. 인기/높은평점 섹션은 **이미 랜덤 셔플**이 구현되어 있음 (100→50 sample + shuffle)
2. "동일하게 보이는" 원인은 프론트 캐시 — 이는 **의도된 동작** (back navigation 시 로딩 방지)
3. F5 새로고침 or 날씨/기분 변경 시 캐시 키가 달라져 API 재호출 → 다른 영화 표시
4. 한국 인기 영화만 고정 정렬이지만, 이 섹션은 "인기 순위"이므로 **고정이 자연스러움**
5. 시연 시에는 날씨/기분/MBTI 변경으로 충분한 변화를 보여줄 수 있음 (hybrid_row + 개별 섹션)

**추가 수정이 필요하다면**: 한국 인기 영화에도 Top 60 → 40 sample + shuffle을 적용하는 것이 가장 간단 (movies.py가 아닌 recommendations.py에서 처리 필요). 하지만 우선순위는 낮음.

---
---

# 2026-03-13: hybrid_row 품질 긴급 수정 — control 로직 강제 + mood 매핑 + MBTI override

---

## 변경 파일
| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/api/v1/recommendations.py` | hybrid_row를 항상 control 경로로 강제 (Two-Tower/LGBM 비활성화), MBTI 쿼리 override 허용 |
| `backend/app/services/reranker.py` | 프론트엔드 mood → reranker mood vocabulary 매핑 추가 (8종→6종) |
| `frontend/app/page.tsx` | 로그인 시에도 user.mbti를 쿼리 파라미터로 전달 |

## 핵심 변경

### 수정 1: hybrid_row control 경로 강제
- Two-Tower/LGBM 경로는 후보 200편이 weather/mood 무관하게 고정 → 컨텍스트 변경에 둔감
- 모든 A/B 그룹에서 hybrid_row는 control 로직 사용: DB 스캔 → 5축 가중합산
- 가중치: MBTI 20% + Weather 15% + Mood 25% + Personal 15% + CF 25%
- experiment_group 자체는 유지 (추천 로그 분석용)

### 수정 2: Reranker mood 매핑
```
relaxed→calm, tense→excited, excited→excited, emotional→emotional
imaginative→happy, light→happy, gloomy→sad, stifled→tired
```
나중에 test_a 복원 시 mood feature가 정상 인식됨.

### 수정 3: MBTI 쿼리 override
- 기존: 로그인 시 무조건 `current_user.mbti` 사용 (쿼리 무시)
- 수정: 쿼리 파라미터 우선, 없으면 user.mbti fallback
- 프론트엔드도 로그인 시 `user.mbti`를 쿼리 파라미터로 전달

## 검증 결과 (test_b 그룹 사용자, 배포 후)

| 시나리오 | Top 10 Overlap | 결과 |
|----------|---------------|------|
| 날씨 변경 (sunny→rainy) | 3/10 | **크게 변함** (기존 test_b: 9/10) |
| 기분 변경 (relaxed→tense) | 4/10 | **크게 변함** |
| MBTI 변경 (INTJ→ENFP) | 4/10 | **크게 변함** |
| 비로그인 | hybrid_row: None | 정상 |

### 대표 결과 비교

**ENFP + sunny + relaxed** (밝고 모험적):
- 주토피아2 (0.493), 스폰지밥 (0.492), 인사이드아웃2 (0.486), 아바타 (0.477), 모아나2 (0.471)

**INTJ + rainy + tense** (스릴러/미스터리):
- 하우스메이드 (0.548), 나이브스아웃 (0.496), 파이널데스티네이션 (0.496), 웨폰 (0.493)

→ 컨텍스트에 따라 영화 장르/분위기가 확연히 달라짐

## 커밋
- `5826f48` fix: force control algorithm for hybrid_row to ensure context responsiveness

---
---

# 2026-03-13: 맞춤 추천(하이브리드) 섹션 품질 및 갱신 문제 원인 분석

---

## 증상 1: 드롭다운 변경 시 hybrid_row 미갱신

### 근본 원인: **가설 A, B, C, D 모두 해당하지 않음 — 코드는 정상 동작**

라이브 API 검증 결과, **hybrid_row는 파라미터 변경에 정확하게 반응합니다.**

| 조건 | Top 10 영화 ID |
|------|----------------|
| `weather=sunny&mood=relaxed` | 552524, 83533, 1184918, 569094, 519182, 1084242, 1022787, 939243, 1087192, 840464 |
| `weather=rainy&mood=tense` | 1368166, 812583, 574475, 1078605, 950396, 1408208, 425274, 1288072, 1419406, 604079 |
| 파라미터 없음 (MBTI만) | 1368166, 950396, 701387, 812583, 933260, 574475, 425274, 1354700, 1408208, 1272837 |

- sunny+relaxed vs rainy+tense: **겹침 0편** (완전히 다른 결과)
- rainy+tense vs 파라미터 없음: **겹침 6편** (mood/weather 추가 시 결과 변화)

### 상세 검증 결과

| 가설 | 결과 | 근거 |
|------|------|------|
| **A: hybrid_row가 쿼리 파라미터 무시** | ❌ 해당 안함 | `recommendations.py:200-204` — weather, mood, mbti 모두 `calculate_hybrid_scores()`에 전달 |
| **B: CF/Personal이 결과 지배** | ⚠️ **그룹별 다름** | control: 컨텍스트 60% / test_b: 컨텍스트 25% (아래 상세) |
| **C: 프론트 캐시가 변경 미반영** | ❌ 해당 안함 | `page.tsx:136` 캐시 키에 `weather.condition`, `mood`, `effectiveMBTI` 포함. 의존성 배열도 완전함 |
| **D: Redis 서버 캐시** | ❌ 해당 안함 | hybrid_row에 Redis 캐싱 없음. 매 요청마다 계산 |

### 파라미터 전달 경로 확인

```
Frontend Header 드롭다운 변경
  → useMoodStore.setMood() / useWeather.setManualWeather() / updateMBTI()
  → page.tsx useEffect 의존성 트리거 [weather, mood, user?.mbti, guestMBTI]
  → 캐시 키 변경 → getHomeRecommendations(weather.condition, mood, mbtiParam)
  → Backend GET /recommendations?weather=X&mood=Y
  → calculate_hybrid_scores(db, movies, mbti, weather, ..., mood, experiment_group)
  → 5축 가중합산 → hybrid_row 반환
```

모든 단계에서 파라미터가 정상 전달됩니다.

### 유일한 잠재 이슈: test_b 그룹의 CF 지배 효과

**test_b 그룹** (사용자의 1/3)에서는 CF 가중치가 70%로, 날씨/기분/MBTI를 변경해도 결과 변화가 **미미**합니다:

| 그룹 | 컨텍스트 비중 (mbti+weather+mood) | CF+Personal 비중 | 드롭다운 변경 시 체감 |
|------|----------------------------------|-------------------|---------------------|
| **control** | 60% (with mood) / 45% (no mood) | 40% / 55% | **크게 변함** |
| **test_a** | 37% / 30% | 63% / 70% | 중간 변화 |
| **test_b** | 25% / 18% | 75% / 82% | **거의 안 변함** |

**만약 보고자가 test_b 그룹에 배정된 사용자라면, "영화가 안 바뀐다"는 체감이 맞습니다.**

---

## 증상 2: hybrid_row 영화 품질 낮음

### 근본 원인: 복합적

#### 1. Cold-start 사용자의 축 공백
평점/찜 이력이 없으면:
- `personal_score = 0` (장르 매칭, 유사 영화 보너스 모두 0)
- `cf_score ≈ 0.3~0.5` (SVD가 기본값 근처 예측)

→ 5축 중 2축(personal, CF)이 약하므로, **점수 차이가 좁아져서** 상위 결과의 차별성이 낮아짐

#### 2. 개별 섹션과의 차이

| 섹션 | 스코어링 방식 | 특화도 |
|------|--------------|--------|
| 날씨 섹션 | `weather_scores[condition]` 단일 축 정렬 | ✅ 해당 날씨에 최적화된 영화만 |
| 기분 섹션 | `emotion_tags[emotion]` 단일 축 정렬 | ✅ 해당 감정에 최적화된 영화만 |
| MBTI 섹션 | `mbti_scores[type]` 단일 축 정렬 | ✅ 해당 MBTI에 최적화된 영화만 |
| **hybrid_row** | 5축 가중합산 | ⚠️ **모든 축에서 "중간" 점수인 영화가 상위에** |

단일 축 섹션은 해당 축에서 0.9+ 점수인 영화를 선별.
hybrid_row는 여러 축의 합산이므로, **각 축에서는 0.6~0.7이지만 합산이 높은 영화**가 선정됨.
→ "날씨엔 괜찮고, MBTI에도 괜찮지만, 둘 다 딱히 최적은 아닌" 영화가 나올 수 있음.

#### 3. 점수 분해 예시 (하우스메이드, rainy+tense+INTJ, control 그룹)

```
가중치:  mbti=0.20  weather=0.15  mood=0.25  personal=0.15  cf=0.25
점수:    ≈0.70      ≈0.70         ≈0.70      0.00           ≈0.50

기여:    0.14       0.105         0.175      0.00           0.125
합산:    0.545
× quality_factor(≈1.0): 0.548 ✓
```

personal=0 (cold start), cf=0.5 (약한 신호) → 전체 점수의 40%가 약한 축에서 나옴.
→ **활발한 사용자일수록 hybrid_row 품질이 향상되는 구조**

---

## A/B 그룹 배정 현황

```
user_id= 1: control    user_id= 7: test_a     user_id=13: test_b
user_id= 2: control    user_id= 8: control    user_id=14: test_a
user_id= 3: test_b     user_id= 9: test_b     user_id=15: control
user_id= 4: control    user_id=10: control    user_id=16: test_b
user_id= 5: test_b     user_id=11: test_a     user_id=17: test_a
user_id= 6: control    user_id=12: control    user_id=18: test_b
```

확인 필요: **시연 계정의 user_id → experiment_group 확인**

---

## 수정 제안 (우선순위 순)

### 1. [가장 임팩트 큰] 시연용 A/B 그룹 고정
- 시연 계정이 test_b(CF 70%)에 배정되어 있다면, 드롭다운 변경이 거의 무의미
- **시연 시 control 그룹 사용** 권장 (컨텍스트 60% 반영)
- 또는 시연 계정의 `experiment_group`을 DB에서 직접 `control`로 설정

### 2. [차선] 활성 사용자에서 테스트
- cold-start(평점 0편) 사용자는 personal=0, CF=약함 → hybrid_row 차별성 낮음
- **최소 10편 이상 평점 부여한 계정**에서 시연해야 hybrid_row 효과 극대화

### 3. [장기 개선] 가중치 최적화
- test_b의 CF 70%는 너무 공격적 — 컨텍스트 변경 체감이 사라짐
- 제안: test_b의 CF를 50%로 하향 (mbti=0.12, weather=0.10, mood=0.15, personal=0.13, cf=0.50)
- 또는 "컨텍스트 변경 감지 시" 가중치를 동적으로 조정하는 로직 추가

### 4. [장기 개선] hybrid_row에 컨텍스트 부스팅 적용
- 현재: 순수 가중합산만 사용
- 개선: 사용자가 방금 변경한 축(날씨/기분)에 일시적 부스트(+0.10~0.15) 적용
- 이렇게 하면 드롭다운 변경 시 즉각적인 결과 변화를 체감할 수 있음

---

## 프로덕션 상태 확인

| 항목 | 상태 |
|------|------|
| CF(SVD) 모델 | ✅ loaded |
| Two-Tower | ✅ loaded |
| Reranker(LGBM) | ✅ loaded |
| Redis | ✅ connected |
| DB | ✅ connected |

---
---

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
