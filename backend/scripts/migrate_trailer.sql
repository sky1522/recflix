-- Phase 47A: Add trailer_key column to movies table
-- Run against production DB:
--   psql -h <host> -U <user> -d <db> -f scripts/migrate_trailer.sql

ALTER TABLE movies ADD COLUMN IF NOT EXISTS trailer_key VARCHAR(20);

CREATE INDEX IF NOT EXISTS idx_movies_trailer_key
    ON movies (trailer_key) WHERE trailer_key IS NOT NULL;
