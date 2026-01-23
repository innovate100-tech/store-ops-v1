-- ============================================
-- PHASE 10 / STEP 10-4: 설계 데이터 DB화
-- ============================================
-- 목적: session_state로만 저장되던 설계 데이터를 Supabase DB에 영구 저장(SSOT)
-- 대상: 메뉴 역할 태그, 재료 설계 상태, 설계 루틴 로그
-- ============================================

-- ============================================
-- STEP 1: menu_portfolio_state 테이블
-- ============================================
-- 메뉴별 역할 태그(미끼/볼륨/마진) SSOT
CREATE TABLE IF NOT EXISTS menu_portfolio_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    menu_id UUID NOT NULL REFERENCES menu_master(id) ON DELETE CASCADE,
    role_tag TEXT NULL CHECK (role_tag IN ('미끼', '볼륨', '마진')),
    updated_by UUID NULL REFERENCES auth.users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(store_id, menu_id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_menu_portfolio_state_store_id ON menu_portfolio_state(store_id);
CREATE INDEX IF NOT EXISTS idx_menu_portfolio_state_menu_id ON menu_portfolio_state(menu_id);

-- ============================================
-- STEP 2: ingredient_structure_state 테이블
-- ============================================
-- 재료별 설계 상태(대체 가능/발주유형/메모) SSOT
CREATE TABLE IF NOT EXISTS ingredient_structure_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    is_substitutable BOOLEAN NULL,
    order_type TEXT NULL CHECK (order_type IN ('single', 'multi', 'unset')),
    substitute_memo TEXT NULL,
    strategy_memo TEXT NULL,
    updated_by UUID NULL REFERENCES auth.users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(store_id, ingredient_id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_ingredient_structure_state_store_id ON ingredient_structure_state(store_id);
CREATE INDEX IF NOT EXISTS idx_ingredient_structure_state_ingredient_id ON ingredient_structure_state(ingredient_id);

-- ============================================
-- STEP 3: design_routine_log 테이블
-- ============================================
-- 설계 루틴 체크(주간/월간 완료 기록) SSOT
CREATE TABLE IF NOT EXISTS design_routine_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    routine_type TEXT NOT NULL CHECK (routine_type IN ('weekly_design_check', 'monthly_structure_review')),
    period_key TEXT NOT NULL,  -- ex) '2026-W04', '2026-01'
    completed_by UUID NULL REFERENCES auth.users(id),
    completed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(store_id, routine_type, period_key)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_design_routine_log_store_id ON design_routine_log(store_id);
CREATE INDEX IF NOT EXISTS idx_design_routine_log_routine_type ON design_routine_log(routine_type, period_key);

-- ============================================
-- STEP 4: RLS (Row Level Security) 활성화
-- ============================================
ALTER TABLE menu_portfolio_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_structure_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE design_routine_log ENABLE ROW LEVEL SECURITY;

-- ============================================
-- STEP 5: RLS 정책 - menu_portfolio_state
-- ============================================
-- SELECT: 자신의 매장 데이터만 조회
CREATE POLICY "Users can view menu_portfolio_state from their store"
    ON menu_portfolio_state FOR SELECT
    USING (store_id = get_user_store_id());

-- INSERT: 자신의 매장에만 삽입
CREATE POLICY "Users can insert menu_portfolio_state to their store"
    ON menu_portfolio_state FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

-- UPDATE: 자신의 매장 데이터만 수정
CREATE POLICY "Users can update menu_portfolio_state in their store"
    ON menu_portfolio_state FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

-- DELETE: 자신의 매장 데이터만 삭제
CREATE POLICY "Users can delete menu_portfolio_state from their store"
    ON menu_portfolio_state FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- STEP 6: RLS 정책 - ingredient_structure_state
-- ============================================
-- SELECT: 자신의 매장 데이터만 조회
CREATE POLICY "Users can view ingredient_structure_state from their store"
    ON ingredient_structure_state FOR SELECT
    USING (store_id = get_user_store_id());

-- INSERT: 자신의 매장에만 삽입
CREATE POLICY "Users can insert ingredient_structure_state to their store"
    ON ingredient_structure_state FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

-- UPDATE: 자신의 매장 데이터만 수정
CREATE POLICY "Users can update ingredient_structure_state in their store"
    ON ingredient_structure_state FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

-- DELETE: 자신의 매장 데이터만 삭제
CREATE POLICY "Users can delete ingredient_structure_state from their store"
    ON ingredient_structure_state FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- STEP 7: RLS 정책 - design_routine_log
-- ============================================
-- SELECT: 자신의 매장 데이터만 조회
CREATE POLICY "Users can view design_routine_log from their store"
    ON design_routine_log FOR SELECT
    USING (store_id = get_user_store_id());

-- INSERT: 자신의 매장에만 삽입
CREATE POLICY "Users can insert design_routine_log to their store"
    ON design_routine_log FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

-- UPDATE: 자신의 매장 데이터만 수정
CREATE POLICY "Users can update design_routine_log in their store"
    ON design_routine_log FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

-- DELETE: 자신의 매장 데이터만 삭제
CREATE POLICY "Users can delete design_routine_log from their store"
    ON design_routine_log FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- STEP 8: updated_by/updated_at 자동화 트리거
-- ============================================
-- menu_portfolio_state 트리거
CREATE OR REPLACE FUNCTION update_menu_portfolio_state_meta()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_by = auth.uid();
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trigger_update_menu_portfolio_state_meta ON menu_portfolio_state;
CREATE TRIGGER trigger_update_menu_portfolio_state_meta
    BEFORE INSERT OR UPDATE ON menu_portfolio_state
    FOR EACH ROW
    EXECUTE FUNCTION update_menu_portfolio_state_meta();

-- ingredient_structure_state 트리거
CREATE OR REPLACE FUNCTION update_ingredient_structure_state_meta()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_by = auth.uid();
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trigger_update_ingredient_structure_state_meta ON ingredient_structure_state;
CREATE TRIGGER trigger_update_ingredient_structure_state_meta
    BEFORE INSERT OR UPDATE ON ingredient_structure_state
    FOR EACH ROW
    EXECUTE FUNCTION update_ingredient_structure_state_meta();

-- design_routine_log 트리거 (completed_by 자동 설정)
CREATE OR REPLACE FUNCTION update_design_routine_log_meta()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_by IS NULL THEN
        NEW.completed_by = auth.uid();
    END IF;
    NEW.completed_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trigger_update_design_routine_log_meta ON design_routine_log;
CREATE TRIGGER trigger_update_design_routine_log_meta
    BEFORE INSERT OR UPDATE ON design_routine_log
    FOR EACH ROW
    EXECUTE FUNCTION update_design_routine_log_meta();

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'PHASE 10 / STEP 10-4: 설계 데이터 DB화 테이블 생성 완료';
    RAISE NOTICE '생성된 테이블:';
    RAISE NOTICE '  1. menu_portfolio_state (메뉴 역할 태그)';
    RAISE NOTICE '  2. ingredient_structure_state (재료 설계 상태)';
    RAISE NOTICE '  3. design_routine_log (설계 루틴 로그)';
    RAISE NOTICE 'RLS 정책 및 트리거가 모두 설정되었습니다.';
END $$;
