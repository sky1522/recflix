# v2.0 배포 Step 2: Dockerfile에 v2.0 모델 파일 다운로드 추가

## 배경
현재 Dockerfile은 SVD 모델 + Voyage AI 임베딩만 다운로드(lines 28-42)하고 있음. Two-Tower 모델, FAISS 인덱스, LightGBM 모델이 컨테이너에 포함되지 않아 런타임에 모델 로드 실패 → fallback 동작.

## 작업 내용

`backend/Dockerfile`을 수정하여 v2.0 모델 파일 4개를 컨테이너 빌드 시 포함시켜줘.

### 추가해야 할 파일 (data/models/ 하위)

| 파일 | 경로 | 크기 | 용도 |
|------|------|------|------|
| model_v1.pt | data/models/two_tower/model_v1.pt | 1.2MB | Two-Tower PyTorch 모델 |
| faiss_index.bin | data/models/two_tower/faiss_index.bin | 21MB | FAISS 인덱스 |
| item_embeddings_tt.npy | data/models/two_tower/item_embeddings_tt.npy | 21MB | Item 임베딩 |
| movie_id_map.json | data/models/two_tower/movie_id_map.json | 320KB | 인덱스→movie_id 매핑 |
| lgbm_v1.txt | data/models/reranker/lgbm_v1.txt | 98KB | LightGBM 모델 |

### 방법 결정 — 현재 Dockerfile 확인 후 판단

기존 SVD/Voyage 파일이 어떻게 포함되는지 확인해줘:
1. **Git LFS + COPY** — 이미 Git LFS로 관리되어 `COPY . .`로 포함되는 경우 → data/models/two_tower/와 data/models/reranker/도 LFS에 추가하면 됨
2. **Dockerfile 내 curl/wget 다운로드** — GitHub Release 또는 Git LFS media URL로 다운로드하는 경우 → 동일 패턴으로 v2.0 모델도 다운로드 추가
3. **Railway Volume** — 외부 스토리지에서 마운트하는 경우 → 해당 볼륨에 모델 업로드

기존 패턴과 동일한 방식으로 v2.0 모델을 추가해줘.

### 주의사항

1. **Docker 레이어 캐시** — 모델 파일은 자주 변경되지 않으므로, requirements.txt 설치 레이어 이후에 COPY하여 코드 변경 시 모델 다운로드를 재실행하지 않도록
2. **SHA256 검증** — 기존에 체크섬 검증을 하고 있다면 v2.0 모델도 동일하게 추가. 없다면 생략 가능
3. **총 이미지 크기** — 기존 ~220MB(SVD+Voyage) + ~44MB(v2.0) = ~264MB. Railway 무료 티어 제한 확인
4. **torch CPU** — requirements.txt에서 이미 CPU 전용으로 설치하므로 Dockerfile에서 별도 처리 불필요
5. **경로 일관성** — TwoTowerRetriever와 LGBMReranker가 참조하는 모델 경로와 Dockerfile 내 경로가 일치하는지 반드시 확인
   - `backend/app/services/two_tower_retriever.py`의 모델 로드 경로
   - `backend/app/services/reranker.py`의 모델 로드 경로
   - config.py의 모델 경로 설정

## 완료 조건
- [ ] Dockerfile에 v2.0 모델 5개 파일이 컨테이너에 포함되는 로직 추가
- [ ] `docker build -t recflix-test .` 성공 (로컬 테스트)
- [ ] 컨테이너 내에서 모델 파일 존재 확인: `docker run recflix-test ls -la data/models/two_tower/ data/models/reranker/`
- [ ] TwoTowerRetriever, LGBMReranker 모델 로드 경로와 일치 확인

## 다음 단계
Step 3: Railway 프로덕션 DB에 Alembic 마이그레이션 적용