# v2.0 배포 Step 3+4: Alembic 마이그레이션 + Railway 환경변수 — 완료

> 작업일: 2026-02-27

## Step 3: Alembic 마이그레이션 적용

### 마이그레이션 내역

| 리비전 | 설명 | 상태 |
|--------|------|------|
| `e2b032d303d8` | initial schema snapshot (빈 베이스라인) | 적용 완료 |
| `3a2d04b4c24c` | add_reco_log_tables (3테이블) | 적용 완료 |

### 생성된 테이블

| 테이블 | 컬럼 수 | FK | 인덱스 |
|--------|---------|-----|--------|
| `reco_impressions` | 12 | user_id → users (SET NULL) | 3개 |
| `reco_interactions` | 10 | user_id → users (SET NULL) | 3개 |
| `reco_judgments` | 7 | user_id → users (CASCADE) | 2개 |

### 검증

```
alembic_version: 3a2d04b4c24c (head)
reco_* tables: ['reco_impressions', 'reco_interactions', 'reco_judgments']
```

- 기존 테이블(movies, users, ratings 등) 영향 없음 확인
- 초기 마이그레이션이 빈 베이스라인이므로 기존 스키마 충돌 없음

---

## Step 4: Railway 환경변수 설정

| 변수명 | 값 | 상태 |
|--------|-----|------|
| TWO_TOWER_ENABLED | true | 신규 추가 |
| RERANKER_ENABLED | true | 신규 추가 |
| EXPERIMENT_WEIGHTS | control:34,test_a:33,test_b:33 | 신규 추가 |

---

## 완료 조건 체크

- [x] `alembic current` → `3a2d04b4c24c (head)` 확인
- [x] 로컬 DB에서 이미 적용됨 확인
- [x] 프로덕션 DB에 reco_impressions/interactions/judgments 3테이블 생성 확인
- [x] TWO_TOWER_ENABLED=true, RERANKER_ENABLED=true 환경변수 설정 완료
- [x] EXPERIMENT_WEIGHTS=control:34,test_a:33,test_b:33 설정 완료
- [x] 기존 테이블·환경변수와 충돌 없음

## 다음 단계

Step 5: git push → CI 통과 → Railway 배포 → 배포 후 검증
