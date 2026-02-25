# A/B 테스트 + 추천 개인화 현황 전체 분석

**날짜**: 2026-02-25
**유형**: 조사 전용 (수정 금지)

---

## 1. A/B 그룹 구성

### 1-1. 그룹 정의

**3개 그룹**: `control`, `test_a`, `test_b`
- **근거**: `backend/app/api/v1/auth.py:39` — `EXPERIMENT_GROUPS = ["control", "test_a", "test_b"]`

### 1-2. 그룹 배정 로직

**균등 랜덤 배정** (`random.choice()`, 1/3 확률)
- 이메일 가입: `auth.py:102`
- 카카오 가입: `auth.py:331`
- 구글 가입: `auth.py:415`
- DB 기본값: `"control"` (`models/user.py:23` — `server_default="control"`)
- 기존 사용자(마이그레이션 이전)는 전부 `control`

### 1-3. 그룹별 가중치 설정 (`recommendation_constants.py:11-49`)

**Mood 선택 시 (mood O):**

| 요소 | control | control+CF | test_a | test_b |
|------|:-------:|:----------:|:------:|:------:|
| MBTI | 0.25 | 0.20 | 0.12 | 0.08 |
| Weather | 0.20 | 0.15 | 0.10 | 0.07 |
| Mood | 0.30 | 0.25 | 0.15 | 0.10 |
| Personal | 0.25 | 0.15 | 0.13 | 0.05 |
| CF | 0.00 | 0.25 | 0.50 | 0.70 |
| **합계** | 1.00 | 1.00 | 1.00 | 1.00 |

**Mood 미선택 시 (mood X):**

| 요소 | control | control+CF | test_a | test_b |
|------|:-------:|:----------:|:------:|:------:|
| MBTI | 0.35 | 0.25 | 0.17 | 0.10 |
| Weather | 0.25 | 0.20 | 0.13 | 0.08 |
| Personal | 0.40 | 0.30 | 0.20 | 0.12 |
| CF | 0.00 | 0.25 | 0.50 | 0.70 |

### 1-4. 그룹별 추천 결과 차이 분석

**A/B 분기가 적용되는 곳:**
- `recommendation_engine.py:305` — `get_weights_for_group(experiment_group, use_mood)` 호출
- **하이브리드 Row만** 영향받음 (`recommendations.py:71-75`, `recommendations.py:256-260`)

**A/B 분기가 적용되지 않는 곳 (모든 그룹 동일):**
- MBTI Row: `get_movies_by_score(db, "mbti_scores", mbti)` — `recommendations.py:130`
- 날씨 Row: `get_movies_by_score(db, "weather_scores", weather)` — `recommendations.py:145`
- 기분 Row: `get_movies_by_score(db, "emotion_tags", primary_emotion)` — `recommendations.py:161`
- 인기 Row: `popularity DESC` — `recommendations.py:176-178`
- 평점 Row: `weighted_score DESC` — `recommendations.py:192-194`
- 다양성 후처리: `diversity.py` — 모든 그룹 동일 파이프라인
- 섹션 순서: `recommendations.py:206-221` — 그룹 무관

**실질적 차이:**
- `test_b` (CF 70%)는 MovieLens item_bias에 크게 의존 → 인기 영화 편향
- `control` (CF 0% 또는 25%)는 Rule-based 중심 → MBTI/날씨/기분 반영 높음
- CF가 user-level이 아닌 item_bias만 사용(`recommendation_cf.py:46-64`)하므로, **test_a/test_b 간 차이는 본질적으로 "MovieLens 인기도" 의존도 차이**

---

## 2. 이벤트 트래킹 현황

### 2-1. 정의된 이벤트 10종 (`schemas/user_event.py:6-17`)

| # | event_type | 설명 |
|---|-----------|------|
| 1 | `movie_click` | 영화 카드 클릭 |
| 2 | `movie_detail_view` | 상세 페이지 진입 |
| 3 | `movie_detail_leave` | 상세 페이지 이탈 |
| 4 | `recommendation_impression` | 추천 섹션 노출 |
| 5 | `search` | 검색 실행 |
| 6 | `search_click` | 검색 결과 클릭 |
| 7 | `rating` | 평점 등록 |
| 8 | `favorite_add` | 찜 추가 |
| 9 | `favorite_remove` | 찜 해제 |
| 10 | `not_interested` | 관심 없음 |

### 2-2. 프론트엔드 실제 전송 현황

| 이벤트 | 전송 | 파일:라인 | 트리거 | 메타데이터 |
|--------|:----:|----------|--------|-----------|
| `movie_click` | **O** | `MovieCard.tsx:57-61` | 포스터 클릭 | `{source, section, position}` |
| `movie_click` | **O** | `HybridMovieCard.tsx:69-73` | 포스터 클릭 | `{source, section, position}` |
| `recommendation_impression` | **O** | `MovieRow.tsx:30-34` via hook | 뷰포트 30%+ | `{section, movie_ids[0:10], count}` |
| `recommendation_impression` | **O** | `HybridMovieRow.tsx:38-42` via hook | 뷰포트 30%+ | `{section, movie_ids[0:10], count}` |
| `movie_detail_view` | **O** | `movies/[id]/page.tsx:42-46` | 페이지 마운트 | `{referrer}` |
| `movie_detail_leave` | **O** | `movies/[id]/page.tsx:49-53` | 페이지 언마운트 | `{duration_ms}` |
| `favorite_add` | **O** | `movies/[id]/page.tsx:102-106` | 찜 버튼 | `{source: "detail_page"}` |
| `favorite_remove` | **O** | `movies/[id]/page.tsx:102-106` | 찜 해제 | `{source: "detail_page"}` |
| `rating` | **O** | `movies/[id]/page.tsx:119-123` | 별점 클릭 | `{rating, source: "detail_page"}` |
| `search` | **O** | `SearchAutocomplete.tsx:106-113` | 검색 결과 로드 | `{query, result_count, is_semantic}` |
| `search_click` | **O** | `SearchResults.tsx:137-142` | 결과 클릭 | `{query, position}` |
| `not_interested` | **X** | - | 미구현 | - |

### 2-3. 누락된 이벤트 & 사각지대

| 누락 | 파일:라인 | 설명 | 영향도 |
|------|----------|------|:------:|
| **MovieModal 찜/평점 이벤트 없음** | `MovieModal.tsx:103-127` | `handleFavoriteClick`, `handleRatingClick`에 `trackEvent` 호출 없음 | **높음** |
| **FeaturedBanner 찜 이벤트 없음** | `FeaturedBanner.tsx:120-134` | `handleAddToList`에 `trackEvent` 호출 없음 | **높음** |
| **FeaturedBanner 상세보기 클릭 미추적** | `FeaturedBanner.tsx:236-243` | 상세보기 Link에 click 이벤트 없음 | **중간** |
| **FeaturedBanner 미리보기(모달) 클릭 미추적** | `FeaturedBanner.tsx:245-254` | 모달 열기에 이벤트 없음 | **낮음** |
| **FeaturedBanner 트레일러 클릭 미추적** | `FeaturedBanner.tsx:255-265` | 트레일러 열기에 이벤트 없음 | **낮음** |
| **`not_interested` 미구현** | - | 백엔드만 정의, UI 없음 | **중간** |
| **모달 내 유사 영화 클릭 미추적** | `MovieModal.tsx:307-309` | section 미전달 → `MovieCard`에서 이벤트 발생 안 함 | **중간** |

### 2-4. 이벤트 컨텍스트 포함 여부

| 컨텍스트 | 포함 | 위치 |
|---------|:----:|------|
| **section** (어떤 섹션에서) | **O** | `movie_click`, `recommendation_impression` |
| **position** (몇 번째 카드) | **O** | `movie_click` (index prop) |
| **hybrid_score** (추천 점수) | **X** | 미포함 |
| **recommendation_tags** | **X** | 미포함 |
| **experiment_group** | **서버 주입** | `events.py:35, 67` — 로그인 사용자만 |
| **algorithm_version** | **X** | 미포함 |
| **weather/mood 컨텍스트** | **X** | 미포함 (어떤 날씨/기분에서 클릭했는지 모름) |

### 2-5. 이벤트 전송 메커니즘

- **배치 전송**: 5초마다 자동 flush (`eventTracker.ts:83-85`)
- **페이지 이탈**: Beacon API (`eventTracker.ts:87-97`)
- **세션 ID**: sessionStorage 기반 (`eventTracker.ts:99-107`)
- **인증 토큰**: flush 시 localStorage에서 읽어 Bearer 헤더 추가 (`eventTracker.ts:68-70`)
- **Beacon API 제한**: Beacon은 auth 헤더 미포함 → 로그아웃 상태에서 이탈 시 user_id=null

---

## 3. ab-report API 분석

### 3-1. 계산하는 메트릭 (`events.py:173-301`)

| 메트릭 | 계산 방법 | 근거 라인 |
|--------|----------|----------|
| **users** | 그룹별 `COUNT(DISTINCT user_id)` | `events.py:274-279` |
| **total_clicks** | `movie_click` 이벤트 수 | `events.py:252` |
| **total_impressions** | `recommendation_impression` 이벤트 수 | `events.py:253` |
| **ctr** | clicks / impressions | `events.py:254` |
| **avg_detail_duration_ms** | `movie_detail_leave`의 `duration_ms` 평균 | `events.py:197-208` |
| **rating_conversion** | ratings / detail_views | `events.py:259` |
| **favorite_conversion** | favorites / detail_views | `events.py:260` |
| **by_section** | 섹션별 clicks, impressions, ctr | `events.py:263-271` |
| **winner** | CTR 최고 그룹 이름 | `events.py:292-294` |

### 3-2. 핵심 SQL 쿼리

**그룹별 이벤트 집계** (`events.py:185-195`):
```sql
SELECT COALESCE(metadata->>'experiment_group', 'unknown') AS exp_group,
       event_type, COUNT(*), COUNT(DISTINCT user_id)
FROM user_events WHERE created_at >= :since
GROUP BY exp_group, event_type
```

**그룹별 체류 시간** (`events.py:198-207`):
```sql
SELECT COALESCE(metadata->>'experiment_group', 'unknown'),
       AVG((metadata->>'duration_ms')::float)
FROM user_events
WHERE event_type = 'movie_detail_leave' AND metadata->>'duration_ms' IS NOT NULL
GROUP BY exp_group
```

**그룹별 섹션 CTR** (`events.py:211-222`):
```sql
SELECT exp_group, metadata->>'section', event_type, COUNT(*)
FROM user_events
WHERE event_type IN ('recommendation_impression', 'movie_click')
  AND metadata->>'section' IS NOT NULL
GROUP BY exp_group, section, event_type
```

### 3-3. 반환 데이터 구조 (`schemas/user_event.py:62-79`)

```
ABReport {
  period: str                         // "7d"
  groups: { [group]: ABGroupStats }   // control, test_a, test_b
  winner: str | null                  // CTR 최고 그룹
  confidence_note: str                // 유의성 관련 안내
}

ABGroupStats {
  users: int
  total_clicks: int
  total_impressions: int
  ctr: float
  avg_detail_duration_ms: float | null
  rating_conversion: float
  favorite_conversion: float
  by_section: { [section]: { clicks, impressions, ctr } }
}
```

---

## 4. 측정 가능한 KPI

### 4-1. CTR (impression → click)

**가능 여부**: **O** (현재 측정 가능)
- `recommendation_impression` → `movie_click` 매칭 가능
- 섹션별 분리 가능 (personal, popular, top_rated, mbti, weather, mood)
- ab-report API에서 `ctr`, `by_section` 반환

**제약:**
- impression은 섹션 단위 (첫 노출 1회), click은 개별 영화 단위 → CTR이 100% 초과 가능
- `movie_ids[0:10]`만 전송 → 11번째 이후 영화의 노출 여부 불확실

### 4-2. 전환율 (click → rating/favorite)

**가능 여부**: **O** (현재 측정 가능)
- `rating_conversion = ratings / detail_views`
- `favorite_conversion = favorites / detail_views`
- ab-report에서 그룹별 계산

**제약:**
- click → detail_view가 1:1이 아님 (직접 URL 접근, 검색 경유 등)
- **MovieModal에서의 찜/평점은 추적 안 됨** → 전환율 과소 측정

### 4-3. 추천 수용률 (추천 영화 중 높은 평점 비율)

**가능 여부**: **X** (현재 측정 불가)
- rating 이벤트에 `{rating, source: "detail_page"}` 포함
- 그러나 "추천에서 온 영화"인지 "검색에서 온 영화"인지 구분 불가
- `movie_detail_view`에 `{referrer}` 있지만 어느 추천 섹션인지 미포함
- **필요**: click 이벤트의 `section` 정보를 detail_view까지 전파하거나, rating 이벤트에 `source_section` 추가

### 4-4. 다양성 (장르 분포)

**가능 여부**: **X** (현재 측정 불가)
- impression 이벤트에 `movie_ids`만 포함, 장르 정보 없음
- 서버 사이드에서 추천 결과의 장르 분포를 로깅하지 않음
- **필요**: 추천 API 응답 시 장르 분포 메타데이터 로깅 또는 impression에 장르 정보 포함

---

## 5. 개인화 수준

### 5-1. 비로그인 vs 로그인 차이 (`recommendations.py:46-228`)

| 기능 | 비로그인 | 로그인 |
|------|---------|-------|
| 하이브리드 맞춤 Row | X | O (MBTI+날씨+기분+취향+CF) |
| MBTI Row | X | O (mbti 설정 시) |
| 날씨 Row | O | O |
| 기분 Row | O (기본: relaxed) | O |
| 인기 Row | **1순위** | 3순위 |
| 평점 Row | **2순위** | 4순위 |
| 찜한 영화 제외 | X | O |
| 유사 영화 보너스 | X | O |
| personal_score | X | O |
| CF score | X | O (그룹별) |

### 5-2. MBTI별 차이 정도

- `mbti_scores` JSONB에 16 유형별 점수 (0.0~1.0) 저장
- Rule-based 생성 → 유형 간 차이가 제한적일 수 있음
- MBTI Row: 해당 유형 점수 TOP 영화 반환 (`get_movies_by_score`)
- 하이브리드 Row: MBTI 가중치 control 25% / test_b 8%
- **MBTI 미설정 시**: MBTI Row 미표시, 하이브리드 Row에서 `mbti_score=0` → 해당 가중치 낭비

### 5-3. personal_score 영향력 (`recommendation_engine.py:355-376`)

**점수 구성:**
- 장르 매칭: top 3 장르 × 0.3 (최대 0.9)
- 유사 영화: +0.4
- 이론적 최대: ~1.3

**콜드스타트 (상호작용 < 5건):**
- `preferred_genres`로 폴백 (`recommendation_engine.py:248-261`)
- 온보딩 장르 → Genre 테이블 매핑 → `genre_counts`에 **1점만** 추가
- 나머지 장르(찜/평점)는 1~2점씩 → 온보딩 장르가 **동등 이하**
- **결과**: personal_score ≈ 0.3 (장르 1개 매칭) → 가중치 25% 적용 시 실질 기여 ~0.075

**활발한 사용자 (찜 10+, 평점 5+):**
- genre_counts가 풍부 → personal_score ≈ 0.6~0.9
- 유사 영화 보너스까지 → 최대 1.3
- **실질 기여**: 0.25 * 0.9 = 0.225 (전체 점수의 ~22%)

### 5-4. preferred_genres 반영 상태 (Phase 46 추가)

**현재 구현** (`recommendation_engine.py:248-261`):
```python
# 상호작용 < 5건일 때만 발동
if total_interactions < 5 and user.preferred_genres:
    preferred = json.loads(user.preferred_genres)  # ["액션","SF"]
    genre_rows = db.query(Genre.name, Genre.name_ko).filter(
        Genre.name_ko.in_(preferred)
    ).all()
    for eng_name, _ko_name in genre_rows:
        genre_counts.setdefault(eng_name, 0)
        genre_counts[eng_name] += 1  # 1점만 추가
```

**문제:**
- 가중치가 1점으로 너무 낮음 (찜은 1점, 높은 평점은 2점인데 온보딩도 1점)
- `total_interactions >= 5`이면 온보딩 장르 완전 무시
- 온보딩에서 장르를 5개 선택해도 각 1점 → 찜 1편 + 고평점 1편이면 이미 추월

---

## 6. 갭 분석

### 6-1. A/B 테스트 운영 가능 수준 평가

| 항목 | 수준 | 설명 |
|------|:----:|------|
| **그룹 배정** | C | `random.choice()` 사용, 소규모에서 비균등 분포 가능 |
| **그룹별 추천 차이** | B | 하이브리드 Row에서만 차이, 5개 섹션은 동일 |
| **이벤트 수집** | B+ | 9/10 이벤트 구현, 배치 전송 + Beacon API |
| **ab-report** | C+ | CTR/전환율 계산하나, 통계적 유의성 없음 |
| **메트릭 범위** | C | 평균 평점, 다양성, 추천 수용률 없음 |
| **실험 관리** | D | 하드코딩 가중치, 실험 시작/종료 없음, 동적 변경 불가 |

**종합**: 프로토타입 수준. 데이터 수집은 되고 있으나, **의사결정에 활용하기에는 부족**.

### 6-2. 의미있는 실험을 위해 부족한 것들

| 우선순위 | 부족한 것 | 영향 | 난이도 |
|:--------:|----------|------|:------:|
| **1** | **MovieModal/Banner 이벤트 누락** — 전환율 과소 측정 | 높음 | 낮음 |
| **2** | **통계적 유의성 검증** — winner가 무의미 | 높음 | 중간 |
| **3** | **추천 컨텍스트 전파** — 어떤 추천이 전환을 만드는지 추적 불가 | 높음 | 중간 |
| **4** | **CF가 user-level 아님** — test_a/test_b 실험의 의미 제한적 | 높음 | 높음 |
| **5** | **Beacon API auth 미포함** — 이탈 이벤트에 user_id=null 가능 | 중간 | 낮음 |
| **6** | **그룹 비율 조절 불가** — 위험한 실험에 소수 배정 불가 | 중간 | 낮음 |
| **7** | **실험 기간 관리 없음** — 시작/종료, 과거 실험 결과 보존 없음 | 중간 | 중간 |
| **8** | **다양성/추천 수용률 메트릭** — 추천 품질의 다면 평가 불가 | 중간 | 중간 |

### 6-3. 이벤트 데이터로 추천 품질 평가 가능 여부

**현재 가능:**
- 섹션별 CTR (어떤 추천 섹션이 클릭을 많이 받는지)
- 상세 체류 시간 (추천 영화에 관심을 갖는지)
- 전환율 (상세 → 찜/평점)

**현재 불가:**
- 추천 순위별 클릭률 (position 데이터는 있지만 그룹별 집계 미구현)
- 추천 영화 vs 비추천 영화 평점 비교
- 장르 다양성 변화 추적
- 사용자 재방문율 (일별 고유 사용자 추이)
- 세션당 인게이지먼트 (이벤트 수, 체류 시간)

---

## 요약: 핵심 발견 TOP 5

1. **MovieModal/FeaturedBanner에서 찜/평점/클릭 이벤트 누락** — 전환 추적의 가장 큰 사각지대
2. **CF score가 user-level 개인화 아님** — test_a/test_b의 높은 CF 가중치가 실질적으로 MovieLens 인기도 편향
3. **ab-report에 통계적 유의성 없음** — winner 판정이 무의미
4. **preferred_genres 가중치 1점** — 콜드스타트 사용자에게 거의 영향 없음
5. **추천 컨텍스트 미전파** — 어떤 추천이 실제 전환(평점/찜)으로 이어졌는지 추적 불가
