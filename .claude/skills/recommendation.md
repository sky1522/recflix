# 추천 시스템

## 핵심 파일
→ `backend/app/api/v1/recommendations.py` 참조 (770 LOC)

## 하이브리드 스코어링
→ recommendations.py의 `calculate_hybrid_scores()` 참조
- Mood 있을 때: (0.25 x MBTI) + (0.20 x Weather) + (0.30 x Mood) + (0.25 x Personal)
- Mood 없을 때: (0.35 x MBTI) + (0.25 x Weather) + (0.40 x Personal)
- 품질 보정: weighted_score 기반 x0.85~1.0
- 품질 필터: weighted_score >= 6.0

## 추천 태그
→ recommendations.py의 태그 부여 로직 참조
- `#MBTI추천` — MBTI 스코어 > 0.5 (보라)
- `#비오는날` 등 — 날씨 스코어 > 0.5 (파랑)
- `#취향저격` — 장르 2개 이상 매칭 (초록)
- `#비슷한영화` — similar_movies 포함 (초록)
- `#명작` — weighted_score >= 7.5 (노랑)

## MBTI/날씨/기분 매핑
→ recommendations.py의 `MOOD_EMOTION_MAP`, 날씨/MBTI 매핑 상수 참조

### 기분(Mood) 8종 → 감성 클러스터 매핑
| 기분 | 한국어 | 매핑 |
|------|--------|------|
| relaxed | 평온한 | healing, light |
| tense | 긴장된 | tension, energy |
| excited | 활기찬 | energy, light |
| emotional | 몽글몽글한 | romance, healing |
| imaginative | 상상에 빠진 | fantasy, deep |
| light | 유쾌한 | light, energy |
| gloomy | 울적한 | deep, healing |
| stifled | 답답한 | energy, tension |

## 개인화 로직
→ recommendations.py의 Personal Score 계산 참조
1. 찜 + 고평점(4.0 이상) 영화 장르 집계 (고평점 2배 가중치)
2. 상위 3개 장르 추출
3. similar_movies 보너스
4. 명작 보너스 (평점 8.0 이상, 투표 100 이상)

## emotion_tags 2-Tier
| 방식 | 대상 | 영화 수 | 최대 점수 |
|------|------|--------|----------|
| LLM 분석 (Claude API) | 인기 상위 | ~1,711 | 1.0 |
| 키워드 기반 | 나머지 | ~41,206 | 0.7 |

## 알고리즘 변경 시 체크리스트
1. recommendations.py 가중치/로직 수정
2. `docs/RECOMMENDATION_LOGIC.md` 동기화
3. 추천 태그 조건 확인
4. 품질 필터(weighted_score >= 6.0) 영향 확인
5. 프론트엔드 HybridMovieCard 태그 표시 확인
6. 빌드 확인
