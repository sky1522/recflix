## 작업: 오프라인 학습/평가용 데이터셋 자동 생성 스크립트

### 배경
Phase 01에서 reco_impressions, reco_interactions, reco_judgments에 로그가 쌓입니다.
이 로그를 ML 학습/오프라인 평가에 사용 가능한 형태로 변환하는 스크립트가 필요합니다.

핵심 원칙:
- 추천 시스템은 "미래를 맞히는 문제"이므로 시간 기준 분리(temporal split) 필수
- 노출 중 선택=positive, 미선택=negative (달리셔스 CTR 데이터 구성 참고)
- Synthetic 데이터는 학습에만 사용, 평가는 실제 데이터로만 (순환 논증 방지)

### 요구사항

#### 1. 스크립트: backend/scripts/build_offline_dataset.py

#### 2. 데이터 생성 흐름
reco_impressions (노출 기록)
+ LEFT JOIN reco_interactions ON (request_id, movie_id)
+ LEFT JOIN reco_judgments ON (request_id, movie_id)
↓
merged_events (impression 1건 = 1행)
↓ 라벨 부여 + 피처 추출
labeled_events
↓ Temporal Split
train.jsonl / valid.jsonl / test.jsonl

#### 3. 라벨 정의 (계층적 — 가장 강한 신호 우선)
```python
def compute_label(interactions, judgments):
    """
    하나의 impression(노출)에 대한 라벨 결정.
    판정 우선순위: judgment > favorite > dwell > click > none
    """
    # judgment가 있으면 최우선
    if judgments:
        rating = max(j.label_value for j in judgments if j.label_type == 'rating')
        if rating >= 4.0:
            return 3  # strong positive
        elif rating >= 3.0:
            return 2  # positive
        else:
            return 1  # weak positive (평점을 남긴 것 자체가 관심)
    
    # favorite
    if any(i.event_type == 'favorite_add' for i in interactions):
        return 3  # strong positive
    
    # dwell time (상세 페이지 체류)
    dwell_events = [i for i in interactions if i.event_type == 'detail_leave' and i.dwell_ms]
    if dwell_events and max(e.dwell_ms for e in dwell_events) >= 30000:
        return 2  # positive (30초 이상 체류)
    
    # click
    if any(i.event_type in ('click', 'movie_click', 'detail_view') for i in interactions):
        return 1  # weak positive
    
    # 노출만 되고 반응 없음
    return 0  # negative
```

#### 4. 피처 추출

각 impression 행에 영화 메타데이터를 조인하여 피처를 추가:
```python
features = {
    "genres": movie.genres,               # list[str]
    "weighted_score": movie.weighted_score,  # float
    "emotion_tags": movie.emotion_tags,    # dict (7dim)
    "mbti_score": movie.mbti_scores.get(context.get('mbti', ''), 0),  # float
    "weather_score": movie.weather_scores.get(context.get('weather', ''), 0),  # float
}
```

#### 5. Temporal Split 규칙
```python
# served_at 기준 (노출 시각)
all_events = sorted by served_at
T = max(served_at)

# 기본: 시간 기준 분리
train:  served_at < T - 14days
valid:  T - 14days <= served_at < T - 7days
test:   T - 7days <= served_at

# 최소 보장: train 50건 미만이면 비율 fallback
if len(train) < 50:
    # 전체의 70/15/15 비율로 시간순 분리
    n = len(all_events)
    train = all_events[:int(n * 0.7)]
    valid = all_events[int(n * 0.7):int(n * 0.85)]
    test = all_events[int(n * 0.85):]

# 검증: test의 min(served_at) > train의 max(served_at)
```

#### 6. 출력 포맷 (JSONL — 한 줄에 하나의 impression)
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

- interacted_at: 가장 마지막 상호작용 시각 (없으면 null)
- label=0인 행은 interacted_at=null

#### 7. 통계 리포트 (stdout + stats.json)
============================================================
RecFlix Offline Dataset Builder
Generated: 2026-02-26T15:00:00
Total impressions: 5,000
With interaction (label>0): 850 (17.0%)
Label distribution:
0 (negative):       4,150 (83.0%)
1 (weak positive):    520 (10.4%)
2 (positive):         180 (3.6%)
3 (strong positive):  150 (3.0%)
Split:
Train: 3,500 (70.0%)  [... ~ 2026-02-12]
Valid:   750 (15.0%)  [2026-02-12 ~ 2026-02-19]
Test:    750 (15.0%)  [2026-02-19 ~ 2026-02-26]
Users: 12 unique
Movies: 1,847 unique
Sections: hybrid_row(2000), popular(1500), featured(500), ...
Algorithms: hybrid_v1(3400), hybrid_v1_test_a(800), hybrid_v1_test_b(800)

#### 8. CLI 인터페이스
```bash
python backend/scripts/build_offline_dataset.py \
  --db-url "$DATABASE_URL" \
  --output-dir data/offline/ \
  --split temporal \
  --min-impressions 10 \
  --verbose
```

옵션:
- --db-url: PostgreSQL 연결 문자열 (필수 또는 DATABASE_URL 환경변수)
- --output-dir: 출력 디렉토리 (기본: data/offline/)
- --split: temporal (기본) | ratio (디버깅용 70/15/15)
- --min-impressions: 이 수 미만의 유저는 제외 (기본: 1)
- --verbose: 상세 로그

#### 9. 데이터가 없을 때 처리

reco_impressions가 비어있으면:
- "No impressions found. Run the service and collect data first." 메시지 출력
- 종료 코드 0 (에러 아님)
- 빈 파일 생성하지 않음

#### 10. 영화 메타데이터 조회

피처 추출을 위해 movies 테이블에서 필요한 정보를 한 번에 로드:
```python
# 모든 movie_id에 대해 벌크 조회
movie_ids = set(imp.movie_id for imp in impressions)
movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
movie_map = {m.id: m for m in movies}
```

### 검증
1. train.jsonl + valid.jsonl + test.jsonl 생성 확인 (데이터 있을 때)
2. test의 모든 served_at > train의 모든 served_at (temporal split 검증)
3. label 분포가 통계 리포트와 일치
4. JSONL 각 행이 유효한 JSON이고 필수 필드 포함
5. stats.json 생성 확인
6. 데이터 없을 때 깨끗하게 종료 확인
7. Ruff 린트 통과

### 금지사항
- 실시간 DB 수정 금지 (읽기 전용 스크립트)
- 사용자 PII(이메일 등) 출력 금지
- 외부 API 호출 금지
- reco_impressions 외 테이블 INSERT/UPDATE/DELETE 금지

### 완료 후
작업 결과를 claude_results.md에 저장하세요. 포함:
- 생성 파일 목록
- CLI 사용 예시
- 검증 결과 (데이터 있는 경우 / 없는 경우)
- 출력 포맷 예시 (1~2행)