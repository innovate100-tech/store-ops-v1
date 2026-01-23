-- ============================================
-- Phase 8-A Step 2-A: RLS 정책 검증 쿼리
-- Step 2-A SQL 실행 후 이 쿼리들을 실행하여 검증
-- ============================================
-- 
-- ⚠️ 주의사항:
-- - 검증 1-3, 2-3은 실제 INSERT/UPDATE를 시도합니다.
-- - DO 블록 내에서 실행되므로 예외 발생 시 자동 롤백됩니다.
-- - 하지만 안전을 위해 테스트 환경에서만 실행하세요.
-- 
-- 검증 항목:
-- 1. 사용자 A가 본인 store만 조회 가능한지
-- 2. 사용자 A가 타 store_id로 INSERT/UPDATE 시도 시 실패하는지
-- 3. helper 함수가 타 store를 반환할 가능성이 없는지
-- ============================================

-- ============================================
-- 사전 준비: 테스트용 데이터 확인
-- ============================================

-- 현재 로그인한 사용자 정보 확인
SELECT 
    '현재 로그인 사용자' AS info,
    auth.uid() AS user_id,
    (SELECT email FROM auth.users WHERE id = auth.uid()) AS email;

-- 현재 사용자의 store_members 확인
SELECT 
    '현재 사용자의 store_members' AS info,
    sm.*,
    s.name AS store_name
FROM store_members sm
JOIN stores s ON sm.store_id = s.id
WHERE sm.user_id = auth.uid();

-- ============================================
-- 검증 1: store_members 테이블
-- ============================================

-- 검증 1-1: 자신의 멤버십 조회 (성공해야 함)
SELECT 
    '✅ 검증 1-1: 자신의 멤버십 조회' AS test_name,
    COUNT(*) AS result_count,
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ 성공: 자신의 멤버십 조회 가능'
        ELSE '❌ 실패: 멤버십 조회 불가'
    END AS result
FROM store_members
WHERE user_id = auth.uid();

-- 검증 1-2: 모든 store_members 조회 시도 (자신 것만 나와야 함)
SELECT 
    '✅ 검증 1-2: 모든 store_members 조회 (자신 것만)' AS test_name,
    COUNT(*) AS total_count,
    COUNT(CASE WHEN user_id = auth.uid() THEN 1 END) AS own_count,
    CASE 
        WHEN COUNT(*) = COUNT(CASE WHEN user_id = auth.uid() THEN 1 END) 
        THEN '✅ 성공: 자신의 멤버십만 조회됨'
        ELSE '❌ 실패: 타 사용자의 멤버십도 조회됨'
    END AS result
FROM store_members;

-- 검증 1-3: 타 사용자의 store_id로 INSERT 시도 (실패해야 함)
-- 실제 INSERT 시도 (DO 블록 내에서 예외 발생 시 자동 롤백)
DO $$
DECLARE
    test_store_id UUID;
    error_message TEXT;
BEGIN
    -- 타 사용자의 store_id 찾기
    SELECT s.id INTO test_store_id
    FROM stores s
    WHERE s.id NOT IN (
        SELECT store_id FROM store_members WHERE user_id = auth.uid()
    )
    LIMIT 1;
    
    IF test_store_id IS NULL THEN
        RAISE NOTICE '✅ 검증 1-3: 타 사용자 store_id 없음 (테스트 불가)';
    ELSE
        BEGIN
            -- 타 사용자 store_id로 INSERT 시도
            INSERT INTO store_members (store_id, user_id, role)
            VALUES (test_store_id, auth.uid(), 'manager');
            
            -- INSERT가 성공하면 정책 위반 (예외 발생시켜 롤백)
            RAISE EXCEPTION '❌ 검증 1-3 실패: 타 사용자 store_id로 INSERT 성공 (정책 위반)';
        EXCEPTION 
            WHEN insufficient_privilege THEN
                RAISE NOTICE '✅ 검증 1-3 성공: 타 사용자 store_id로 INSERT 실패 (정책 차단)';
            WHEN OTHERS THEN
                error_message := SQLERRM;
                IF error_message LIKE '%policy%' OR error_message LIKE '%row-level%' OR error_message LIKE '%permission%' THEN
                    RAISE NOTICE '✅ 검증 1-3 성공: 타 사용자 store_id로 INSERT 실패 (정책 차단)';
                ELSE
                    RAISE NOTICE '⚠️ 검증 1-3: INSERT 실패 (다른 이유: %)', error_message;
                END IF;
        END;
    END IF;
END $$;

-- ============================================
-- 검증 2: stores 테이블
-- ============================================

-- 검증 2-1: 자신이 멤버인 매장 조회 (성공해야 함)
SELECT 
    '✅ 검증 2-1: 자신이 멤버인 매장 조회' AS test_name,
    COUNT(*) AS result_count,
    CASE 
        WHEN COUNT(*) > 0 THEN '✅ 성공: 자신의 매장 조회 가능'
        ELSE '⚠️ 주의: 멤버인 매장이 없음 (정상일 수 있음)'
    END AS result
FROM stores s
WHERE EXISTS (
    SELECT 1 
    FROM store_members 
    WHERE user_id = auth.uid() 
    AND store_id = s.id
);

-- 검증 2-2: 모든 stores 조회 시도 (자신이 멤버인 것만 나와야 함)
SELECT 
    '✅ 검증 2-2: 모든 stores 조회 (자신이 멤버인 것만)' AS test_name,
    (SELECT COUNT(*) FROM stores) AS total_stores,
    COUNT(*) AS visible_stores,
    CASE 
        WHEN COUNT(*) <= (
            SELECT COUNT(*) 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
        THEN '✅ 성공: 자신이 멤버인 매장만 조회됨'
        ELSE '❌ 실패: 타 사용자의 매장도 조회됨'
    END AS result
FROM stores s
WHERE EXISTS (
    SELECT 1 
    FROM store_members 
    WHERE user_id = auth.uid() 
    AND store_id = s.id
);

-- 검증 2-3: 타 사용자의 store로 UPDATE 시도 (실패해야 함)
-- 실제 UPDATE 시도 (DO 블록 내에서 예외 발생 시 자동 롤백)
DO $$
DECLARE
    test_store_id UUID;
    error_message TEXT;
BEGIN
    -- 타 사용자의 store 찾기 (owner가 아닌 경우)
    SELECT s.id INTO test_store_id
    FROM stores s
    WHERE s.id NOT IN (
        SELECT store_id 
        FROM store_members 
        WHERE user_id = auth.uid() 
        AND role = 'owner'
    )
    LIMIT 1;
    
    IF test_store_id IS NULL THEN
        RAISE NOTICE '✅ 검증 2-3: 타 사용자 store 없음 (테스트 불가)';
    ELSE
        BEGIN
            -- 타 사용자 store로 UPDATE 시도
            UPDATE stores
            SET name = name || ' (테스트)'
            WHERE id = test_store_id;
            
            -- UPDATE가 성공하면 정책 위반 (예외 발생시켜 롤백)
            RAISE EXCEPTION '❌ 검증 2-3 실패: 타 사용자 store로 UPDATE 성공 (정책 위반)';
        EXCEPTION 
            WHEN insufficient_privilege THEN
                RAISE NOTICE '✅ 검증 2-3 성공: 타 사용자 store로 UPDATE 실패 (정책 차단)';
            WHEN OTHERS THEN
                error_message := SQLERRM;
                IF error_message LIKE '%policy%' OR error_message LIKE '%row-level%' OR error_message LIKE '%permission%' THEN
                    RAISE NOTICE '✅ 검증 2-3 성공: 타 사용자 store로 UPDATE 실패 (정책 차단)';
                ELSE
                    RAISE NOTICE '⚠️ 검증 2-3: UPDATE 실패 (다른 이유: %)', error_message;
                END IF;
        END;
    END IF;
END $$;

-- ============================================
-- 검증 3: user_profiles 테이블
-- ============================================

-- 검증 3-1: 본인 프로필 조회 (성공해야 함)
SELECT 
    '✅ 검증 3-1: 본인 프로필 조회' AS test_name,
    COUNT(*) AS result_count,
    CASE 
        WHEN COUNT(*) = 1 THEN '✅ 성공: 본인 프로필 조회 가능'
        WHEN COUNT(*) = 0 THEN '⚠️ 주의: 프로필이 없음'
        ELSE '❌ 실패: 여러 프로필 조회됨'
    END AS result
FROM user_profiles
WHERE id = auth.uid();

-- 검증 3-2: 모든 user_profiles 조회 시도 (본인 것만 나와야 함)
SELECT 
    '✅ 검증 3-2: 모든 user_profiles 조회 (본인 것만)' AS test_name,
    (SELECT COUNT(*) FROM user_profiles) AS total_profiles,
    COUNT(*) AS visible_profiles,
    CASE 
        WHEN COUNT(*) = 1 AND COUNT(CASE WHEN id = auth.uid() THEN 1 END) = 1
        THEN '✅ 성공: 본인 프로필만 조회됨'
        ELSE '❌ 실패: 타 사용자의 프로필도 조회됨'
    END AS result
FROM user_profiles
WHERE id = auth.uid();

-- ============================================
-- 검증 4: Helper 함수 동작 확인
-- ============================================

-- 검증 4-1: get_user_store_id() 함수가 자신의 store만 반환하는지
SELECT 
    '✅ 검증 4-1: get_user_store_id() 반환값 확인' AS test_name,
    get_user_store_id() AS returned_store_id,
    CASE 
        WHEN get_user_store_id() IS NULL THEN '⚠️ 주의: store_id가 NULL (멤버십 없음)'
        WHEN EXISTS (
            SELECT 1 
            FROM store_members 
            WHERE user_id = auth.uid() 
            AND store_id = get_user_store_id()
        ) THEN '✅ 성공: 자신의 store_id 반환'
        ELSE '❌ 실패: 타 사용자의 store_id 반환 가능성'
    END AS result;

-- 검증 4-2: get_user_store_ids() 함수가 자신의 stores만 반환하는지
SELECT 
    '✅ 검증 4-2: get_user_store_ids() 반환값 확인' AS test_name,
    COUNT(*) AS returned_store_count,
    (
        SELECT COUNT(*) 
        FROM store_members 
        WHERE user_id = auth.uid()
    ) AS expected_count,
    CASE 
        WHEN COUNT(*) = (
            SELECT COUNT(*) 
            FROM store_members 
            WHERE user_id = auth.uid()
        ) THEN '✅ 성공: 자신의 stores만 반환'
        ELSE '❌ 실패: 반환된 store 수가 예상과 다름'
    END AS result
FROM get_user_store_ids();

-- 검증 4-3: is_user_store_member() 함수가 올바르게 동작하는지
SELECT 
    '✅ 검증 4-3: is_user_store_member() 동작 확인' AS test_name,
    CASE 
        WHEN get_user_store_id() IS NOT NULL THEN
            CASE 
                WHEN is_user_store_member(get_user_store_id()) = TRUE 
                THEN '✅ 성공: 자신의 store에 대해 TRUE 반환'
                ELSE '❌ 실패: 자신의 store에 대해 FALSE 반환'
            END
        ELSE '⚠️ 주의: store_id가 NULL이어서 테스트 불가'
    END AS result;

-- ============================================
-- 검증 5: RLS 정책 존재 확인
-- ============================================

-- 검증 5-1: store_members 정책 확인
SELECT 
    '✅ 검증 5-1: store_members 정책 존재' AS test_name,
    COUNT(*) AS policy_count,
    CASE 
        WHEN COUNT(*) >= 3 THEN '✅ 성공: 정책이 존재함'
        ELSE '❌ 실패: 정책이 없거나 부족함'
    END AS result
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'store_members';

-- 검증 5-2: stores 정책 확인
SELECT 
    '✅ 검증 5-2: stores 정책 존재' AS test_name,
    COUNT(*) AS policy_count,
    CASE 
        WHEN COUNT(*) >= 3 THEN '✅ 성공: 정책이 존재함'
        ELSE '❌ 실패: 정책이 없거나 부족함'
    END AS result
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'stores';

-- 검증 5-3: user_profiles 정책 확인
SELECT 
    '✅ 검증 5-3: user_profiles 정책 존재' AS test_name,
    COUNT(*) AS policy_count,
    CASE 
        WHEN COUNT(*) >= 3 THEN '✅ 성공: 정책이 존재함'
        ELSE '❌ 실패: 정책이 없거나 부족함'
    END AS result
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'user_profiles';

-- ============================================
-- 검증 6: RLS 활성화 상태 확인
-- ============================================

SELECT 
    '✅ 검증 6: RLS 활성화 상태' AS test_name,
    tablename,
    rowsecurity AS rls_enabled,
    CASE 
        WHEN rowsecurity = TRUE THEN '✅ 활성화됨'
        ELSE '❌ 비활성화됨'
    END AS result
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('store_members', 'stores', 'user_profiles')
ORDER BY tablename;

-- ============================================
-- 종합 요약
-- ============================================

SELECT 
    '========================================' AS summary
UNION ALL
SELECT 
    'Phase 8-A Step 2-A 검증 완료'
UNION ALL
SELECT 
    '========================================'
UNION ALL
SELECT 
    '위 결과를 확인하여 모든 항목이 ✅인지 확인하세요.'
UNION ALL
SELECT 
    '특히 다음을 확인:'
UNION ALL
SELECT 
    '1. 자신의 데이터만 조회 가능한지'
UNION ALL
SELECT 
    '2. Helper 함수가 올바른 store_id를 반환하는지'
UNION ALL
SELECT 
    '3. RLS 정책이 모두 존재하는지'
UNION ALL
SELECT 
    '========================================'
UNION ALL
SELECT 
    '문제가 없으면 기존 앱 동작을 확인하세요.'
UNION ALL
SELECT 
    '========================================';
