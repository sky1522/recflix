# Phase 49A: 시맨틱 재랭킹 튜닝 + scripts 문서화

**날짜**: 2026-02-24

## 변경/생성 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/api/v1/movies.py` | `_calculate_relevance` 재랭킹 공식 v2 |
| `backend/scripts/README.md` | 배치 스크립트 운영 가이드 (신규) |

## 재랭킹 공식 Before/After

| 항목 | Before (v1) | After (v2) |
|------|-------------|------------|
| **semantic** | 0.50 | **0.60** |
| **popularity** | 0.30 | **0.15** |
| **quality** | 0.20 | **0.25** |

## popularity 정규화 변경

| 항목 | Before | After |
|------|--------|-------|
| **입력** | `vote_count` | `popularity` (TMDB 인기도) |
| **정규화** | `log1p(vote_count) / log1p(50000)` | `log1p(popularity) / log1p(1000)` |
| **효과** | 투표수 기반, 대작 편향 | 인기도 log 스케일, 인디 영화 노출 증가 |

예시: popularity 10 vs 10000
- Before: 차이 비율 ~3x
- After (log): `log(11)/log(1001)` ≈ 0.35 vs `log(10001)/log(1001)` ≈ 1.33 → 차이 ~3.8x로 압축

## scripts/README.md 요약

- 전체 16개 스크립트 분류: 수집/갱신, 유사도 계산, 데이터 처리, DB 마이그레이션
- 필수 환경변수 4개 (DATABASE_URL, TMDB_API_KEY, ANTHROPIC_API_KEY, VOYAGE_API_KEY)
- 월 1회 정기 갱신 체크리스트: trailers → similar_movies → (선택) emotion_tags
- 각 스크립트 실행 예시 포함

## GitHub Actions 워크플로우

**생략** — 사유:
- `compute_similar_movies.py`에 `DATABASE_URL`이 localhost로 하드코딩됨
- 환경변수 대응 수정은 "비즈니스 로직 외 변경 금지" 규칙에 해당
- 대신 `scripts/README.md`에 수동 실행 가이드 문서화

## 검증 결과

| 항목 | 결과 |
|------|------|
| `ruff check app/` | 0 issues |
| `from app.main import app` | 정상 |
