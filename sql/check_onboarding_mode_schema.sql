-- ============================================
-- onboarding_mode 컬럼 상태 확인
-- ============================================
-- 이 SQL은 Supabase SQL Editor에서 실행하여 현재 상태를 확인하세요.

-- 1. 컬럼 정보 확인
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'user_profiles' 
AND column_name = 'onboarding_mode';

-- 2. CHECK 제약 확인
SELECT 
    constraint_name,
    check_clause
FROM information_schema.check_constraints
WHERE constraint_name LIKE '%onboarding_mode%';

-- 3. 최근 생성된 사용자의 onboarding_mode 확인
SELECT 
    id,
    onboarding_mode,
    created_at
FROM user_profiles
ORDER BY created_at DESC
LIMIT 5;
