-- ============================================
-- RLS 정책 동적 생성 헬퍼 함수
-- 모든 테이블에 동일한 패턴의 RLS 정책을 자동으로 생성
-- ============================================

-- ============================================
-- 함수: 특정 테이블에 대한 RLS 정책 생성
-- ============================================
CREATE OR REPLACE FUNCTION create_rls_policies_for_table(
    table_name TEXT,
    store_id_column TEXT DEFAULT 'store_id'
)
RETURNS void AS $$
DECLARE
    policy_name TEXT;
BEGIN
    -- 기존 정책 삭제 (있다면)
    EXECUTE format('DROP POLICY IF EXISTS "Users can view %I from their store" ON %I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS "Users can insert %I to their store" ON %I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS "Users can update %I in their store" ON %I', table_name, table_name);
    EXECUTE format('DROP POLICY IF EXISTS "Users can delete %I from their store" ON %I', table_name, table_name);
    
    -- SELECT 정책
    EXECUTE format(
        'CREATE POLICY "Users can view %I from their store" ON %I FOR SELECT USING (%I = get_user_store_id())',
        table_name, table_name, store_id_column
    );
    
    -- INSERT 정책
    EXECUTE format(
        'CREATE POLICY "Users can insert %I to their store" ON %I FOR INSERT WITH CHECK (%I = get_user_store_id())',
        table_name, table_name, store_id_column
    );
    
    -- UPDATE 정책
    EXECUTE format(
        'CREATE POLICY "Users can update %I in their store" ON %I FOR UPDATE USING (%I = get_user_store_id()) WITH CHECK (%I = get_user_store_id())',
        table_name, table_name, store_id_column, store_id_column
    );
    
    -- DELETE 정책
    EXECUTE format(
        'CREATE POLICY "Users can delete %I from their store" ON %I FOR DELETE USING (%I = get_user_store_id())',
        table_name, table_name, store_id_column
    );
    
    RAISE NOTICE 'RLS policies created for table: %', table_name;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 함수: 모든 표준 테이블에 RLS 정책 일괄 생성
-- ============================================
CREATE OR REPLACE FUNCTION create_all_rls_policies()
RETURNS void AS $$
BEGIN
    -- 표준 store_id 컬럼을 가진 테이블들
    PERFORM create_rls_policies_for_table('sales');
    PERFORM create_rls_policies_for_table('naver_visitors');
    PERFORM create_rls_policies_for_table('menu_master');
    PERFORM create_rls_policies_for_table('ingredients');
    PERFORM create_rls_policies_for_table('recipes');
    PERFORM create_rls_policies_for_table('daily_sales_items');
    PERFORM create_rls_policies_for_table('inventory');
    PERFORM create_rls_policies_for_table('daily_close');
    PERFORM create_rls_policies_for_table('targets');
    PERFORM create_rls_policies_for_table('abc_history');
    PERFORM create_rls_policies_for_table('expense_structure');
    PERFORM create_rls_policies_for_table('suppliers');
    PERFORM create_rls_policies_for_table('ingredient_suppliers');
    PERFORM create_rls_policies_for_table('orders');
    
    RAISE NOTICE 'All RLS policies created successfully';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 사용 방법
-- ============================================
-- 1. 개별 테이블에 정책 생성:
--    SELECT create_rls_policies_for_table('sales');
--
-- 2. 모든 테이블에 일괄 생성:
--    SELECT create_all_rls_policies();
--
-- 3. 기존 정책을 업데이트하려면:
--    먼저 기존 정책을 DROP하고 함수를 실행하면 됩니다.
--    (함수 내부에서 자동으로 DROP 처리)

-- ============================================
-- 주의사항
-- ============================================
-- - user_profiles와 stores 테이블은 별도 정책이 필요하므로
--   이 함수로 생성하지 않습니다.
-- - 특수한 정책이 필요한 테이블도 수동으로 설정해야 합니다.
