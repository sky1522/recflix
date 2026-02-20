# Phase 34: 추천 다양성/신선도 정책 구현 결과

## 날짜
2026-02-20

## 변경 파일

| 파일 | 작업 | 설명 |
|------|------|------|
| `backend/app/api/v1/diversity.py` | **신규** | 5개 다양성 후처리 함수 |
| `backend/app/api/v1/recommendation_constants.py` | 수정 | 다양성 설정 상수 8개 추가 |
| `backend/app/api/v1/recommendation_engine.py` | 수정 | calculate_hybrid_scores 후 다양성 파이프라인 |
| `backend/app/api/v1/recommendations.py` | 수정 | 홈 추천 섹션 간 중복 제거 + for-you serendipity |
| `backend/app/api/v1/movies.py` | 수정 | 시맨틱 검색 장르 다양성 후처리 |

## diversity.py 함수 목록

| 함수 | 설명 | 파라미터 |
|------|------|----------|
| `diversify_by_genre()` | 같은 primary genre 연속 N개 제한 | max_consecutive=3 |
| `apply_genre_cap()` | 단일 장르 비율 상한 | max_genre_ratio=0.35 |
| `ensure_freshness()` | 최신작/클래식 최소 비율 보장 | recent_ratio=0.20, classic_ratio=0.10 |
| `inject_serendipity()` | 선호 외 고품질 영화 삽입 | serendipity_ratio=0.10, min_quality=7.0 |
| `deduplicate_section()` | 이미 노출된 영화 제외 | seen_ids 기반 |

## 다양성 전/후 비교

### MBTI INTJ 추천 (20편)

| 지표 | Before | After | 변화 |
|------|--------|-------|------|
| Top 3 장르 집중도 | 62.9% | **59.0%** | -3.9% |
| 같은 장르 연속 최대 | 20 (무제한) | **2** | 제한 성공 |
| 최신작(3년) | 0편 | **2편** (2024, 2025) | 신선도 보장 |
| 연도 범위 | 2001~2023 | **2001~2025** | 확장 |
| 장르 종류 | 5종 | **6종** (+공포, TV영화) | 다양화 |

### 시맨틱 검색 "비 오는 날 잔잔한 영화" (20편)

| 지표 | Before | After | 변화 |
|------|--------|-------|------|
| Top 3 장르 집중도 | **81.6%** | **51.1%** | **-30.5%** |
| 드라마 편수 (primary) | 18/20 (90%) | **5/20 (25%)** | 대폭 감소 |
| 장르 종류 | 3종 | **8종** | 다양화 |

### 홈 추천 섹션 간 중복

| 지표 | Before | After |
|------|--------|-------|
| 중복 영화 수 | 11편 (5.9%) | **0편 (0.0%)** |
| 전체 고유 영화 수 | 188편 | **199편** |

## 적용된 엔드포인트 매트릭스

| 엔드포인트 | 장르 다양성 | 신선도 | Serendipity | 중복 제거 |
|-----------|:----------:|:-----:|:-----------:|:--------:|
| `GET /recommendations` (홈) | O | O | O (hybrid만) | O |
| `GET /recommendations/hybrid` | O | O | - | - |
| `GET /recommendations/mbti` | O | O | - | - |
| `GET /recommendations/weather` | O | O | - | - |
| `GET /recommendations/emotion` | O | O | - | - |
| `GET /recommendations/popular` | - | - | - | - |
| `GET /recommendations/top-rated` | - | - | - | - |
| `GET /recommendations/for-you` | - | - | O | - |
| `GET /movies/semantic-search` | O (전용) | - | - | - |

## Config 상수 (recommendation_constants.py)

```python
DIVERSITY_ENABLED = True
GENRE_MAX_CONSECUTIVE = 3
GENRE_MAX_RATIO = 0.35
FRESHNESS_RECENT_RATIO = 0.20
FRESHNESS_CLASSIC_RATIO = 0.10
SERENDIPITY_RATIO = 0.10
SERENDIPITY_MIN_QUALITY = 7.0
SEMANTIC_GENRE_MAX = 5
```

## 프로덕션 재배포 필요
- Backend (Railway): `cd backend && railway up`
- Frontend: 변경 없음 (backend only)
