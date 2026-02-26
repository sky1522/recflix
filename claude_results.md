# Step 01B: 추천 API 응답에 request_id 발급 + impression 자동 기록

> 작업일: 2026-02-26
> 목적: 추천 API가 응답 시 request_id(UUID)를 발급하고, 노출된 영화를 reco_impressions에 자동 기록

## 생성된 파일

| 파일 | 설명 |
|------|------|
| `backend/app/services/reco_logger.py` | impression 벌크 INSERT 서비스 (별도 DB 세션, structlog 에러 로깅) |

## 변경된 기존 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/schemas/recommendation.py` | HomeRecommendations에 `request_id`, `algorithm_version` 필드 추가 |
| `backend/app/api/v1/recommendations.py` | request_id 생성, impression 수집, BackgroundTasks 로깅, 응답 필드 추가 |

## 응답 스키마 변경사항

HomeRecommendations에 2개 필드 추가:
```json
{
  "request_id": "eb9a9f45-c7e9-4797-b72e-cdad73573ca2",
  "algorithm_version": "hybrid_v1_control",
  "featured": {...},
  "rows": [...],
  "hybrid_row": {...}
}
```

## impression 수집 섹션 (7개)

| 섹션명 | 설명 | score |
|--------|------|-------|
| `hybrid_row` | 맞춤 추천 (로그인 시) | hybrid_score |
| `mbti_picks` | MBTI 성향 추천 | null |
| `weather_picks` | 날씨 기반 추천 | null |
| `mood_picks` | 기분별 추천 | null |
| `popular` | 인기 영화 | null |
| `top_rated` | 높은 평점 영화 | null |
| `featured` | 대표 배너 영화 | null |

## 검증 결과

| 항목 | 결과 |
|------|------|
| reco_logger 단독 테스트 (벌크 INSERT + DB 확인) | OK |
| 빈 sections 처리 (조용히 반환) | OK |
| Python import 확인 | OK |
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |
| 로컬 API 테스트 | SKIP (로컬 DB에 trailer_key 컬럼 부재 - 기존 이슈) |

## impression 기록 예시

```
request_id=eb9a9f45-..., section=featured, movie_id=278, rank=0, algo=hybrid_v1_control, group=control
request_id=eb9a9f45-..., section=popular,  movie_id=278, rank=0, algo=hybrid_v1_control, group=control
request_id=eb9a9f45-..., section=popular,  movie_id=13,  rank=1, algo=hybrid_v1_control, group=control
```

## 설계 결정

- **BackgroundTasks 사용**: 응답 지연 방지 (impression 로깅이 실패해도 추천 응답에 영향 없음)
- **별도 DB 세션**: SessionLocal()로 독립 세션 생성 (메인 세션 공유 금지)
- **structlog 로깅**: 성공 시 info, 실패 시 error + exc_info
- **벌크 INSERT**: `db.execute(insert(RecoImpression), rows)` 패턴으로 효율적 삽입
