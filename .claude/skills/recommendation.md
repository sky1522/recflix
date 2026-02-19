# 추천 시스템

## 핵심 파일
→ `backend/app/api/v1/recommendations.py` (API 라우터)
→ `backend/app/api/v1/recommendation_engine.py` (스코어링 엔진)
→ `backend/app/api/v1/recommendation_constants.py` (가중치 상수)
→ `backend/app/api/v1/recommendation_cf.py` (CF 모듈)

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

## 알고리즘 변경 시 체크리스트
1. recommendation_engine.py 가중치/로직 수정
2. recommendation_constants.py 상수 수정
3. `docs/RECOMMENDATION_LOGIC.md` 동기화
4. 추천 태그 조건 확인
5. 품질 필터(weighted_score >= 6.0) 영향 확인
6. 프론트엔드 HybridMovieCard 태그 표시 확인
7. 빌드 확인
