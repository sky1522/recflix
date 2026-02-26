# Step 02A Review — 오프라인 데이터셋 빌더

## Findings (Severity Order)

### CRITICAL
- 없음

### WARNING
1. `validate_split`이 체크리스트의 엄격 조건(`test.min > train.max`)이 아닌 `>=` 비교를 사용합니다.
- 현재 구현은 경계 시각이 동일한 레코드가 train/test에 걸쳐 있을 때도 검증 통과할 수 있습니다.
- 근거: `backend/scripts/build_offline_dataset.py:441`, `backend/scripts/build_offline_dataset.py:450`, `backend/scripts/build_offline_dataset.py:455`

2. DB 연결 실패 시 사용자 친화적 에러 메시지를 출력하지 않고 예외 스택트레이스에 의존합니다.
- `--db-url` 누락은 명확히 처리하지만, 실제 DB connect/query 실패(`load_impressions` 등)는 `try/except` 래핑이 없어 명시 메시지 요구를 충족하지 못합니다.
- 근거: `backend/scripts/build_offline_dataset.py:468`, `backend/scripts/build_offline_dataset.py:475`, `backend/scripts/build_offline_dataset.py:478`, `backend/scripts/build_offline_dataset.py:106`

### INFO
- `impressions LEFT JOIN interactions/judgments`는 SQL 조인문이 아니라, impression 순회 + `(request_id, movie_id)` 키 조회(`dict.get(..., [])`)로 동일한 left join 의미를 구현했습니다. (소스 기반 추론)
- 근거: `backend/scripts/build_offline_dataset.py:227`, `backend/scripts/build_offline_dataset.py:228`, `backend/scripts/build_offline_dataset.py:229`

## 체크리스트 검증

### 라벨 정의 정확성
- [x] 라벨 우선순위: judgment(rating) > favorite_add > dwell(≥30s) > click/detail_view > none
  - 근거: `backend/scripts/build_offline_dataset.py:40`, `backend/scripts/build_offline_dataset.py:56`, `backend/scripts/build_offline_dataset.py:60`, `backend/scripts/build_offline_dataset.py:69`, `backend/scripts/build_offline_dataset.py:74`
- [x] rating ≥ 4.0 → label=3, rating 3.0~3.9 → label=2, rating < 3.0 → label=1
  - 근거: `backend/scripts/build_offline_dataset.py:49`, `backend/scripts/build_offline_dataset.py:51`, `backend/scripts/build_offline_dataset.py:53`
- [x] favorite_add → label=3
  - 근거: `backend/scripts/build_offline_dataset.py:56`, `backend/scripts/build_offline_dataset.py:57`
- [x] dwell_ms ≥ 30000 → label=2
  - 근거: `backend/scripts/build_offline_dataset.py:60`, `backend/scripts/build_offline_dataset.py:65`, `backend/scripts/build_offline_dataset.py:66`
- [x] click/movie_click/detail_view → label=1
  - 근거: `backend/scripts/build_offline_dataset.py:69`, `backend/scripts/build_offline_dataset.py:71`
- [x] 반응 없음 → label=0
  - 근거: `backend/scripts/build_offline_dataset.py:74`

### Temporal Split 정확성
- [x] 기본: T-14d 경계(train), T-14d~T-7d(valid), T-7d~T(test)
  - 근거: `backend/scripts/build_offline_dataset.py:301`, `backend/scripts/build_offline_dataset.py:302`, `backend/scripts/build_offline_dataset.py:307`, `backend/scripts/build_offline_dataset.py:309`, `backend/scripts/build_offline_dataset.py:311`
- [x] train 50건 미만 시 70/15/15 비율 fallback
  - 근거: `backend/scripts/build_offline_dataset.py:314`, `backend/scripts/build_offline_dataset.py:315`
- [ ] test의 min(served_at) > train의 max(served_at) 검증 로직 존재
  - 상태: 검증 함수는 존재하나 비교가 `>=`로 구현되어 체크리스트의 엄격한 `>` 조건과 불일치
  - 근거: `backend/scripts/build_offline_dataset.py:441`, `backend/scripts/build_offline_dataset.py:455`
- [x] --split ratio 옵션이 시간순 정렬 후 비율 분리
  - 근거: `backend/scripts/build_offline_dataset.py:108`, `backend/scripts/build_offline_dataset.py:114`, `backend/scripts/build_offline_dataset.py:294`, `backend/scripts/build_offline_dataset.py:462`

### 데이터 조인 정확성
- [x] impressions LEFT JOIN interactions ON (request_id, movie_id)
  - 근거: `backend/scripts/build_offline_dataset.py:227`, `backend/scripts/build_offline_dataset.py:228`
- [x] impressions LEFT JOIN judgments ON (request_id, movie_id)
  - 근거: `backend/scripts/build_offline_dataset.py:227`, `backend/scripts/build_offline_dataset.py:229`
- [x] movies 벌크 조회 후 movie_map으로 피처 추출
  - 근거: `backend/scripts/build_offline_dataset.py:161`, `backend/scripts/build_offline_dataset.py:180`, `backend/scripts/build_offline_dataset.py:490`, `backend/scripts/build_offline_dataset.py:491`, `backend/scripts/build_offline_dataset.py:243`
- [x] movie_map에 없는 movie_id 처리 (features 빈 값 또는 skip)
  - 근거: `backend/scripts/build_offline_dataset.py:82`, `backend/scripts/build_offline_dataset.py:83`, `backend/scripts/build_offline_dataset.py:243`, `backend/scripts/build_offline_dataset.py:245`

### 출력 포맷
- [x] JSONL 각 행이 유효한 JSON
  - 근거: `backend/scripts/build_offline_dataset.py:341`, `backend/scripts/build_offline_dataset.py:344`
- [x] 필수 필드: request_id, user_id, movie_id, rank, label, algorithm_version, served_at
  - 근거: `backend/scripts/build_offline_dataset.py:248`, `backend/scripts/build_offline_dataset.py:249`, `backend/scripts/build_offline_dataset.py:251`, `backend/scripts/build_offline_dataset.py:252`, `backend/scripts/build_offline_dataset.py:255`, `backend/scripts/build_offline_dataset.py:256`, `backend/scripts/build_offline_dataset.py:260`
- [x] features에 genres, weighted_score, emotion_tags, mbti_score, weather_score 포함
  - 근거: `backend/scripts/build_offline_dataset.py:95`, `backend/scripts/build_offline_dataset.py:96`, `backend/scripts/build_offline_dataset.py:97`, `backend/scripts/build_offline_dataset.py:98`, `backend/scripts/build_offline_dataset.py:99`
- [x] stats.json 생성
  - 근거: `backend/scripts/build_offline_dataset.py:523`, `backend/scripts/build_offline_dataset.py:524`

### 안전성
- [x] DB 읽기 전용 (INSERT/UPDATE/DELETE 없음)
  - 근거: `backend/scripts/build_offline_dataset.py:110`, `backend/scripts/build_offline_dataset.py:126`, `backend/scripts/build_offline_dataset.py:145`, `backend/scripts/build_offline_dataset.py:167`
- [x] PII(이메일 등) 미포함
  - 근거: 출력 레코드 필드 구성 `backend/scripts/build_offline_dataset.py:248`~`backend/scripts/build_offline_dataset.py:261`
- [x] 빈 데이터 시 깨끗한 종료 (exit 0, 파일 미생성)
  - 근거: `backend/scripts/build_offline_dataset.py:479`, `backend/scripts/build_offline_dataset.py:480`, `backend/scripts/build_offline_dataset.py:503`, `backend/scripts/build_offline_dataset.py:504`
- [ ] DB 연결 실패 시 명확한 에러 메시지
  - 상태: 예외 처리/사용자용 메시지 래핑 미흡
  - 근거: `backend/scripts/build_offline_dataset.py:472`, `backend/scripts/build_offline_dataset.py:475`, `backend/scripts/build_offline_dataset.py:478`

### 코드 품질
- [x] argparse CLI 인터페이스
  - 근거: `backend/scripts/build_offline_dataset.py:459`~`backend/scripts/build_offline_dataset.py:464`
- [x] structlog 또는 print로 진행 상황 표시
  - 근거: `backend/scripts/build_offline_dataset.py:475`, `backend/scripts/build_offline_dataset.py:483`, `backend/scripts/build_offline_dataset.py:489`, `backend/scripts/build_offline_dataset.py:495`, `backend/scripts/build_offline_dataset.py:508`
- [x] 함수 분리 (compute_label, extract_features, temporal_split 등)
  - 근거: `backend/scripts/build_offline_dataset.py:32`, `backend/scripts/build_offline_dataset.py:81`, `backend/scripts/build_offline_dataset.py:283`, `backend/scripts/build_offline_dataset.py:347`, `backend/scripts/build_offline_dataset.py:441`

## 결론
- Step 02A 구현은 라벨링, 피처 추출, split, 출력 파이프라인이 전반적으로 요구사항에 부합합니다.
- 다만 체크리스트 기준으로는 **WARNING 2건**(split 검증 연산자 엄격도, DB 연결 실패 메시지 처리) 보완이 필요합니다.
