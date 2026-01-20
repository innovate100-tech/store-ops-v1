-- ============================================
-- UPDATE 정책 중복 문제 해결
-- 모든 UPDATE 정책을 삭제하고 재생성
-- ============================================

-- ============================================
-- 방법 1: 모든 UPDATE 정책 삭제 (안전한 방법)
-- ============================================

-- 각 테이블의 모든 UPDATE 정책을 찾아서 삭제
-- PostgreSQL에서는 정책 이름이 정확히 일치해야 삭제됩니다.

-- sales 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'sales' 
        AND policyname LIKE '%update%' OR policyname LIKE '%Update%' OR policyname LIKE '%UPDATE%'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON sales', r.policyname);
    END LOOP;
END $$;

-- naver_visitors 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'naver_visitors' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON naver_visitors', r.policyname);
    END LOOP;
END $$;

-- menu_master 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'menu_master' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON menu_master', r.policyname);
    END LOOP;
END $$;

-- ingredients 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'ingredients' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON ingredients', r.policyname);
    END LOOP;
END $$;

-- recipes 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'recipes' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON recipes', r.policyname);
    END LOOP;
END $$;

-- daily_sales_items 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'daily_sales_items' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON daily_sales_items', r.policyname);
    END LOOP;
END $$;

-- inventory 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'inventory' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON inventory', r.policyname);
    END LOOP;
END $$;

-- daily_close 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'daily_close' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON daily_close', r.policyname);
    END LOOP;
END $$;

-- targets 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'targets' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON targets', r.policyname);
    END LOOP;
END $$;

-- abc_history 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'abc_history' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON abc_history', r.policyname);
    END LOOP;
END $$;

-- expense_structure 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'expense_structure' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON expense_structure', r.policyname);
    END LOOP;
END $$;

-- suppliers 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'suppliers' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON suppliers', r.policyname);
    END LOOP;
END $$;

-- ingredient_suppliers 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'ingredient_suppliers' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON ingredient_suppliers', r.policyname);
    END LOOP;
END $$;

-- orders 테이블
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT policyname 
        FROM pg_policies 
        WHERE tablename = 'orders' 
        AND (policyname ILIKE '%update%')
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON orders', r.policyname);
    END LOOP;
END $$;

-- ============================================
-- 방법 2: 모든 정책을 한 번에 삭제하는 함수
-- ============================================

CREATE OR REPLACE FUNCTION drop_all_update_policies()
RETURNS void AS $$
DECLARE
    r RECORD;
    table_list TEXT[] := ARRAY[
        'sales', 'naver_visitors', 'menu_master', 'ingredients', 'recipes',
        'daily_sales_items', 'inventory', 'daily_close', 'targets', 'abc_history',
        'expense_structure', 'suppliers', 'ingredient_suppliers', 'orders'
    ];
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY table_list
    LOOP
        FOR r IN 
            SELECT policyname 
            FROM pg_policies 
            WHERE schemaname = 'public' 
            AND tablename = table_name
            AND (policyname ILIKE '%update%')
        LOOP
            EXECUTE format('DROP POLICY IF EXISTS %I ON %I', r.policyname, table_name);
            RAISE NOTICE 'Dropped policy: % on table: %', r.policyname, table_name;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 사용 방법
-- ============================================
-- 1. 방법 2 함수 실행 (더 간단):
--    SELECT drop_all_update_policies();
--
-- 2. 그 다음 정책 재생성:
--    SELECT create_all_rls_policies();
--
-- 3. 완료! 이제 각 테이블당 정책이 정확히 4개만 있을 것입니다.
