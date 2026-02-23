# Phase 47A: TMDB 트레일러 데이터 수집 + API 반영

**날짜**: 2026-02-23

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `backend/app/models/movie.py` | `trailer_key` Column(String(20)) 추가 |
| `backend/scripts/migrate_trailer.sql` | ALTER TABLE + partial index 마이그레이션 |
| `backend/scripts/collect_trailers.py` | TMDB 트레일러 키 수집 배치 스크립트 (신규) |
| `backend/app/schemas/movie.py` | MovieListItem, MovieDetail에 `trailer_key` 필드 추가 |

## 핵심 변경사항

### 1. DB 스키마 (migrate_trailer.sql)
```sql
ALTER TABLE movies ADD COLUMN IF NOT EXISTS trailer_key VARCHAR(20);
CREATE INDEX IF NOT EXISTS idx_movies_trailer_key
    ON movies (trailer_key) WHERE trailer_key IS NOT NULL;
```

### 2. 배치 스크립트 (collect_trailers.py)
- **TMDB API**: `GET /movie/{id}/videos?language=ko-KR&include_video_language=ko,en`
- **선택 우선순위**: YouTube Trailer → official 우선 → 한국어 우선 → 최신순
- **Rate limit**: 0.05초 간격 (20 req/sec, TMDB 허용 ~40)
- **배치 처리**: 1000건씩 DB commit
- **재실행 안전**: `WHERE trailer_key IS NULL`만 대상
- **CLI**: `--limit N`, `--dry-run`, `--batch-size`
- **총 소요 예상**: 42,917편 × 0.05초 ≈ 36분

### 3. API 스키마
- `MovieListItem.trailer_key: str | None = None`
- `MovieDetail.trailer_key: str | None = None`
- `from_orm_with_genres()`, `from_orm_with_relations()` 모두 trailer_key 반영

## 검증 결과

| 항목 | 결과 |
|------|------|
| `ruff check app/ scripts/collect_trailers.py` | All checks passed |
| `python -c 'from app.main import app; print(app.title)'` | RecFlix (정상) |
| 스크립트 import 테스트 | Module loaded OK |
| SQL 문법 | 표준 DDL (IF NOT EXISTS 안전) |

## 사용법

```bash
# 1. 프로덕션 DB에 마이그레이션 적용
psql -h shinkansen.proxy.rlwy.net -p 20053 -U postgres -d railway -f scripts/migrate_trailer.sql

# 2. 트레일러 수집 (전체)
DATABASE_URL="postgresql://..." TMDB_API_KEY="..." python scripts/collect_trailers.py

# 3. 테스트 (5건만, DB 저장 안 함)
DATABASE_URL="postgresql://..." TMDB_API_KEY="..." python scripts/collect_trailers.py --limit 5 --dry-run
```
