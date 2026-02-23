-- ==============================================
-- Phase 4 Migration: A/B 테스트 + 소셜 로그인 + 온보딩 + 이벤트
-- 멱등 실행 가능 (IF NOT EXISTS / IF EXISTS 사용)
-- ==============================================

-- ============================
-- 1. users 테이블 컬럼 추가
-- ============================

-- Phase 4-1: A/B 테스트 experiment_group
ALTER TABLE users ADD COLUMN IF NOT EXISTS experiment_group VARCHAR(10) NOT NULL DEFAULT 'control';

-- 기존 사용자 3등분 배정 (이미 배정된 경우 skip)
UPDATE users SET experiment_group = CASE
    WHEN id % 3 = 0 THEN 'control'
    WHEN id % 3 = 1 THEN 'test_a'
    ELSE 'test_b'
END
WHERE experiment_group = 'control' AND id > 0;

-- Phase 4-2: 소셜 로그인 컬럼
ALTER TABLE users ADD COLUMN IF NOT EXISTS kakao_id VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(100) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(20) NOT NULL DEFAULT 'email';

-- Phase 4-3: 온보딩 컬럼
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_genres TEXT;  -- JSON 문자열 '["액션","SF"]'

-- users 인덱스
CREATE INDEX IF NOT EXISTS ix_users_kakao_id ON users (kakao_id) WHERE kakao_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id) WHERE google_id IS NOT NULL;

-- ============================
-- 2. users 컬럼 타입/제약조건 보정 (모델과 불일치 수정)
-- ============================

-- preferred_genres: text[] → TEXT (모델은 Text, JSON 문자열로 저장)
ALTER TABLE users ALTER COLUMN preferred_genres TYPE TEXT USING preferred_genres::TEXT;

-- auth_provider: nullable → NOT NULL (모든 행이 값 있음)
UPDATE users SET auth_provider = 'email' WHERE auth_provider IS NULL;
ALTER TABLE users ALTER COLUMN auth_provider SET NOT NULL;
ALTER TABLE users ALTER COLUMN auth_provider SET DEFAULT 'email';

-- onboarding_completed: nullable → NOT NULL (모든 행이 값 있음)
UPDATE users SET onboarding_completed = false WHERE onboarding_completed IS NULL;
ALTER TABLE users ALTER COLUMN onboarding_completed SET NOT NULL;
ALTER TABLE users ALTER COLUMN onboarding_completed SET DEFAULT false;

-- ============================
-- 3. user_events 테이블 생성
-- ============================

CREATE TABLE IF NOT EXISTS user_events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    session_id VARCHAR(64),
    event_type VARCHAR(50) NOT NULL,
    movie_id INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- user_events 인덱스
CREATE INDEX IF NOT EXISTS ix_user_events_event_type ON user_events (event_type);
CREATE INDEX IF NOT EXISTS ix_user_events_created_at ON user_events (created_at);
CREATE INDEX IF NOT EXISTS idx_events_user_time ON user_events (user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON user_events (event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_events_movie ON user_events (movie_id, event_type);
