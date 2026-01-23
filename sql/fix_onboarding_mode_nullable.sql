-- ============================================
-- onboarding_mode 컬럼을 NULL 허용으로 변경
-- ============================================
-- 이 SQL은 Supabase SQL Editor에서 실행하세요.

-- onboarding_mode 컬럼을 NULL 허용으로 변경
DO $$
BEGIN
    -- 컬럼이 NOT NULL이면 NULL 허용으로 변경
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'onboarding_mode'
        AND is_nullable = 'NO'
    ) THEN
        -- NOT NULL 제약 제거
        ALTER TABLE user_profiles 
        ALTER COLUMN onboarding_mode DROP NOT NULL;
        
        RAISE NOTICE 'onboarding_mode 컬럼을 NULL 허용으로 변경 완료';
    ELSE
        RAISE NOTICE 'onboarding_mode 컬럼이 이미 NULL 허용이거나 존재하지 않습니다.';
    END IF;
END $$;

-- 확인 쿼리
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'user_profiles' 
AND column_name = 'onboarding_mode';
