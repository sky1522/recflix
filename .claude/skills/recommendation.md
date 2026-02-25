# 추천 시스템

## 핵심 파일
→ `backend/app/api/v1/recommendations.py` (API 라우터)
→ `backend/app/api/v1/recommendation_engine.py` (스코어링 엔진)
→ `backend/app/api/v1/recommendation_constants.py` (가중치/다양성 상수)
→ `backend/app/api/v1/recommendation_cf.py` (CF 모듈)
→ `backend/app/api/v1/recommendation_reason.py` (추천 이유 43개 템플릿)
→ `backend/app/api/v1/diversity.py` (다양성 후처리 5개 함수)
→ `backend/app/api/v1/semantic_search.py` (인메모리 벡터 검색)

## 하이브리드 스코어링 (v3, CF 통합)
→ recommendation_engine.py의 `calculate_hybrid_scores()` 참조

### CF 활성화 시
- Mood 있을 때: (0.20 x MBTI) + (0.15 x Weather) + (0.25 x Mood) + (0.15 x Personal) + (0.25 x CF)
- Mood 없을 때: (0.25 x MBTI) + (0.20 x Weather) + (0.30 x Personal) + (0.25 x CF)

### CF 없을 때 (fallback, v2)
- Mood 있을 때: (0.25 x MBTI) + (0.20 x Weather) + (0.30 x Mood) + (0.25 x Personal)
- Mood 없을 때: (0.35 x MBTI) + (0.25 x Weather) + (0.40 x Personal)

### 공통
- 품질 보정: weighted_score 기반 x0.85~1.0
- 품질 필터: weighted_score >= 6.0

## 협업 필터링 (CF)
→ recommendation_cf.py 참조
- MovieLens 25M 기반 SVD (scipy, k=100)
- 50K users x 17.5K items 학습
- RecFlix 사용자는 MovieLens에 없음 → CF = global_mean + item_bias
- 모델: `backend/data/movielens/svd_model.pkl` (53MB, git 제외)
- SVD RMSE: 0.8768 (Item Mean 0.9656 대비 -9.2%)

## 추천 태그
→ recommendation_engine.py의 태그 부여 로직 참조
- `#MBTI추천` — MBTI 스코어 > 0.5 (보라)
- `#비오는날` 등 — 날씨 스코어 > 0.5 (파랑)
- `#취향저격` — 장르 2개 이상 매칭 (초록)
- `#비슷한영화` — similar_movies 포함 (초록)
- `#명작` — weighted_score >= 7.5 (노랑)

## MBTI/날씨/기분 매핑
→ recommendation_constants.py의 MOOD_EMOTION_MAPPING 참조

### 기분(Mood) 8종 → 감성 클러스터 매핑
| 기분 | 한국어 | 매핑 |
|------|--------|------|
| relaxed | 평온한 | healing |
| tense | 긴장된 | tension |
| excited | 활기찬 | energy |
| emotional | 몽글몽글한 | romance, deep |
| imaginative | 상상에 빠진 | fantasy |
| light | 유쾌한 | light |
| gloomy | 울적한 | deep, healing |
| stifled | 답답한 | energy, tension |

## 개인화 로직
→ recommendation_engine.py의 Personal Score 계산 참조
1. 찜 + 고평점(4.0 이상) 영화 장르 집계 (고평점 2배 가중치)
2. 상위 3개 장르 추출
3. similar_movies 보너스
4. 명작 보너스 (weighted_score >= 7.5, 태그만)

## emotion_tags 2-Tier
| 방식 | 대상 | 영화 수 | 최대 점수 |
|------|------|--------|----------|
| LLM 분석 (Claude API) | 인기 상위 | ~1,711 | 1.0 |
| 키워드 기반 | 나머지 | ~41,206 | 0.7 |

## 다양성 후처리 (diversity.py)
→ 스코어링 후 순차 적용: diversify_by_genre → apply_genre_cap → ensure_freshness → inject_serendipity → deduplicate_section
→ 상수: recommendation_constants.py의 DIVERSITY_* 참조

## 추천 이유 (recommendation_reason.py)
→ 우선순위: compound > mood/personal > mbti > weather > quality
→ 43개 템플릿, LLM 호출 없음 ($0, ~0ms)

## 시맨틱 검색 (semantic_search.py)
→ Voyage AI 임베딩 42,917편, NumPy 인메모리 코사인 유사도
→ API: `GET /movies/semantic-search?q={query}&limit=20`
→ 재랭킹 v2: semantic 60% + popularity 15% (log1p) + quality 25%

## 콜드스타트 (Phase 46)
→ preferred_genres 기반 fallback (온보딩에서 설정)
→ 찜/평점 없는 신규 사용자도 장르 기반 추천 가능
→ 상호작용 5건 이상이면 preferred_genres 무시 (실제 데이터 우선)

## 피드백 루프 (Phase 46)
→ interaction_version 캐시 무효화 키 도입
→ 평점/찜 변경 시 홈 추천이 즉시 갱신됨

## A/B 테스트 & 이벤트 트래킹 (Phase 52)
→ `backend/app/api/v1/ab_stats.py` (Z-test, Wilson CI, 추가 메트릭 SQL)
→ `backend/app/api/v1/events.py` (AB Report + 7개 헬퍼 함수)

### 실험 그룹 가중치
- 설정: `EXPERIMENT_WEIGHTS=control:34,test_a:33,test_b:33` (config.py)
- 배정: `_weighted_random_group()` in auth.py (회원가입 3곳 적용)
- 폴백: 파싱 실패 시 `random.choice(EXPERIMENT_GROUPS)`

### 이벤트 컨텍스트 전파
- MovieCard/HybridMovieCard → `?from=section&pos=index` URL 파라미터
- 상세 페이지: `source_section`, `source_position` 이벤트 메타데이터에 포함
- FeaturedBanner: 상세보기 click + 트레일러 click 이벤트

### preferred_genres 가중치
- 콜드스타트: preferred_genres 장르당 가중치 **3** (기존 1)
- 상호작용 5건 이상이면 preferred_genres 무시

## 알고리즘 변경 시 체크리스트
1. recommendation_engine.py 가중치/로직 수정
2. recommendation_constants.py 상수 수정
3. `docs/RECOMMENDATION_LOGIC.md` 동기화
4. 추천 태그 조건 확인
5. 품질 필터(weighted_score >= 6.0) 영향 확인
6. 다양성 정책 상수 영향 확인
7. 프론트엔드 HybridMovieCard 태그/추천이유 표시 확인
8. 빌드 확인
