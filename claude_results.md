# Phase 33-4: 시맨틱 검색 프로덕션 배포 + 최적화 결과

## 날짜
2026-02-20

## 생성/수정된 파일

| 파일 | 상태 | 설명 |
|------|------|------|
| `backend/app/api/v1/movies.py` | 수정 | 시맨틱 검색 단계별 타이밍 로그 추가 |

## 검색 시간 분석 (단계별)

### 로컬 (Redis 없음 — Voyage API 매번 호출)
| 단계 | 시간 |
|------|------|
| Voyage AI 임베딩 | ~4,560ms |
| NumPy 코사인 유사도 검색 | ~10ms |
| PostgreSQL DB 조회 + 필터 | ~50ms |
| **총 합계** | **~8,670ms** |

### 프로덕션 Railway (Redis 캐시 포함)
| 구분 | 시간 | 비고 |
|------|------|------|
| 1st request (cold) | 654.7ms | Voyage API + Redis 캐시 저장 |
| 2nd request (cache hit) | **2.2ms** | Redis 결과 캐시 히트 |
| 다른 쿼리 (cold) | 325.3ms | 임베딩 Redis 캐시 히트 (같은 세션) |

### 캐시 계층 구조
1. **결과 캐시** (Redis, 1시간 TTL): 동일 쿼리 → 2ms 이내
2. **임베딩 캐시** (Redis, 24시간 TTL): Voyage API 호출 스킵 → 300ms 이내
3. **미캐시** (Voyage API 직접 호출): 500-700ms

## Railway 배포 결과

```
$ railway up
Uploading... ✓
Build Logs: https://railway.com/project/...

$ railway logs
Loaded 42917 movie embeddings (1024 dims, 167.6 MB)
Semantic search: enabled
```

- VOYAGE_API_KEY 환경변수 신규 설정
- 176MB .npy 파일 포함 업로드 성공 (첫 시도 타임아웃, 재시도 성공)

## Vercel 배포 결과

```
$ npx vercel --prod
✓ Compiled successfully
Production: https://jnsquery-reflix.vercel.app [2m]
```

## 프로덕션 E2E 테스트 결과

### API 테스트 1: "비오는 날 혼자 보기 좋은 잔잔한 영화"
```
time=654.7ms fallback=False results=5
  You Are Alone (6.3) [sim:0.5961]
  Rain (6.2) [sim:0.5707]
  고독 (6.2) [sim:0.5454]
  Hysterical Blindness (6.3) [sim:0.5429]
  혼자 사는 사람들 (6.5) [sim:0.5399]
```

### API 테스트 2: "감동적인 가족 영화 추천"
```
time=325.3ms fallback=False results=5
  패밀리 이즈 패밀리 (5.9) [sim:0.5635]
  애들이 똑같아요 (6.5) [sim:0.56]
  윌러비 가족 (6.9) [sim:0.5593]
  When I Find the Ocean (6.3) [sim:0.5549]
  The Present (6.3) [sim:0.5542]
```

### Redis 캐시 히트 테스트
```
1st: 654.7ms → 2nd: 2.2ms (298x faster)
```

## 로컬 Redis 미실행 참고
- 로컬 개발 환경에서 Redis가 없으면 캐시 미동작 (매번 Voyage API 호출 ~4.5초)
- 프로덕션 Railway에서는 Redis 캐시 정상 동작 (결과 캐시 2ms, 임베딩 캐시 300ms)

## 커밋 내역
- `5a17a92` — 임베딩 데이터 git-lfs 추가
- 이번 커밋 — 타이밍 로그 추가

## Phase 33 전체 완료 요약
| Phase | 내용 | 상태 |
|-------|------|------|
| 33 설계 | 임베딩 아키텍처 설계 | ✅ |
| 33-1 | Backend 시맨틱 검색 구현 | ✅ |
| 33-2 | Frontend UI (자연어 감지 + AI 추천 섹션) | ✅ |
| 33-3 | 임베딩 데이터 git-lfs + 로컬 테스트 | ✅ |
| 33-4 | 프로덕션 배포 + 최적화 확인 | ✅ |
