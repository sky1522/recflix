-- ==============================================
-- Phase 4 Migration: A/B 테스트 + 소셜 로그인 + 온보딩
-- ==============================================

-- Phase 4-1: A/B 테스트 experiment_group (이미 적용된 경우 skip)
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

-- Phase 4-2: 온보딩 컬럼
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferred_genres TEXT;  -- JSON 문자열 '["액션","SF"]'

-- 인덱스
CREATE INDEX IF NOT EXISTS ix_users_kakao_id ON users (kakao_id) WHERE kakao_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id) WHERE google_id IS NOT NULL;
