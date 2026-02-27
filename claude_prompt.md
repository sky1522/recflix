# v2.0 배포 Step 3+4: Alembic 마이그레이션 + Railway 환경변수

## Step 3: Railway 프로덕션 DB에 Alembic 마이그레이션 적용

### 배경
`backend/alembic/versions/3a2d04b4c24c_add_reco_log_tables.py` 마이그레이션이 생성되어 있지만 프로덕션 DB에는 아직 적용되지 않음. reco_impressions, reco_interactions, reco_judgments 3테이블이 필요.

### 작업

1. **현재 마이그레이션 상태 확인**
```bash
cd backend
alembic current
alembic history
```

2. **프로덕션 DB에 마이그레이션 적용**
- Railway PostgreSQL 접속 정보 확인 (DATABASE_URL 환경변수)
- 로컬에서 프로덕션 DB를 대상으로 실행하거나, Railway CLI로 실행

```bash
# 방법 A: 로컬에서 프로덕션 DB 대상 실행
DATABASE_URL="postgresql://..." alembic upgrade head

# 방법 B: Railway CLI
railway run alembic upgrade head
```

3. **적용 확인**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE 'reco_%';
```
→ reco_impressions, reco_interactions, reco_judgments 3개 나와야 함

### 주의사항
- 기존 테이블(movies, users, ratings, collections, user_events, similar_movies)에 영향 없는지 확인
- 마이그레이션 파일이 CASCADE 관계를 포함하는지 확인 (user 삭제 시 reco 로그도 삭제?)
- 로컬 DB에 먼저 테스트 후 프로덕션 적용 권장

---

## Step 4: Railway 환경변수 확인/추가

### 확인할 환경변수

| 변수명 | 값 | 비고 |
|--------|---|------|
| TWO_TOWER_ENABLED | true | Two-Tower 후보 생성 활성화 |
| RERANKER_ENABLED | true | LightGBM 재랭킹 활성화 |
| EXPERIMENT_WEIGHTS | control:34,test_a:33,test_b:33 | A/B 그룹 비율 (이미 기본값일 수 있음) |

### 작업

1. **config.py에서 기본값 확인**
```bash
grep -n "TWO_TOWER_ENABLED\|RERANKER_ENABLED\|EXPERIMENT_WEIGHTS" backend/app/core/config.py
```
→ 기본값이 True면 환경변수 안 넣어도 되지만, 명시적으로 넣는 것을 권장

2. **Railway 환경변수 설정**
```bash
# Railway CLI
railway variables set TWO_TOWER_ENABLED=true
railway variables set RERANKER_ENABLED=true
```
또는 Railway 대시보드 → Variables 탭에서 수동 추가

3. **기존 환경변수 충돌 확인** — 이미 설정된 변수 목록 확인
```bash
railway variables list
```

---

## 완료 조건
- [ ] `alembic current`로 마이그레이션 상태 확인
- [ ] 로컬 DB에서 `alembic upgrade head` 테스트 성공
- [ ] 프로덕션 DB에 reco_impressions/interactions/judgments 3테이블 생성됨
- [ ] TWO_TOWER_ENABLED=true, RERANKER_ENABLED=true 환경변수 설정됨
- [ ] 기존 테이블·환경변수와 충돌 없음

## 다음 단계
Step 5: git push → CI 통과 → Railway 배포 → 배포 후 검증