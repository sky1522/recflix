# v2.0 배포 Step 1: requirements.txt ML 패키지 추가 — 완료

> 작업일: 2026-02-27
> 변경 파일: `backend/requirements.txt`

## 변경 내용

### 추가된 ML 패키지 (requirements.txt 맨 아래)

| 패키지 | 버전 | 비고 |
|--------|------|------|
| torch | 2.10.0+cpu | `--extra-index-url https://download.pytorch.org/whl/cpu` (~200MB) |
| lightgbm | 4.6.0 | LightGBM CTR 재랭커 |
| faiss-cpu | 1.13.2 | FAISS 벡터 검색 |

### numpy 버전 범프

- `1.26.3` → `1.26.4` (scipy==1.14.1이 numpy>=1.26.4 요구)

## 검증 결과

| 항목 | 결과 |
|------|------|
| `pip install -r requirements.txt` | ML 패키지 정상 (pandas 빌드는 기존 이슈) |
| `pip check` | No broken requirements found |
| `import torch; import lightgbm; import faiss` | OK |
| numpy 호환성 | torch(무관), lightgbm(>=1.17), faiss-cpu(>=1.25,<3.0) — 모두 호환 |

## 완료 조건 체크

- [x] requirements.txt에 torch(CPU), lightgbm, faiss-cpu 추가됨
- [x] `python -c "import torch; import lightgbm; import faiss; print('OK')"` 성공
- [x] `pip check` — No broken requirements found
- [x] 기존 패키지와 버전 충돌 없음

## 다음 단계

Step 2: Dockerfile 수정 (v2.0 모델 파일 다운로드 + SHA256 검증)
