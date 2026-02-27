# v2.0 배포 Step 1: requirements.txt ML 패키지 추가

## 배경
RecFlix v2.0 ML 파이프라인(Two-Tower + LightGBM + FAISS)이 코드상 완성되어 있지만, requirements.txt에 ML 패키지가 누락되어 Docker 빌드 후 런타임에 ModuleNotFoundError가 발생합니다.

## 작업 내용

`backend/requirements.txt`에 아래 패키지를 추가해줘:

```
torch --index-url https://download.pytorch.org/whl/cpu
lightgbm
faiss-cpu
```

### 주의사항

1. **torch는 CPU 전용으로 설치** — Railway에 GPU가 없으므로 `--index-url https://download.pytorch.org/whl/cpu` 사용. 이렇게 하면 torch 패키지 크기가 ~2GB → ~200MB로 줄어듦

2. **버전 핀 여부 확인** — 기존 requirements.txt의 패키지들이 버전 고정(`==`)을 사용하는지 확인하고, 동일한 스타일을 따를 것. 로컬에서 현재 사용 중인 버전을 `pip show torch lightgbm faiss-cpu`로 확인해서 핀

3. **의존성 충돌 확인** — 추가 후 `pip install -r requirements.txt --dry-run` 또는 실제 설치로 기존 패키지와 충돌이 없는지 확인

4. **numpy 호환성** — 기존 requirements.txt에 numpy가 있을 텐데, torch와 faiss-cpu가 요구하는 numpy 버전 범위와 충돌하지 않는지 확인

5. **Railway 빌드 시간 고려** — torch CPU 버전이라도 빌드 시간이 늘어나므로, pip cache를 활용할 수 있도록 requirements.txt에서 ML 패키지를 맨 아래에 배치 (Docker 레이어 캐시 활용)

## 완료 조건
- [ ] requirements.txt에 torch(CPU), lightgbm, faiss-cpu 추가됨
- [ ] `pip install -r requirements.txt`가 에러 없이 완료됨
- [ ] `python -c "import torch; import lightgbm; import faiss; print('OK')"` 성공
- [ ] 기존 패키지와 버전 충돌 없음

## 다음 단계
Step 2에서 Dockerfile을 수정하여 v2.0 모델 파일 다운로드를 추가합니다.