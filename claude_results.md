# 문서 동기화 갭 분석

> 분석일: 2026-02-27

## 갭 요약

| 문서 | 갭 수 | 심각도 |
|------|-------|--------|
| CLAUDE.md | 5 | 높음 (핵심 구조 미반영) |
| PROGRESS.md | 2 | 높음 (v2.0 Phase 누락) |
| HANDOFF_CONTEXT.md | 6 | 높음 (v2.0 미반영) |
| .claude/skills/recommendation.md | 3 | 높음 (Two-Tower/LGBM 누락) |
| .claude/skills/deployment.md | 4 | 중간 (v2.0 배포 변경 미반영) |
| .claude/skills/database.md | 1 | 중간 (reco_* 테이블 누락) |
| docs/RECOMMENDATION_LOGIC.md | 1 | 낮음 (이미 일부 반영) |
| docs/ARCHITECTURE.md | 0 | 없음 (이미 v2.0 반영) |
| docs/PROJECT_INDEX.md | 2 | 낮음 |

## 문서별 갭 상세

### 1. CLAUDE.md

| # | 갭 | 현재 | 실제 |
|---|-----|------|------|
| 1 | services/ 목록 불완전 | weather.py, llm.py만 | +two_tower_retriever.py, reranker.py, reco_logger.py, interleaving.py, embedding.py |
| 2 | health.py 설명 불완전 | "DB/Redis/SVD/임베딩" | +Two-Tower, Reranker 상태 |
| 3 | reco_* 테이블 누락 | DB 모델에 없음 | reco_impressions, reco_interactions, reco_judgments 3테이블 추가됨 |
| 4 | config 설명 불완전 | "EXPERIMENT_WEIGHTS 포함" | +TWO_TOWER_*, RERANKER_* 설정 추가됨 |
| 5 | 알려진 이슈 패턴 누락 | 6개 | +Railway LFS 413 (.railwayignore), numpy 2.x pickle 호환성 |

### 2. PROGRESS.md

| # | 갭 | 현재 | 실제 |
|---|-----|------|------|
| 1 | v2.0 ML 파이프라인 Phase 누락 | Phase 52까지 (v1.1.0) | Phase 53: Two-Tower + LGBM 프로덕션 배포 (v2.0.0) |
| 2 | 해결한 이슈 누락 | #23까지 | +Dockerfile SHA256, .railwayignore, Railway CLI npx, numpy 2.x |

### 3. HANDOFF_CONTEXT.md

| # | 갭 | 현재 | 실제 |
|---|-----|------|------|
| 1 | 버전 | Phase 52, v1.1.0 | Phase 53, v2.0.0 |
| 2 | services/ 목록 누락 | weather.py, llm.py만 | +5개 서비스 모듈 |
| 3 | reco_* 테이블 누락 | DB 스키마에 없음 | 3테이블 추가 |
| 4 | Phase 53 누락 | Phase 52까지 | +Two-Tower + LGBM 배포 |
| 5 | health 엔드포인트 | DB/Redis/SVD/임베딩 | +two_tower, reranker |
| 6 | CI/CD 변경 미반영 | railway up | npx @railway/cli, ML 패키지 제외, lazy imports |

### 4. .claude/skills/recommendation.md

| # | 갭 | 현재 | 실제 |
|---|-----|------|------|
| 1 | Two-Tower 섹션 없음 | — | FAISS 42917 items, 200 후보 생성 |
| 2 | LGBM 재랭커 섹션 없음 | — | 76dim 피처, 200→50 재랭킹 |
| 3 | A/B 알고리즘 라우팅 없음 | — | control→hybrid_v1, test_a→twotower_lgbm_v1, test_b→twotower_v1 |

### 5. .claude/skills/deployment.md

| # | 갭 | 현재 | 실제 |
|---|-----|------|------|
| 1 | Dockerfile v2.0 모델 미반영 | 4개 파일 SHA256 | +5개 v2.0 모델 파일 |
| 2 | .railwayignore 누락 | — | LFS 파일 업로드 제외 |
| 3 | Railway 환경변수 누락 | — | TWO_TOWER_ENABLED, RERANKER_ENABLED |
| 4 | CI npx 변경 미반영 | `npm install -g @railway/cli` | `npx @railway/cli@4.30.5` |

### 6. .claude/skills/database.md

| # | 갭 | 현재 | 실제 |
|---|-----|------|------|
| 1 | reco_* 테이블 3개 누락 | — | reco_impressions(12col), reco_interactions(10col), reco_judgments(7col) |
