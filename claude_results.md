# Step 02: 오프라인 학습/평가용 데이터셋 자동 생성 스크립트

> 작업일: 2026-02-26
> 목적: reco_* 테이블의 로그를 ML 학습/평가용 JSONL 데이터셋으로 변환

## 생성 파일

| 파일 | 설명 |
|------|------|
| `backend/scripts/build_offline_dataset.py` | 오프라인 데이터셋 빌더 CLI 스크립트 (약 530줄) |

## CLI 사용 예시

```bash
# 기본 사용 (temporal split)
python backend/scripts/build_offline_dataset.py \
  --db-url "$DATABASE_URL" \
  --output-dir data/offline/ \
  --verbose

# 비율 기반 분리 (디버깅용)
python backend/scripts/build_offline_dataset.py \
  --db-url "$DATABASE_URL" \
  --split ratio \
  --min-impressions 10
```

## 데이터 흐름

```
reco_impressions
+ LEFT JOIN reco_interactions ON (request_id, movie_id)
+ LEFT JOIN reco_judgments ON (request_id, movie_id)
+ LEFT JOIN movies ON (movie_id)
↓
라벨 부여 (judgment > favorite > dwell > click > none)
↓
피처 추출 (genres, weighted_score, emotion_tags, mbti_score, weather_score)
↓
Temporal Split (14일/7일 경계 또는 70/15/15 fallback)
↓
train.jsonl / valid.jsonl / test.jsonl + stats.json
```

## 라벨 정의

| Label | 조건 | 의미 |
|-------|------|------|
| 3 | rating >= 4.0 또는 favorite_add | strong positive |
| 2 | rating 3.0~3.9 또는 dwell >= 30초 | positive |
| 1 | rating < 3.0 또는 click/detail_view | weak positive |
| 0 | 반응 없음 | negative |

## 출력 포맷 예시

```json
{
  "request_id": "eb9a9f45-c7e9-4797-b72e-cdad73573ca2",
  "user_id": 123,
  "session_id": "a1b2c3d4",
  "movie_id": 27205,
  "rank": 3,
  "score": 0.847,
  "section": "hybrid_row",
  "label": 1,
  "algorithm_version": "hybrid_v1",
  "experiment_group": "control",
  "context": {"weather": "rainy", "mood": "emotional", "mbti": "INTJ"},
  "features": {
    "genres": ["SF", "Action"],
    "weighted_score": 8.2,
    "emotion_tags": {"tension": 0.8, "deep": 0.7},
    "mbti_score": 0.48,
    "weather_score": 0.35
  },
  "served_at": "2026-02-20T12:00:00+00:00",
  "interacted_at": "2026-02-20T12:01:30+00:00"
}
```

## 검증 결과

| 항목 | 결과 |
|------|------|
| compute_label 단위 테스트 (8케이스) | OK |
| extract_features 단위 테스트 | OK |
| temporal_split ratio/temporal 테스트 | OK |
| validate_split 테스트 (정상/역전) | OK |
| 빈 데이터 → 깨끗한 종료 (exit 0) | OK |
| 빈 데이터 → 파일 미생성 | OK |
| Ruff 린트 | OK |
| pytest (10 passed, 4 skipped) | OK |
