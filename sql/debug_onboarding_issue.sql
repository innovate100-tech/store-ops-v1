-- ============================================
-- 온보딩 문제 디버깅 쿼리
-- ============================================
-- 이 SQL은 Supabase SQL Editor에서 실행하여 현재 상태를 확인하세요.

-- 1. 컬럼이 NULL 허용인지 확인
SELECT 
    column_name,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'user_profiles' 
AND column_name = 'onboarding_mode';

-- 2. 최근 생성된 사용자의 onboarding_mode 확인
SELECT 
    id,
    onboarding_mode,
    created_at,
    CASE 
        WHEN onboarding_mode IS NULL THEN 'NULL (온보딩 필요)'
        WHEN onboarding_mode = 'coach' THEN 'coach (온보딩 완료)'
        WHEN onboarding_mode = 'fast' THEN 'fast (온보딩 완료)'
        ELSE '기타: ' || onboarding_mode
    END AS status
FROM user_profiles
ORDER BY created_at DESC
LIMIT 10;

-- 3. 현재 로그인한 사용자 확인 (auth.users와 조인)
SELECT 
    au.id AS user_id,
    au.email,
    up.onboarding_mode,
    up.created_at AS profile_created_at,
    CASE 
        WHEN up.onboarding_mode IS NULL THEN '온보딩 필요'
        ELSE '온보딩 완료: ' || up.onboarding_mode
    END AS onboarding_status
FROM auth.users au
LEFT JOIN user_profiles up ON au.id = up.id
ORDER BY au.created_at DESC
LIMIT 10;
