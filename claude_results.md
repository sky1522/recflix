# Step 04: FAISS 인덱스 + Two-Tower 서빙 통합

> 작업일: 2026-02-27
> 목적: Two-Tower 후보 생성을 추천 API에 통합 (A/B 테스트 test_a 그룹)

## 생성/수정 파일

| 파일 | 변경 | 설명 |
|------|------|------|
| `backend/scripts/build_faiss_index.py` | 신규 | FAISS 인덱스 빌드 CLI (flat/ivfflat) |
| `backend/app/services/two_tower_retriever.py` | 신규 | TwoTowerRetriever 서빙 모듈 (싱글톤) |
| `backend/app/config.py` | 수정 | TWO_TOWER_* 설정 4개 추가 |
| `backend/app/api/v1/recommendation_constants.py` | 수정 | test_a → "twotower_v1" |
| `backend/app/api/v1/recommendations.py` | 수정 | Two-Tower 분기 + fallback |
| `backend/app/main.py` | 수정 | lifespan에 retriever 초기화 |

## FAISS 인덱스

| 항목 | 값 |
|------|-----|
| 타입 | IndexFlatIP (Inner Product) |
| 벡터 | 42,917개 x 128dim |
| 파일 크기 | 21.0 MB |
| 빌드 시간 | <0.01s |
| 검색 속도 | 0.13 ms/query (top-200, 100회 벤치마크) |

## 추천 분기 흐름

```
get_home_recommendations()
├── algorithm_version = "twotower_v1" && retriever != None
│   ├── retriever.retrieve(mbti, genres, top_k=200, exclude=favorited)
│   ├── len(candidates) >= 20 → DB에서 후보만 조회
│   │   └── calculate_hybrid_scores(후보 200편) → 재랭킹
│   └── len(candidates) < 20 → "twotower_v1_supplemented"
│       └── 기존 전체 DB 스캔으로 보충
├── algorithm_version = "twotower_v1" && retriever == None
│   └── "hybrid_v1_fallback" → 기존 전체 스캔
└── 기존 경로 (control, test_b)
    └── 기존 전체 DB 스캔 → calculate_hybrid_scores()
```

## 서빙 성능

| 항목 | 값 |
|------|-----|
| Retriever 초기화 | 0.03s (모델 + FAISS + 맵 로드) |
| retrieve() 1회 | 2.0ms avg (min=1.6, max=2.6) |
| 전체 Two-Tower 경로 | < 50ms (retrieve + DB 쿼리 + 재랭킹) |

## Fallback 시나리오

| 시나리오 | algorithm_version | 동작 |
|----------|-------------------|------|
| 모델 파일 없음 | hybrid_v1_fallback | 기존 전체 스캔 |
| 후보 < 20편 | twotower_v1_supplemented | 기존 전체 스캔으로 보충 |
| TWO_TOWER_ENABLED=false | (skip loading) | 모든 그룹 기존 방식 |
| control/test_b 그룹 | hybrid_v1 / hybrid_v1_test_b | 기존 방식 그대로 |

## 환경변수 (config.py)

```
TWO_TOWER_ENABLED=true
TWO_TOWER_MODEL_PATH=data/models/two_tower/model_v1.pt
TWO_TOWER_INDEX_PATH=data/models/two_tower/faiss_index.bin
TWO_TOWER_MOVIE_MAP_PATH=data/models/two_tower/movie_id_map.json
```

## 검증 결과

| 항목 | 결과 |
|------|------|
| FAISS 인덱스 빌드 (faiss_index.bin, 21MB) | OK |
| Retriever retrieve() → 200개 후보 반환 | OK |
| Fallback: retriever=None → hybrid_v1_fallback | OK |
| 응답 시간 < 500ms (retrieve 2ms + DB) | OK |
| control 그룹 기존 방식 유지 (코드 미변경) | OK |
| calculate_hybrid_scores 미수정 | OK |
| Ruff 린트 (6 files) | OK |
| pytest (10 passed, 4 skipped) | OK |
