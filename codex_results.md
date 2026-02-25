# RecFlix A/B 테스트 + 추천 개인화 강화 사전 조사 보고서

**분석일**: 2026-02-25
**범위**: 코드 수정 없이 분석만

---

## 1. A/B 테스트 현황

### 1-1. experiment_group 배정 방식

**현재 상태:**
- `backend/app/api/v1/auth.py:39` — 3개 그룹 정의: `["control", "test_a", "test_b"]`
- `auth.py:102, 331, 415` — 회원가입(이메일/카카오/구글) 시 `random.choice()`로 **균등 랜덤 배정** (1/3씩)
- `backend/app/models/user.py:23` — `experiment_group` 컬럼: `String(10)`, `default="control"`, `server_default="control"`

**문제/갭:**
- `random.choice()`는 **비균등 분포** 가능 (소규모 사용자에서 편향 발생)
- 배정 후 **변경 불가** (API 없음), 재배정 로직 없음
- 기존 사용자(마이그레이션 전)는 전부 `control`에 고정됨 (server_default)
- 그룹 비율 조절 불가 (항상 1:1:1 고정)

**개선 방안:**
- 가중치 기반 배정 (예: control 60%, test_a 20%, test_b 20%)
- 관리자 API로 그룹 재배정 가능하게
- 실험 ID/실험 기간 개념 도입

**난이도:** 낮음

---

### 1-2. A/B 분기가 추천에 만드는 차이

**현재 상태:**
- `recommendation_engine.py:55-65` — `get_weights_for_group()` 함수에서 그룹별 가중치 분기
- 분기는 **하이브리드 스코어링 가중치**에만 적용됨
- `recommendations.py:74, 259` — `calculate_hybrid_scores()`에 `experiment_group` 전달

**각 그룹의 가중치 설정값** (`recommendation_constants.py`):

| 요소 | control (mood O) | control (mood X) | test_a (mood O) | test_a (mood X) | test_b (mood O) | test_b (mood X) |
|------|:-:|:-:|:-:|:-:|:-:|:-:|
| MBTI | 0.25 | 0.35 | 0.12 | 0.17 | 0.08 | 0.10 |
| Weather | 0.20 | 0.25 | 0.10 | 0.13 | 0.07 | 0.08 |
| Mood | 0.30 | - | 0.15 | - | 0.10 | - |
| Personal | 0.25 | 0.40 | 0.13 | 0.20 | 0.05 | 0.12 |
| CF | 0.00* | 0.00* | 0.50 | 0.50 | 0.70 | 0.70 |

\* control 그룹은 CF 모델 존재 시 별도 가중치 적용 (CF O: mbti=0.20, weather=0.15, mood=0.25, personal=0.15, cf=0.25)

**실험 설계 의도:**
- `control`: 기존 Rule-based 위주 (CF 모델 있으면 25%)
- `test_a`: Rule 50% + CF 50% (CF 의존도 중간)
- `test_b`: Rule 30% + CF 70% (CF 의존도 높음)

**문제/갭:**
- A/B 분기가 **하이브리드 Row에만** 적용됨. MBTI Row, 날씨 Row, 기분 Row, 인기 Row, 평점 Row는 **그룹 구분 없이 동일** (`get_movies_by_score()` 사용)
- CF 모델이 **item_bias만** 사용하므로 (`recommendation_cf.py:46-64`), test_a/test_b의 높은 CF 가중치가 실제로는 "MovieLens 평균 평점이 높은 영화" 편향을 일으킴 → 진정한 개인화가 아님
- 다양성 후처리(genre cap, freshness)는 **그룹 구분 없이 동일** 적용

**개선 방안:**
- CF를 user-level 협업 필터링으로 확장 (RecFlix 사용자 평점 데이터 활용)
- A/B 분기를 다양성 정책에도 적용 (예: test_a는 더 높은 serendipity)
- 비하이브리드 섹션에도 그룹별 차이 도입

**난이도:** CF 확장 = 높음, 다양성 분기 = 중간

---

### 1-3. ab-report API 반환 메트릭

**현재 상태** (`events.py:173-301`):

`GET /events/ab-report?days=7` 반환 구조 (`ABReport`):
```
{
  period: "7d",
  groups: {
    "control": {
      users: int,                    // 고유 사용자 수
      total_clicks: int,             // 총 클릭
      total_impressions: int,        // 총 노출
      ctr: float,                    // 클릭률 (clicks/impressions)
      avg_detail_duration_ms: float, // 평균 상세 체류 시간
      rating_conversion: float,     // 평점 전환율 (ratings/detail_views)
      favorite_conversion: float,   // 찜 전환율 (favorites/detail_views)
      by_section: {                  // 섹션별 CTR
        "personal": { clicks, impressions, ctr },
        "popular": { clicks, impressions, ctr },
        ...
      }
    },
    "test_a": { ... },
    "test_b": { ... }
  },
  winner: "control",                // CTR 최고 그룹
  confidence_note: "통계적 유의성 검증은 최소 1000명 이상, 2주 이상 데이터 필요"
}
```

**문제/갭:**
- **통계적 유의성 검증 없음** — winner는 단순 CTR 비교, p-value/신뢰구간 없음
- 평균 평점 분포 미포함
- 추천 다양성(장르 분포) 메트릭 미포함
- 재방문율, 세션당 이벤트 수 미포함

**개선 방안:**
- 카이제곱 검정 또는 Z-test로 유의성 판정
- 그룹별 평균 평점, 장르 다양성 지표 추가
- "추천 영화에 대한" 평점 vs "직접 검색한 영화에 대한" 평점 비교

**난이도:** 중간

---

### 1-4. 이벤트 종류 10가지 목록

**백엔드 허용 이벤트** (`schemas/user_event.py:6-17`):

| # | event_type | 프론트 구현 | 비고 |
|---|-----------|:-:|------|
| 1 | `movie_click` | O | MovieCard, HybridMovieCard |
| 2 | `movie_detail_view` | O | 영화 상세 페이지 진입 |
| 3 | `movie_detail_leave` | O | 상세 페이지 이탈 (duration_ms 포함) |
| 4 | `recommendation_impression` | O | MovieRow, HybridMovieRow (IntersectionObserver) |
| 5 | `search` | O | SearchAutocomplete (query, result_count) |
| 6 | `search_click` | O | SearchResults (query, position) |
| 7 | `rating` | O | 영화 상세 페이지 |
| 8 | `favorite_add` | O | 영화 상세 페이지 |
| 9 | `favorite_remove` | O | 영화 상세 페이지 |
| 10 | `not_interested` | **X** | 스키마에만 존재, 프론트 미구현 |

---

## 2. 이벤트 트래킹 실효성

### 2-1. 프론트엔드 이벤트 전송 지점

| 이벤트 | 파일 | 트리거 | 메타데이터 |
|--------|------|--------|-----------|
| `movie_click` | `MovieCard.tsx` | 포스터 클릭 | `{source, section, position}` |
| `movie_click` | `HybridMovieCard.tsx` | 포스터 클릭 | `{source, section, position}` |
| `recommendation_impression` | `MovieRow.tsx` → `useImpressionTracker` | 뷰포트 30%+ 진입 | `{section, movie_ids[0:10], count}` |
| `recommendation_impression` | `HybridMovieRow.tsx` → `useImpressionTracker` | 뷰포트 30%+ 진입 | `{section, movie_ids[0:10], count}` |
| `movie_detail_view` | `movies/[id]/page.tsx` | 페이지 마운트 | `{referrer}` |
| `movie_detail_leave` | `movies/[id]/page.tsx` | 페이지 언마운트 | `{duration_ms}` |
| `favorite_add/remove` | `movies/[id]/page.tsx` | 찜 버튼 클릭 | `{source: "detail_page"}` |
| `rating` | `movies/[id]/page.tsx` | 별점 클릭 | `{rating, source: "detail_page"}` |
| `search` | `SearchAutocomplete.tsx` | 검색 결과 로드 | `{query, result_count, is_semantic}` |
| `search_click` | `SearchResults.tsx` | 검색 결과 클릭 | `{query, position}` |

### 2-2. 누락된 이벤트/컨텍스트

**현재 상태 → 문제/갭:**

| 누락 항목 | 설명 | 영향 |
|-----------|------|------|
| `not_interested` | 스키마에만 정의, UI/프론트 미구현 | "관심 없음" 피드백 수집 불가 |
| 모달에서의 이벤트 | `MovieModal.tsx`에서 찜/평점 이벤트 없음 | 모달 경유 전환 추적 불가 |
| `movie_click`에 experiment_group 미포함 | 메타데이터에 사용자 그룹 정보 없음 (서버에서 주입) | 서버에서 주입하므로 비로그인 사용자는 unknown |
| impression에 순서 정보 없음 | `movie_ids[0:10]`만 전송, 전체 순위 미포함 | 어떤 위치의 영화가 클릭되었는지 분석 제한적 |
| 추천 알고리즘 버전 미포함 | 이벤트에 실험 가중치/알고리즘 정보 없음 | 가중치 변경 전후 비교 어려움 |
| 홈 페이지 체류 시간 | 홈 페이지 전체 세션 시간 미추적 | 인게이지먼트 분석 제한 |
| 스크롤 깊이 | 사용자가 몇 번째 Row까지 봤는지 미추적 | 섹션 배치 최적화 불가 |

**개선 방안:**
1. `MovieModal`에 찜/평점 이벤트 추가 (`source: "modal"`)
2. `not_interested` 버튼 UI 추가 (카드 hover 시 X 버튼)
3. `movie_click` 메타데이터에 `hybrid_score`, `recommendation_tags` 추가 → 클릭된 영화의 추천 점수 추적
4. impression에 `algorithm_version` 또는 `weights` 메타데이터 추가

**난이도:** 낮음~중간

---

## 3. A/B 테스트로 측정 가능한 지표

### 현재 측정 가능한 지표

| 지표 | 측정 가능 | 근거 |
|------|:-:|------|
| **CTR** (impression → click) | O | `recommendation_impression` + `movie_click` (section별) |
| **상세 조회율** (click → detail_view) | **△** | `movie_click`과 `movie_detail_view`가 별도 이벤트이나, 동일 movie_id로 연결 가능. 단, 직접 URL 접근 시 click 없이 detail_view 발생 |
| **전환율** (detail_view → rating/favorite) | O | `events.py:259-260`에서 계산 |
| **평균 평점** | **X** | 이벤트 메타데이터에 rating 값 있으나, ab-report에서 **집계하지 않음** |
| **체류 시간** | O | `movie_detail_leave`의 `duration_ms` → `avg_detail_duration_ms` |
| **다양성 지표** | **X** | 추천 결과의 장르 분포 메트릭 없음 |
| **섹션별 CTR** | O | `by_section` 필드로 personal/popular/mbti/weather/mood 구분 |

### 현재 측정 불가능한 지표 (추가 필요)

| 지표 | 필요한 작업 | 난이도 |
|------|-----------|--------|
| 그룹별 평균 평점 | ab-report에 rating 이벤트의 평균 score 집계 추가 | 낮음 |
| 추천 다양성 | impression 이벤트에 장르 정보 포함 또는 별도 집계 | 중간 |
| 재방문율 | 일별 고유 사용자 추적 | 낮음 |
| 세션당 이벤트 수 | session_id 기반 집계 | 낮음 |
| 통계적 유의성 (p-value) | scipy.stats 또는 직접 구현 | 중간 |

---

## 4. 현재 개인화 수준

### 4-1. 로그인 vs 비로그인 추천 차이

**현재 상태** (`recommendations.py:46-228`):

| 항목 | 로그인 | 비로그인 |
|------|-------|---------|
| **하이브리드 Row** | O (MBTI+날씨+기분+취향+CF) | X (미표시) |
| **MBTI Row** | O (user.mbti 있을 때) | X |
| **날씨 Row** | O | O (동일) |
| **기분 Row** | O | O (동일) |
| **인기 Row** | 3번째 | 1번째 (최상단) |
| **평점 Row** | 4번째 | 2번째 |
| **섹션 순서** | MBTI → 날씨 → 기분 → 인기 → 평점 | 인기 → 평점 → 날씨 → 기분 |
| **개인취향 반영** | 찜+평점 기반 장르 가중치 | X |
| **찜한 영화 제외** | O | X |
| **유사 영화 보너스** | O | X |
| **CF 점수** | 그룹별 가중치 | X |

**문제/갭:**
- 비로그인 사용자에게는 날씨/기분 외에 **개인화 요소 전무**
- 비로그인도 검색 이력 기반 추천이 가능하지만 미구현

**개선 방안:**
- 세션 기반 취향 추적 (클릭한 영화의 장르 집계)
- 비로그인 사용자에게 "이런 영화에 관심이 있으시군요" 섹션 추가

**난이도:** 중간

---

### 4-2. MBTI별 추천 차이 정도

**현재 상태:**
- `movies.mbti_scores` JSONB에 16개 MBTI 유형별 점수 저장 (0.0~1.0)
- 하이브리드 점수에서 MBTI 가중치: control 25% (mood O), 35% (mood X)
- MBTI Row는 `get_movies_by_score(db, "mbti_scores", mbti)`로 해당 유형 점수 TOP 영화 반환

**문제/갭:**
- `mbti_scores`가 **Rule-based로 생성**되어 16개 유형 간 차이가 제한적
- MBTI 점수가 높은 영화가 유형 간 상당수 겹칠 가능성 (검증 필요)
- MBTI 미설정 사용자는 MBTI Row 자체가 사라짐

**난이도:** 검증=낮음, 개선=중간

---

### 4-3. personal_score의 실제 영향력

**현재 상태** (`recommendation_engine.py:355-376`):
```
personal_score 구성:
- 장르 매칭: top 3 장르와 겹치는 장르 x 0.3 (최대 0.9)
- 유사 영화 보너스: +0.4
- 합산 최대: ~1.3 (정규화 전)
```

**문제/갭:**
- **찜/평점 데이터가 적을 때** (`< 5건`): 온보딩 선호 장르(`preferred_genres`)로 폴백 (`recommendation_engine.py:248-261`)
- 그러나 온보딩 장르는 **한국어 → 영어 매핑** 후 `genre_counts`에 **1점**만 추가 → 다른 요소 대비 영향력 미미
- 콜드스타트 사용자의 personal_score는 사실상 **0에 가까움**
- personal 가중치가 control 기준 25%인데, 실제 personal_score가 0이면 해당 25%가 **낭비**됨

**개선 방안:**
- 콜드스타트 시 온보딩 장르 가중치 상향 (1 → 3 이상)
- 콜드스타트 시 가중치 재분배 (personal 빈 슬롯을 MBTI/날씨에 재배분)
- 클릭 이벤트 기반 실시간 취향 업데이트

**난이도:** 낮음 (가중치 조정) ~ 중간 (클릭 기반)

---

### 4-4. CF score의 실제 기여도

**현재 상태** (`recommendation_cf.py`):
- MovieLens SVD 모델에서 `global_mean + item_bias` 사용
- **user-level 개인화 없음** — RecFlix 사용자 평점을 학습에 사용하지 않음
- `predict_cf_score()`: 모든 사용자에게 **동일한** 영화별 점수 반환
- 정규화: `(score - 0.5) / 4.5` → 0~1

**문제/갭:**
- CF가 "협업 필터링"이라고 하지만 실질적으로 **MovieLens 전체 평균 품질 점수** → `weighted_score`와 기능 중복
- test_a(CF 50%), test_b(CF 70%)는 "MovieLens에서 인기 있는 영화"에 편향되는 효과
- **진정한 의미의 협업 필터링이 아님** — user-to-user 또는 item-to-item 유사성 미활용

**개선 방안:**
1. **단기**: RecFlix 사용자 평점 데이터로 item-item CF 학습 (ratings 테이블 활용)
2. **중기**: implicit feedback (클릭, 체류시간) 기반 ALS 모델
3. **장기**: 하이브리드 딥러닝 (Neural CF + content-based features)

**난이도:** 높음

---

## 5. 강화 가능한 영역

### 5-1. 실험 설정 동적 변경

**현재 상태:**
- 가중치가 `recommendation_constants.py`에 **하드코딩**
- 변경 시 코드 수정 → 배포 필요
- 실험 그룹 정의도 `auth.py:39`에 하드코딩

**문제/갭:**
- 실험 가중치 조정에 매번 배포 필요
- 실험 시작/종료 기간 관리 없음
- 여러 실험을 동시에 돌리는 구조 아님

**개선 방안:**
- 환경변수 또는 Redis에 실험 설정 저장
- 관리자 API: `PUT /admin/experiments/{id}` (가중치, 그룹 비율, 기간)
- `experiments` 테이블 도입 (id, name, weights, start_date, end_date, status)

**난이도:** 중간

---

### 5-2. 새 실험 추가 용이성

**현재 상태:**
- `get_weights_for_group()` 함수에 `if/elif` 분기로 추가
- `recommendation_constants.py`에 `WEIGHTS_HYBRID_C` 등 추가
- `auth.py`의 `EXPERIMENT_GROUPS` 리스트에 추가

**문제/갭:**
- 3곳을 동시에 수정해야 함 (상수 + 엔진 + auth)
- 그룹 이름 오타 시 `control`로 폴백 (에러 감지 어려움)
- 종료된 실험의 그룹이 계속 배정됨

**개선 방안:**
- `EXPERIMENT_CONFIG` 딕셔너리로 통합:
  ```python
  EXPERIMENT_CONFIG = {
      "control": {"weights_mood": {...}, "weights_no_mood": {...}},
      "test_a": {"weights_mood": {...}, "weights_no_mood": {...}},
  }
  ```
- `get_weights_for_group()`에서 딕셔너리 조회로 통일

**난이도:** 낮음

---

### 5-3. 프론트에서 실험 그룹별 UI 차이

**현재 상태:**
- 프론트엔드는 사용자의 `experiment_group`을 **전혀 모름**
- `getCurrentUser()` API 응답에 `experiment_group` 포함 여부 미확인
- UI 차이 없음 (모든 그룹 동일한 레이아웃)

**문제/갭:**
- 프론트에서 그룹별 UI 실험 불가 (예: test_b에게만 "AI 추천" 배지 표시)
- 추천 응답에 사용된 가중치/그룹 정보 미포함

**개선 방안:**
- `GET /users/me` 응답에 `experiment_group` 필드 노출
- 추천 API 응답에 `experiment_group` 메타데이터 추가
- 프론트에서 `user.experiment_group`에 따른 조건부 렌더링

**난이도:** 낮음

---

## 구현 우선순위 제안

### Phase A: 즉시 적용 (1일) — 분석 정확도 향상

| # | 작업 | 영향 | 난이도 |
|---|------|------|--------|
| A1 | **실험 설정 통합** — `EXPERIMENT_CONFIG` 딕셔너리 통합 | 유지보수성 | 낮음 |
| A2 | **ab-report에 평균 평점 추가** | 분석 정확도 | 낮음 |
| A3 | **MovieModal에 찜/평점 이벤트 추가** | 전환 추적 누락 해소 | 낮음 |
| A4 | **콜드스타트 가중치 재분배** — personal=0이면 다른 요소로 재분배 | 신규 사용자 추천 품질 | 낮음 |

### Phase B: 단기 (2-3일) — A/B 테스트 실효성 강화

| # | 작업 | 영향 | 난이도 |
|---|------|------|--------|
| B1 | **통계적 유의성 검증 추가** — Z-test/카이제곱 for CTR | 의사결정 신뢰도 | 중간 |
| B2 | **이벤트 컨텍스트 강화** — algorithm_version, hybrid_score 메타데이터 | 정밀 분석 | 중간 |
| B3 | **프론트에 experiment_group 노출** — 그룹별 UI 실험 기반 마련 | 실험 확장성 | 낮음 |
| B4 | **비로그인 세션 기반 취향 추적** — 클릭 장르 집계 | 비로그인 개인화 | 중간 |

### Phase C: 중기 (1주) — 개인화 본격 강화

| # | 작업 | 영향 | 난이도 |
|---|------|------|--------|
| C1 | **RecFlix 평점 기반 item-item CF** — ratings 테이블로 자체 CF 학습 | 진정한 CF | 높음 |
| C2 | **실험 관리 시스템** — experiments 테이블, 관리자 API, 동적 가중치 | 운영 효율 | 중간 |
| C3 | **not_interested 기능 구현** — 카드 UI + 네거티브 피드백 반영 | 추천 정밀도 | 중간 |
| C4 | **추천 다양성 메트릭** — 장르 분포, HHI 지수 등 | 다양성 모니터링 | 중간 |

### 우선 추천 순서: A1 → A3 → A4 → A2 → B3 → B1 → B2 → B4 → C1 → C2
