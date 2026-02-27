# v2.0 프로덕션 배포 완료

> 작업일: 2026-02-27

## 배포 결과 요약

| 항목 | 상태 |
|------|------|
| Railway 배포 | SUCCESS (bbcd4c5a) |
| Health 엔드포인트 | v2.0.0 |
| Two-Tower Retriever | loaded (42917 items) |
| LGBM Reranker | loaded |
| SVD CF Model | loaded (17471 items) |
| Semantic Search | enabled (42917 embeddings, 1024 dims) |
| DB | connected |
| Redis | connected |
| reco_impressions 로깅 | 정상 동작 확인 |

---

## 수행한 작업 (Steps 1-5)

### Step 1: requirements.txt ML 패키지 추가
- torch==2.10.0+cpu, lightgbm==4.6.0, faiss-cpu==1.13.2
- numpy 2.x로 업그레이드 (SVD pickle 호환성)

### Step 2: Dockerfile v2.0 모델 다운로드
- Two-Tower 모델 3개 + movie_id_map.json + LGBM 모델 1개
- SHA256 체크섬 검증 포함
- Git LFS로 대용량 파일 관리

### Step 3: Alembic 마이그레이션
- reco_impressions (12컬럼, 3인덱스)
- reco_interactions (10컬럼, 3인덱스)
- reco_judgments (7컬럼, 2인덱스)

### Step 4: Railway 환경변수
- TWO_TOWER_ENABLED=true
- RERANKER_ENABLED=true
- EXPERIMENT_WEIGHTS=control:34,test_a:33,test_b:33

### Step 5: CI 수정 + 배포 + 검증

#### CI 수정 사항
- ML 패키지 CI에서 제외 (grep -v torch|lightgbm|faiss-cpu)
- 환경변수 추가 (DATABASE_URL, JWT_SECRET_KEY)
- UUID→String(36) SQLite 호환성 (conftest.py)
- SVD pickle 예외 처리 broadening
- Railway CLI: npx @railway/cli@4.30.5 직접 실행

#### 배포 트러블슈팅
| 문제 | 원인 | 해결 |
|------|------|------|
| Docker 빌드 실패 | embedding_metadata.json SHA256 불일치 | 체크섬 재계산 |
| 413 Payload Too Large | LFS 모델 파일 258MB 업로드 시도 | .railwayignore 생성 |
| Railway CLI 설치 실패 | npm install -g 불안정 | npx 직접 실행 |
| CF 모델 로드 실패 | numpy 1.26 vs 2.x pickle 비호환 | numpy>=2.0.0 |

---

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `requirements.txt` (root) | ML 패키지 + numpy 2.x |
| `backend/requirements.txt` | ML 패키지 + numpy 2.x |
| `backend/Dockerfile` | v2.0 모델 다운로드 (lines 44-60) |
| `.gitattributes` | LFS 패턴 4개 추가 |
| `backend/data/models/` | 5개 모델 파일 (Git LFS) |
| `.github/workflows/ci.yml` | ML 제외, 환경변수, npx railway |
| `backend/tests/conftest.py` | UUID→String(36) 변환 |
| `backend/app/api/v1/recommendation_cf.py` | 예외 처리 broadening |
| `backend/app/api/v1/health.py` | two_tower/reranker 상태 추가 |
| `backend/app/services/two_tower_retriever.py` | lazy imports |
| `backend/app/services/reranker.py` | lazy imports |
| `.railwayignore` | LFS 파일 업로드 제외 |

---

## 프로덕션 검증 결과

### Health Endpoint
```json
{
    "status": "ok",
    "environment": "production",
    "database": "connected",
    "redis": "connected",
    "semantic_search": "enabled",
    "cf_model": "loaded",
    "two_tower": "loaded",
    "reranker": "loaded",
    "version": "v2.0.0"
}
```

### Startup Logs
```
Semantic search: enabled (42917 embeddings, 1024 dims)
FAISS: AVX512 support
TwoTowerRetriever loaded: 42917 items in index
LGBMReranker loaded: data/models/reranker/lgbm_v1.txt
CF 모델 로드: items=17471, global_mean=3.5309
impressions_logged: 199 items
```

### Recommendation API
```
algorithm_version: twotower_v1
request_id: 81085f1f-...
rows: 4 (인기, 높은평점, 날씨추천, 기분추천)
impressions: reco_impressions 테이블에 자동 로깅
```
