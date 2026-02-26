# Step 01A: 로그 정규화 스키마 + Alembic 마이그레이션

> 작업일: 2026-02-26
> 목적: 오프라인 평가용 노출→반응→판단 로그 스키마 도입

## 생성된 파일

| 파일 | 설명 |
|------|------|
| `backend/app/models/reco_impression.py` | RecoImpression 모델 (추천 노출 기록) |
| `backend/app/models/reco_interaction.py` | RecoInteraction 모델 (사용자 반응 기록) |
| `backend/app/models/reco_judgment.py` | RecoJudgment 모델 (명시적 판단 기록) |
| `backend/alembic/versions/3a2d04b4c24c_add_reco_log_tables.py` | Alembic 마이그레이션 |

## 변경된 기존 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/models/__init__.py` | 3개 모델 import + `__all__` 추가 |

## Alembic Migration ID

`3a2d04b4c24c` (down_revision: `e2b032d303d8`)

## 테이블 스키마 요약

### reco_impressions (추천 노출)
- `id` BIGSERIAL PK, `request_id` UUID NOT NULL, `user_id` FK→users(SET NULL)
- `session_id`, `experiment_group`, `algorithm_version`, `section`, `movie_id`, `rank`, `score`, `context` JSONB, `served_at`
- 인덱스: idx_imp_request, idx_imp_user_time, idx_imp_algo

### reco_interactions (사용자 반응)
- `id` BIGSERIAL PK, `request_id` UUID, `user_id` FK→users(SET NULL)
- `session_id`, `movie_id`, `event_type`, `dwell_ms`, `position`, `metadata` JSONB, `interacted_at`
- 인덱스: idx_int_request, idx_int_user_time, idx_int_movie

### reco_judgments (명시적 판단)
- `id` BIGSERIAL PK, `request_id` UUID, `user_id` FK→users(CASCADE) NOT NULL
- `movie_id`, `label_type`, `label_value`, `judged_at`
- 인덱스: idx_jdg_user, idx_jdg_request

## 검증 결과

| 항목 | 결과 |
|------|------|
| `alembic upgrade head` | OK |
| `alembic downgrade -1` | OK |
| 재 `alembic upgrade head` | OK |
| 테이블 3개 생성 확인 | OK (reco_impressions, reco_interactions, reco_judgments) |
| 인덱스 8개 + PK 3개 = 11개 | OK |
| Python 모델 import | OK |

## 준수 사항
- 기존 테이블(users, movies, user_events 등) 수정 없음
- main.py의 create_all 사용 안 함
- movie_id에 Foreign Key 없음 (삭제된 영화 로그 보존)
- 테스트 데이터 삽입 없음
