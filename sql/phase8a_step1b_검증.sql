-- ============================================
-- Phase 8-A Step 1-B: 스키마 변경 검증 쿼리
-- Step 1-A SQL 실행 후 이 쿼리들을 실행하여 검증
-- ============================================

-- ============================================
-- 1. 테이블 구조 확인
-- ============================================

-- 1-1. stores 테이블에 created_by 컬럼 확인
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'stores'
AND column_name = 'created_by';

-- 예상 결과: created_by 컬럼이 존재해야 함

-- 1-2. store_members 테이블 존재 확인
SELECT 
    table_name,
    table_type
FROM information_schema.tables
WHERE table_name = 'store_members';

-- 예상 결과: store_members 테이블이 존재해야 함

-- 1-3. store_members 테이블 구조 확인
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'store_members'
ORDER BY ordinal_position;

-- 예상 결과: id, store_id, user_id, role, created_at, updated_at 컬럼 존재

-- 1-4. store_members 제약 조건 확인
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
LEFT JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'store_members'
ORDER BY tc.constraint_type, tc.constraint_name;

-- 예상 결과:
-- - PRIMARY KEY (id)
-- - UNIQUE (store_id, user_id)
-- - FOREIGN KEY (store_id) → stores(id)
-- - FOREIGN KEY (user_id) → auth.users(id)

-- 1-5. user_profiles 테이블에 새 컬럼 확인
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'user_profiles'
AND column_name IN ('default_store_id', 'onboarding_mode')
ORDER BY column_name;

-- 예상 결과: default_store_id, onboarding_mode 컬럼 존재

-- 1-6. user_profiles.onboarding_mode 제약 확인
SELECT 
    tc.constraint_name,
    cc.check_clause
FROM information_schema.table_constraints AS tc
JOIN information_schema.check_constraints AS cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_name = 'user_profiles'
AND tc.constraint_type = 'CHECK'
AND cc.check_clause LIKE '%onboarding_mode%';

-- 예상 결과: onboarding_mode IN ('coach', 'fast') 제약 존재

-- ============================================
-- 2. 데이터 개수 확인
-- ============================================

-- 2-1. user_profiles 개수
SELECT 
    COUNT(*) AS total_user_profiles,
    COUNT(store_id) AS users_with_store_id,
    COUNT(default_store_id) AS users_with_default_store_id,
    COUNT(CASE WHEN default_store_id IS NULL THEN 1 END) AS users_with_null_default_store_id
FROM user_profiles;

-- 예상 결과: 
-- - total_user_profiles > 0
-- - users_with_store_id = users_with_default_store_id (마이그레이션 완료)

-- 2-2. store_members 개수
SELECT 
    COUNT(*) AS total_store_members,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT store_id) AS unique_stores
FROM store_members;

-- 예상 결과:
-- - total_store_members >= unique_users (한 사용자가 여러 매장 소속 가능)
-- - unique_users = users_with_store_id (마이그레이션 완료)

-- 2-3. user별 매장 수 분포 (0/1/2+)
SELECT 
    store_count_category,
    COUNT(*) AS user_count
FROM (
    SELECT 
        up.id AS user_id,
        COUNT(sm.store_id) AS store_count,
        CASE 
            WHEN COUNT(sm.store_id) = 0 THEN '0개'
            WHEN COUNT(sm.store_id) = 1 THEN '1개'
            ELSE '2개 이상'
        END AS store_count_category
    FROM user_profiles up
    LEFT JOIN store_members sm ON up.id = sm.user_id
    GROUP BY up.id
) AS user_store_counts
GROUP BY store_count_category
ORDER BY 
    CASE store_count_category
        WHEN '0개' THEN 1
        WHEN '1개' THEN 2
        ELSE 3
    END;

-- 예상 결과:
-- - 대부분의 사용자가 '1개' 또는 '2개 이상' 카테고리에 속함
-- - '0개'는 신규 가입자 또는 마이그레이션 누락 가능성

-- 2-4. default_store_id NULL 비율
SELECT 
    COUNT(*) AS total_users,
    COUNT(default_store_id) AS users_with_default_store_id,
    COUNT(CASE WHEN default_store_id IS NULL THEN 1 END) AS users_with_null_default_store_id,
    ROUND(
        COUNT(CASE WHEN default_store_id IS NULL THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS null_percentage
FROM user_profiles;

-- 예상 결과:
-- - null_percentage는 0% 또는 매우 낮은 값 (마이그레이션 완료)
-- - 신규 가입자만 NULL일 수 있음

-- ============================================
-- 3. 마이그레이션 데이터 일관성 확인
-- ============================================

-- 3-1. user_profiles.store_id와 store_members 일치 확인
SELECT 
    COUNT(*) AS mismatched_count
FROM user_profiles up
WHERE up.store_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 
    FROM store_members sm 
    WHERE sm.user_id = up.id 
    AND sm.store_id = up.store_id
);

-- 예상 결과: mismatched_count = 0 (모든 store_id가 store_members에 반영됨)

-- 3-2. user_profiles.store_id와 default_store_id 일치 확인
SELECT 
    COUNT(*) AS mismatched_count
FROM user_profiles up
WHERE up.store_id IS NOT NULL
AND up.default_store_id IS NULL;

-- 예상 결과: mismatched_count = 0 (모든 store_id가 default_store_id로 설정됨)

-- 3-3. store_members role 분포
SELECT 
    role,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / NULLIF(SUM(COUNT(*)) OVER (), 0), 2) AS percentage
FROM store_members
GROUP BY role
ORDER BY 
    CASE role
        WHEN 'owner' THEN 1
        WHEN 'manager' THEN 2
        WHEN 'staff' THEN 3
    END;

-- 예상 결과: role별 분포 확인 (대부분 'manager' 또는 'owner')

-- ============================================
-- 4. Helper 함수 동작 확인
-- ============================================

-- 4-1. get_user_store_id() 함수 존재 확인
SELECT 
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines
WHERE routine_name = 'get_user_store_id'
AND routine_schema = 'public';

-- 예상 결과: 함수가 존재해야 함

-- 4-2. get_user_store_ids() 함수 존재 확인
SELECT 
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines
WHERE routine_name = 'get_user_store_ids'
AND routine_schema = 'public';

-- 예상 결과: 함수가 존재해야 함

-- 4-3. is_user_store_member() 함수 존재 확인
SELECT 
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines
WHERE routine_name = 'is_user_store_member'
AND routine_schema = 'public';

-- 예상 결과: 함수가 존재해야 함

-- 4-4. 함수 보안 설정 확인
SELECT 
    routine_name,
    security_type
FROM information_schema.routines
WHERE routine_name IN ('get_user_store_id', 'get_user_store_ids', 'is_user_store_member')
AND routine_schema = 'public';

-- 예상 결과: security_type = 'DEFINER' (SECURITY DEFINER)

-- ============================================
-- 5. 인덱스 확인
-- ============================================

-- 5-1. stores.created_by 인덱스 확인
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'stores'
AND indexname = 'idx_stores_created_by';

-- 예상 결과: 인덱스 존재

-- 5-2. store_members 인덱스 확인
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'store_members'
ORDER BY indexname;

-- 예상 결과:
-- - idx_store_members_store_id
-- - idx_store_members_user_id
-- - idx_store_members_role

-- 5-3. user_profiles.default_store_id 인덱스 확인
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'user_profiles'
AND indexname = 'idx_user_profiles_default_store_id';

-- 예상 결과: 인덱스 존재

-- ============================================
-- 6. 종합 요약 쿼리
-- ============================================

SELECT 
    '=== Phase 8-A Step 1 검증 요약 ===' AS summary;

SELECT 
    '1. 테이블 구조' AS category,
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'stores' AND column_name = 'created_by')
        THEN '✅ stores.created_by 존재'
        ELSE '❌ stores.created_by 없음'
    END AS status
UNION ALL
SELECT 
    '1. 테이블 구조',
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'store_members')
        THEN '✅ store_members 테이블 존재'
        ELSE '❌ store_members 테이블 없음'
    END
UNION ALL
SELECT 
    '1. 테이블 구조',
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'default_store_id')
        THEN '✅ user_profiles.default_store_id 존재'
        ELSE '❌ user_profiles.default_store_id 없음'
    END
UNION ALL
SELECT 
    '1. 테이블 구조',
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'onboarding_mode')
        THEN '✅ user_profiles.onboarding_mode 존재'
        ELSE '❌ user_profiles.onboarding_mode 없음'
    END
UNION ALL
SELECT 
    '2. 데이터 마이그레이션',
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM user_profiles up
            WHERE up.store_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM store_members sm 
                WHERE sm.user_id = up.id AND sm.store_id = up.store_id
            )
        ) = 0
        THEN '✅ store_members 마이그레이션 완료'
        ELSE '❌ store_members 마이그레이션 누락'
    END
UNION ALL
SELECT 
    '2. 데이터 마이그레이션',
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM user_profiles 
            WHERE store_id IS NOT NULL AND default_store_id IS NULL
        ) = 0
        THEN '✅ default_store_id 설정 완료'
        ELSE '❌ default_store_id 설정 누락'
    END
UNION ALL
SELECT 
    '3. Helper 함수',
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'get_user_store_id')
        THEN '✅ get_user_store_id() 존재'
        ELSE '❌ get_user_store_id() 없음'
    END
UNION ALL
SELECT 
    '3. Helper 함수',
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'get_user_store_ids')
        THEN '✅ get_user_store_ids() 존재'
        ELSE '❌ get_user_store_ids() 없음'
    END
UNION ALL
SELECT 
    '3. Helper 함수',
    CASE 
        WHEN EXISTS (SELECT 1 FROM information_schema.routines WHERE routine_name = 'is_user_store_member')
        THEN '✅ is_user_store_member() 존재'
        ELSE '❌ is_user_store_member() 없음'
    END;

-- ============================================
-- 완료 메시지
-- ============================================

SELECT 
    '========================================' AS message
UNION ALL
SELECT 
    'Phase 8-A Step 1-B 검증 쿼리 실행 완료'
UNION ALL
SELECT 
    '위 결과를 확인하여 모든 항목이 ✅인지 확인하세요.'
UNION ALL
SELECT 
    '========================================';
