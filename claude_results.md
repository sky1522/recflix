# Phase 35: SVD 모델 프로덕션 배포 결과

## 날짜
2026-02-20

## SVD 모델 파일 정보

| 항목 | 값 |
|------|-----|
| 파일 경로 | `backend/data/movielens/svd_model.pkl` |
| 파일 크기 | 54 MB |
| git-lfs 추적 | `backend/data/movielens/*.pkl` |
| 모델 유형 | SVD (MovieLens 25M 기반), RMSE 0.8768 |

## git-lfs 설정 결과

```
$ git lfs ls-files
e76cb82509 * backend/data/embeddings/movie_embeddings.npy  (168 MB)
343853948b * backend/data/movielens/svd_model.pkl          (54 MB)
```

- `.gitattributes`에 `backend/data/movielens/*.pkl filter=lfs diff=lfs merge=lfs -text` 추가
- `.gitignore`에서 `svd_model.pkl` 차단 해제

## Railway 배포 문제 해결

### 문제 1: 413 Payload Too Large (216 MB)
- **원인**: `railway up`이 LFS 실제 파일(임베딩 168MB + SVD 54MB)을 업로드에 포함
- `.dockerignore`는 Docker 빌드 컨텍스트에만 적용, `railway up` 업로드에는 무관
- **해결**: 대용량 LFS 파일을 임시 이동 후 배포, Dockerfile에서 GitHub LFS URL로 빌드 시 다운로드

### 문제 2: Railway가 Dockerfile 무시 (Railpack 사용)
- **원인**: `railway.toml`이 `backend/` 안에 있어 Railway가 발견 못함
- Railway 빌드 컨텍스트가 repo 루트이므로 `backend/railway.toml` 미참조
- **해결**: 루트에 `railway.toml` 생성, `dockerfilePath = "backend/Dockerfile"` 설정

### 문제 3: startCommand `cd` 실행 불가
- **원인**: Railway가 startCommand를 셸 없이 직접 실행 → `cd`는 셸 내장 명령
- **해결**: Dockerfile에 `WORKDIR /app/backend` 설정 + `sh -c '...'` 래퍼

### 문제 4: `${PORT:-8000}` 미확장
- **원인**: Railway startCommand가 셸 없이 실행되어 변수 확장 안 됨
- **해결**: `sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'`

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `railway.toml` (신규, 루트) | Dockerfile 빌더 + startCommand 설정 |
| `.dockerignore` (신규, 루트) | frontend, docs, 대용량 데이터 제외 |
| `backend/Dockerfile` | repo 루트 컨텍스트 대응 (backend/ prefix + LFS 다운로드) |
| `backend/.dockerignore` | backend 전용 제외 규칙 |
| `.gitignore` | svd_model.pkl 차단 해제 |
| `.gitattributes` | *.pkl git-lfs 추적 |

## 프로덕션 검증

### 서버 시작 로그
```
2026-02-20 06:40:23 [INFO] app.main: Environment: production
2026-02-20 06:40:23 [INFO] app.main: Database: connected
2026-02-20 06:40:23 [INFO] app.main: Redis: enabled
2026-02-20 06:40:27 [INFO] app.api.v1.semantic_search: Loaded 42917 movie embeddings (1024 dims, 167.6 MB)
2026-02-20 06:40:27 [INFO] app.main: Semantic search: enabled
```

### 시맨틱 검색 (임베딩 다운로드 확인)
```
비오는 날 잔잔한 영화:
1. 레인 맨        | rel=0.629
2. 레이싱 인 더 레인 | rel=0.588
3. 눈부신 세상 끝에서, 너와 나 | rel=0.587
```
- **PASS** — 임베딩 168MB 정상 로드

### 홈 추천 (기본 기능)
```
Featured: 마티 슈프림
🔥 인기 영화: 마티 슈프림, 컨저링: 마지막 의식, 어벤져스 ...
⭐ 높은 평점: 빽 투 더 퓨쳐, 인생은 아름다워, 피아니스트 ...
☀️ 맑은 날 추천: 에브리씽 에브리웨어 올 앳 원스, 안녕 베일리 ...
😌 편안한 기분: 온워드: 단 하루의 기적, 내 어깨 위 고양이 ...
```
- **PASS** — 4개 섹션 정상 반환

### CF 모델 상태
- SVD 모델 파일: `/app/backend/data/movielens/svd_model.pkl` (빌드 시 다운로드)
- 경로 매칭: `recommendation_cf.py`의 `Path(__file__).parent×4 / "data" / "movielens" / "svd_model.pkl"` → `/app/backend/data/movielens/svd_model.pkl` ✓
- 로드 방식: Lazy singleton (첫 번째 CF 요청 시 로드)
- 비인증 상태에서는 CF 비활성 (정상 동작)
- 로그인 사용자가 추천 요청 시 CF 25% 가중치로 하이브리드 스코어에 반영 예정

## 배포 아키텍처 (최종)

```
railway up (repo root)
  ↓ (.dockerignore로 frontend, data 제외)
Railway Build (Dockerfile)
  ↓ COPY backend/ → /app/backend/
  ↓ curl → SVD model (54MB from GitHub LFS)
  ↓ curl → Embeddings (168MB from GitHub LFS)
  ↓ curl → Metadata files
Railway Deploy
  ↓ WORKDIR /app/backend
  ↓ sh -c 'uvicorn app.main:app --port $PORT'
Production Running ✓
```
