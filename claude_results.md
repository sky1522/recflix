# Phase 33-5: 시맨틱 검색 품질 개선 — 재랭킹 + 인기도 반영

## 날짜
2026-02-20

## 생성/수정된 파일

| 파일 | 상태 | 설명 |
|------|------|------|
| `backend/app/api/v1/movies.py` | 수정 | 재랭킹 함수 + top_k 300 + match_reason |
| `frontend/lib/api.ts` | 수정 | SemanticSearchResult에 relevance_score, match_reason 필드 추가 |
| `frontend/components/search/SearchAutocomplete.tsx` | 수정 | match_reason 표시 |

## 재랭킹 공식

```
최종 점수 = semantic_score × 0.50 + popularity_score × 0.30 + quality_score × 0.20
```

| 요소 | 산식 | 범위 |
|------|------|------|
| semantic_score | 벡터 코사인 유사도 (그대로) | 0~1 |
| popularity_score | min(log(1+vote_count) / log(1+50000), 1.0) | 0~1 |
| quality_score | weighted_score / 10.0 | 0~1 |

- top_k: 100 → **300** (넓은 후보 확보 → 인기 영화 포함)
- weighted_score >= 5.0 필터 유지

## 수정 전/후 비교

### 쿼리 1: "비오는 날 혼자 보기 좋은 잔잔한 영화"

| 순위 | 수정 전 | 수정 후 |
|------|---------|---------|
| 1 | You Are Alone (6.3) | **레인 맨** (7.7) |
| 2 | Rain (6.2) | **퍼펙트 데이즈** (7.6) |
| 3 | 고독 (6.2) | **싱글맨** (7.2) |
| 4 | Hysterical Blindness (6.3) | 디서비디언스 (6.8) |
| 5 | 혼자 사는 사람들 (6.5) | 레인메이커 (6.9) |

### 쿼리 2: "스릴 넘치는 반전 영화"

| 순위 | 수정 전 | 수정 후 |
|------|---------|---------|
| 1 | 대역전 (6.2) | **스내치** (7.8) |
| 2 | As Good As Dead (6.1) | **스피드** (7.1) |
| 3 | The Psycho Lover (6.3) | 미스터 & 미세스 스미스 (6.7) |
| 4 | Alarmed (6.3) | **와일드 테일즈** (7.8) |
| 5 | Treacherous (6.3) | 평행이론: 도플갱어 살인 (7.2) |

### 쿼리 3: "감동적인 가족 영화 추천"

| 순위 | 수정 전 | 수정 후 |
|------|---------|---------|
| 1 | 패밀리 이즈 패밀리 (5.9) | **도리를 찾아서** (7.0) |
| 2 | 애들이 똑같아요 (6.5) | **크루즈 패밀리** (6.9) |
| 3 | 윌러비 가족 (6.9) | **말리와 나** (7.1) |
| 4 | When I Find the Ocean (6.3) | **페어런트 트랩** (7.2) |
| 5 | The Present (6.3) | **인스턴트 패밀리** (7.4) |

## match_reason 예시

```
"분위기 일치 · 높은 평점 · 많은 관객"  (semantic≥0.45, quality≥0.75, pop≥0.5)
"분위기 일치 · 많은 관객"              (semantic≥0.45, pop≥0.5)
"AI 추천"                            (모든 임계값 미달 시)
```

## 프로덕션 재배포 필요
- Railway: `cd backend && railway up` (재랭킹 로직 반영)
- Vercel: `cd frontend && npx vercel --prod` (match_reason UI 반영)
- Redis 캐시 초기화 필요 (기존 결과 캐시에 재랭킹 미적용 데이터 잔존)
