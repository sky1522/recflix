# v2.0 배포 Step 2: Dockerfile에 v2.0 모델 파일 다운로드 추가 — 완료

> 작업일: 2026-02-27
> 변경 파일: `backend/Dockerfile`, `.gitattributes`

## 변경 내용

### 1. 모델 파일 Git LFS 등록

| 파일 | 경로 | 크기 | SHA256 |
|------|------|------|--------|
| model_v1.pt | backend/data/models/two_tower/ | 1.2MB | 55b024c2...e539 |
| faiss_index.bin | backend/data/models/two_tower/ | 21MB | d09001c3...f09e |
| item_embeddings_tt.npy | backend/data/models/two_tower/ | 21MB | 861274d2...654d |
| movie_id_map.json | backend/data/models/two_tower/ | 320KB | 261c66e0...204e |
| lgbm_v1.txt | backend/data/models/reranker/ | 98KB | 37e896e3...8ed7 |

### 2. .gitattributes LFS 패턴 추가

```
backend/data/models/two_tower/*.pt filter=lfs diff=lfs merge=lfs -text
backend/data/models/two_tower/*.bin filter=lfs diff=lfs merge=lfs -text
backend/data/models/two_tower/*.npy filter=lfs diff=lfs merge=lfs -text
backend/data/models/reranker/*.txt filter=lfs diff=lfs merge=lfs -text
```

### 3. Dockerfile 수정 (lines 44-60)

- 기존 패턴 동일: `curl -fSL` + SHA256 체크섬 검증
- LFS 바이너리: `media.githubusercontent.com/media/...`
- 일반 JSON: `raw.githubusercontent.com/...`
- 별도 RUN 레이어 → 기존 v1.0 모델 레이어 캐시 유지

### 4. 경로 일관성 검증

| config.py 경로 (WORKDIR 기준) | 컨테이너 절대 경로 |
|------|------|
| `data/models/two_tower/model_v1.pt` | `/app/backend/data/models/two_tower/model_v1.pt` |
| `data/models/two_tower/faiss_index.bin` | `/app/backend/data/models/two_tower/faiss_index.bin` |
| `data/models/two_tower/movie_id_map.json` | `/app/backend/data/models/two_tower/movie_id_map.json` |
| `data/models/reranker/lgbm_v1.txt` | `/app/backend/data/models/reranker/lgbm_v1.txt` |

## 완료 조건 체크

- [x] Dockerfile에 v2.0 모델 5개 파일 다운로드 로직 추가 (SHA256 검증 포함)
- [ ] `docker build -t recflix-test .` 성공 (빌드 진행 중)
- [ ] 컨테이너 내 모델 파일 존재 확인
- [x] TwoTowerRetriever, LGBMReranker 모델 로드 경로 일치 확인

## 다음 단계

Step 3: Railway 프로덕션 DB에 Alembic 마이그레이션 적용
