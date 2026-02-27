# v2.0 배포 Step 5: git push → CI → Railway 배포 → 검증

## 배경
Step 1~4 완료:
- ✅ requirements.txt에 torch/lightgbm/faiss-cpu 추가
- ✅ Dockerfile에 v2.0 모델 다운로드 추가
- ✅ Alembic 마이그레이션 적용 (reco_* 3테이블)
- ✅ Railway 환경변수 설정 (TWO_TOWER_ENABLED 등)

## 작업

### 1. 변경사항 커밋 + 푸시

```bash
cd /path/to/recflix
git add -A
git status  # 변경 파일 확인

# 커밋 메시지
git commit -m "v2.0: ML 파이프라인 프로덕션 배포 준비

- requirements.txt: torch(CPU), lightgbm, faiss-cpu 추가
- Dockerfile: Two-Tower/LGBM 모델 다운로드 + SHA256 검증
- .gitattributes: v2.0 모델 파일 LFS 등록
- numpy 1.26.3 → 1.26.4 (scipy 호환)"

git push origin main
```

### 2. CI 모니터링

GitHub Actions 확인:
- [ ] backend-lint (ruff check) 통과
- [ ] backend-test (pytest) 통과
- [ ] frontend-build (next build) 통과
- [ ] deploy-backend (railway up) 성공

CI 실패 시:
- torch CPU 인덱스 URL 문제 → pip install 로그 확인
- LFS 파일 다운로드 실패 → GitHub LFS quota 확인
- Dockerfile SHA256 불일치 → 해시값 재확인

### 3. 배포 후 검증

**3-1. 헬스체크**
```bash
curl https://backend-production-cff2.up.railway.app/api/v1/health
```
→ DB, Redis, SVD, 임베딩 + Two-Tower, LGBM 상태 확인

**3-2. 추천 API 호출 (비로그인)**
```bash
curl "https://backend-production-cff2.up.railway.app/api/v1/recommendations?weather=sunny&mood=relaxed"
```
→ 응답 정상 + 각 섹션에 영화 목록 반환 확인

**3-3. 추천 API 호출 (로그인 사용자)**
```bash
# 로그인하여 JWT 토큰 획득 후
curl -H "Authorization: Bearer {token}" \
  "https://backend-production-cff2.up.railway.app/api/v1/recommendations?weather=sunny&mood=relaxed&mbti=INFP"
```
→ algorithm_version 필드 확인 (hybrid_v1 / twotower_lgbm_v1 / twotower_v1 중 하나)

**3-4. Impression 로그 적재 확인**
```sql
-- Railway DB 접속 후
SELECT COUNT(*) FROM reco_impressions;
SELECT algorithm_version, COUNT(*) FROM reco_impressions GROUP BY algorithm_version;
```
→ 추천 호출 후 impression 레코드가 쌓이는지 확인

**3-5. 프론트엔드 동작 확인**
- https://jnsquery-reflix.vercel.app 접속
- 홈 추천 로딩 정상 확인
- 영화 클릭 → 상세 페이지 → request_id가 URL ?rid= 파라미터로 전달되는지 확인

### 4. Fallback 테스트 (선택)

TWO_TOWER_ENABLED=false로 잠시 변경 → 추천 호출 → algorithm_version이 hybrid_v1_fallback인지 확인 → 다시 true로 복원

## 완료 조건
- [ ] git push 성공
- [ ] GitHub Actions CI 전체 통과
- [ ] Railway 배포 완료 (빌드 로그에 모델 다운로드 성공 확인)
- [ ] /health 엔드포인트 정상
- [ ] 추천 API 응답 정상 + algorithm_version 확인
- [ ] reco_impressions에 로그 적재 확인
- [ ] 프론트엔드에서 추천 정상 로딩

## 문제 발생 시
- Railway 빌드 실패 → 빌드 로그에서 에러 위치 확인 (torch 설치, 모델 다운로드, SHA256 등)
- 추천 500 에러 → Railway 런타임 로그 확인 (모델 로드 실패, DB 연결 등)
- Fallback만 동작 → TWO_TOWER_ENABLED 환경변수 확인 + 모델 파일 존재 여부