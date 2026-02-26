## 리뷰 대상: Step 02A — 오프라인 데이터셋 빌더

### 리뷰 범위
- backend/scripts/build_offline_dataset.py (신규, ~530줄)

### 체크리스트

#### 라벨 정의 정확성
- [ ] 라벨 우선순위: judgment(rating) > favorite_add > dwell(≥30s) > click/detail_view > none
- [ ] rating ≥ 4.0 → label=3, rating 3.0~3.9 → label=2, rating < 3.0 → label=1
- [ ] favorite_add → label=3
- [ ] dwell_ms ≥ 30000 → label=2
- [ ] click/movie_click/detail_view → label=1
- [ ] 반응 없음 → label=0

#### Temporal Split 정확성
- [ ] 기본: T-14d 경계(train), T-14d~T-7d(valid), T-7d~T(test)
- [ ] train 50건 미만 시 70/15/15 비율 fallback
- [ ] test의 min(served_at) > train의 max(served_at) 검증 로직 존재
- [ ] --split ratio 옵션이 시간순 정렬 후 비율 분리

#### 데이터 조인 정확성
- [ ] impressions LEFT JOIN interactions ON (request_id, movie_id)
- [ ] impressions LEFT JOIN judgments ON (request_id, movie_id)
- [ ] movies 벌크 조회 후 movie_map으로 피처 추출
- [ ] movie_map에 없는 movie_id 처리 (features 빈 값 또는 skip)

#### 출력 포맷
- [ ] JSONL 각 행이 유효한 JSON
- [ ] 필수 필드: request_id, user_id, movie_id, rank, label, algorithm_version, served_at
- [ ] features에 genres, weighted_score, emotion_tags, mbti_score, weather_score 포함
- [ ] stats.json 생성

#### 안전성
- [ ] DB 읽기 전용 (INSERT/UPDATE/DELETE 없음)
- [ ] PII(이메일 등) 미포함
- [ ] 빈 데이터 시 깨끗한 종료 (exit 0, 파일 미생성)
- [ ] DB 연결 실패 시 명확한 에러 메시지

#### 코드 품질
- [ ] argparse CLI 인터페이스
- [ ] structlog 또는 print로 진행 상황 표시
- [ ] 함수 분리 (compute_label, extract_features, temporal_split 등)

### 발견사항 분류
- CRITICAL: 라벨 계산 오류, 데이터 누수(split 역전), DB 수정
- WARNING: 피처 누락, 통계 불일치, 에러 핸들링 미흡
- INFO: 코드 구조, 네이밍

### 출력
결과를 codex_results.md에 저장하세요.