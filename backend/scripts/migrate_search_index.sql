-- Phase 42: pg_trgm 검색 인덱스 마이그레이션
-- 실행: psql -h <host> -U <user> -d <db> -f migrate_search_index.sql
-- CONCURRENTLY로 무중단 생성 (락 최소화)
-- 주의: CONCURRENTLY는 트랜잭션 내에서 실행 불가

-- 1. pg_trgm 확장 활성화
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. 한국어 제목 검색 인덱스 (title_ko ilike '%...%')
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_title_ko_trgm
    ON movies USING gin (title_ko gin_trgm_ops);

-- 3. 영어 제목 검색 인덱스 (title ilike '%...%')
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_title_trgm
    ON movies USING gin (title gin_trgm_ops);

-- 4. 출연진 검색 인덱스 (cast_ko ilike '%...%')
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_cast_ko_trgm
    ON movies USING gin (cast_ko gin_trgm_ops);

-- 검증: 인덱스 확인
-- SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'movies' AND indexname LIKE '%trgm%';
