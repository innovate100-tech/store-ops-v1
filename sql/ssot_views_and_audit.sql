-- ============================================
-- SSOT VIEW 및 AUDIT 테이블 생성
-- ============================================
-- 목적: daily_close 기반 공식 매출 SSOT 확립
--       daily_sales_items DELETE 금지 및 이력 관리
-- ============================================

-- ============================================
-- STEP 1: 공식 매출 SSOT VIEW
-- ============================================

-- (1) v_daily_sales_official: daily_close 기준 공식 매출 뷰
CREATE OR REPLACE VIEW v_daily_sales_official AS
SELECT 
    dc.store_id,
    dc.date,
    dc.total_sales,
    dc.card_sales,
    dc.cash_sales,
    dc.visitors,
    dc.memo,
    TRUE AS is_official,
    'daily_close' AS source
FROM daily_close dc
WHERE dc.total_sales IS NOT NULL;

-- (2) v_daily_sales_best_available: daily_close 우선, 없으면 sales 사용
-- 날짜별로 중복 없이 하나의 행만 반환
CREATE OR REPLACE VIEW v_daily_sales_best_available AS
SELECT 
    COALESCE(dc.store_id, s.store_id) AS store_id,
    COALESCE(dc.date, s.date) AS date,
    COALESCE(dc.total_sales, s.total_sales, 0) AS total_sales,
    COALESCE(dc.card_sales, s.card_sales, 0) AS card_sales,
    COALESCE(dc.cash_sales, s.cash_sales, 0) AS cash_sales,
    COALESCE(dc.visitors, nv.visitors, 0) AS visitors,
    dc.memo,
    CASE 
        WHEN dc.store_id IS NOT NULL THEN TRUE 
        ELSE FALSE 
    END AS is_official,
    CASE 
        WHEN dc.store_id IS NOT NULL THEN 'daily_close'
        ELSE 'sales'
    END AS source
FROM (
    -- 모든 날짜 수집 (daily_close와 sales의 UNION)
    SELECT DISTINCT store_id, date FROM daily_close
    UNION
    SELECT DISTINCT store_id, date FROM sales
) AS dates
LEFT JOIN daily_close dc ON dates.store_id = dc.store_id AND dates.date = dc.date
LEFT JOIN sales s ON dates.store_id = s.store_id AND dates.date = s.date
LEFT JOIN naver_visitors nv ON dates.store_id = nv.store_id AND dates.date = nv.date;

-- ============================================
-- STEP 2: daily_sales_items AUDIT 테이블
-- ============================================

CREATE TABLE IF NOT EXISTS daily_sales_items_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    menu_id UUID NOT NULL REFERENCES menu_master(id) ON DELETE CASCADE,
    action TEXT NOT NULL CHECK (action IN ('insert', 'update', 'soft_delete')),
    old_qty INTEGER,
    new_qty INTEGER,
    source TEXT NOT NULL CHECK (source IN ('close', 'override', 'import')),
    reason TEXT,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by UUID REFERENCES auth.users(id) ON DELETE SET NULL
);

-- Index for Performance
CREATE INDEX IF NOT EXISTS idx_daily_sales_items_audit_store_date 
    ON daily_sales_items_audit(store_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_sales_items_audit_menu 
    ON daily_sales_items_audit(menu_id);
CREATE INDEX IF NOT EXISTS idx_daily_sales_items_audit_changed_at 
    ON daily_sales_items_audit(changed_at);

-- Enable RLS
ALTER TABLE daily_sales_items_audit ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view audit from their store
CREATE POLICY "Users can view daily_sales_items_audit from their store"
    ON daily_sales_items_audit FOR SELECT
    USING (store_id = get_user_store_id());

-- RLS Policy: System can insert audit (SECURITY DEFINER 함수에서 사용)
CREATE POLICY "System can insert daily_sales_items_audit"
    ON daily_sales_items_audit FOR INSERT
    WITH CHECK (true);  -- SECURITY DEFINER 함수에서만 사용

-- ============================================
-- STEP 3: Audit 로깅 헬퍼 함수
-- ============================================

CREATE OR REPLACE FUNCTION log_daily_sales_item_change(
    p_store_id UUID,
    p_date DATE,
    p_menu_id UUID,
    p_action TEXT,
    p_old_qty INTEGER,
    p_new_qty INTEGER,
    p_source TEXT,
    p_reason TEXT DEFAULT NULL,
    p_changed_by UUID DEFAULT NULL
)
RETURNS void AS $$
BEGIN
    INSERT INTO daily_sales_items_audit (
        store_id, date, menu_id, action, old_qty, new_qty, source, reason, changed_by
    )
    VALUES (
        p_store_id, p_date, p_menu_id, p_action, p_old_qty, p_new_qty, p_source, p_reason, p_changed_by
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- STEP 4: save_daily_close_transaction 수정
-- ============================================
-- DELETE 제거, UPSERT + audit 구조로 변경
-- 기존 함수 삭제 후 새로 생성 (시그니처 변경으로 인한 충돌 방지)

-- 기존 함수 삭제 (모든 오버로드 버전)
DROP FUNCTION IF EXISTS save_daily_close_transaction(
    DATE, UUID, NUMERIC, NUMERIC, NUMERIC, INTEGER, BOOLEAN, BOOLEAN, BOOLEAN, BOOLEAN, TEXT, JSONB
) CASCADE;

DROP FUNCTION IF EXISTS save_daily_close_transaction(
    DATE, UUID, NUMERIC, NUMERIC, NUMERIC, INTEGER, BOOLEAN, BOOLEAN, BOOLEAN, BOOLEAN, TEXT, JSONB, UUID
) CASCADE;

-- 새 함수 생성 (p_changed_by 파라미터 추가)
CREATE FUNCTION save_daily_close_transaction(
    p_date DATE,
    p_store_id UUID,
    p_card_sales NUMERIC,
    p_cash_sales NUMERIC,
    p_total_sales NUMERIC,
    p_visitors INTEGER,
    p_out_of_stock BOOLEAN DEFAULT FALSE,
    p_complaint BOOLEAN DEFAULT FALSE,
    p_group_customer BOOLEAN DEFAULT FALSE,
    p_staff_issue BOOLEAN DEFAULT FALSE,
    p_memo TEXT DEFAULT NULL,
    p_sales_items JSONB DEFAULT NULL,
    p_changed_by UUID DEFAULT NULL
)
RETURNS void AS $$
DECLARE
    v_menu_id UUID;
    v_old_qty INTEGER;
    v_new_qty INTEGER;
    v_item JSONB;
BEGIN
    -- 트랜잭션 시작 (자동)
    
    -- 1. daily_close 저장 (단일 소스)
    INSERT INTO daily_close (
        store_id, date, card_sales, cash_sales, total_sales,
        visitors, out_of_stock, complaint, group_customer, staff_issue,
        memo, sales_items
    )
    VALUES (
        p_store_id, p_date, p_card_sales, p_cash_sales, p_total_sales,
        p_visitors, p_out_of_stock, p_complaint, p_group_customer, p_staff_issue,
        p_memo, p_sales_items
    )
    ON CONFLICT (store_id, date) DO UPDATE SET
        card_sales = EXCLUDED.card_sales,
        cash_sales = EXCLUDED.cash_sales,
        total_sales = EXCLUDED.total_sales,
        visitors = EXCLUDED.visitors,
        out_of_stock = EXCLUDED.out_of_stock,
        complaint = EXCLUDED.complaint,
        group_customer = EXCLUDED.group_customer,
        staff_issue = EXCLUDED.staff_issue,
        memo = EXCLUDED.memo,
        sales_items = EXCLUDED.sales_items,
        updated_at = NOW();
    
    -- 2. sales 저장 (호환성 - 파생 동기화)
    IF p_total_sales > 0 THEN
        INSERT INTO sales (store_id, date, card_sales, cash_sales, total_sales)
        VALUES (p_store_id, p_date, p_card_sales, p_cash_sales, p_total_sales)
        ON CONFLICT (store_id, date) DO UPDATE SET
            card_sales = EXCLUDED.card_sales,
            cash_sales = EXCLUDED.cash_sales,
            total_sales = EXCLUDED.total_sales,
            updated_at = NOW();
    END IF;
    
    -- 3. naver_visitors 저장 (호환성 - 파생 동기화)
    IF p_visitors > 0 THEN
        INSERT INTO naver_visitors (store_id, date, visitors)
        VALUES (p_store_id, p_date, p_visitors)
        ON CONFLICT (store_id, date) DO UPDATE SET
            visitors = EXCLUDED.visitors,
            updated_at = NOW();
    END IF;
    
    -- 4. daily_sales_items 저장 (UPSERT + AUDIT)
    -- ❌ DELETE 제거: 기존 DELETE 로직 완전 제거
    -- ✅ UPSERT 구조: 메뉴 단위로 upsert하며 변경 이력 기록
    IF p_sales_items IS NOT NULL 
       AND jsonb_typeof(p_sales_items) = 'array' 
       AND jsonb_array_length(p_sales_items) > 0 THEN
        
        -- 각 메뉴별로 UPSERT 처리
        FOR v_item IN SELECT * FROM jsonb_array_elements(p_sales_items)
        LOOP
            -- 메뉴 ID 찾기
            SELECT id INTO v_menu_id
            FROM menu_master
            WHERE store_id = p_store_id 
              AND name = v_item->>'menu_name';
            
            -- 메뉴를 찾지 못하면 스킵
            IF v_menu_id IS NULL THEN
                CONTINUE;
            END IF;
            
            v_new_qty := (v_item->>'quantity')::INTEGER;
            
            -- 기존 qty 조회 (audit용)
            SELECT COALESCE(qty, 0) INTO v_old_qty
            FROM daily_sales_items
            WHERE store_id = p_store_id 
              AND date = p_date 
              AND menu_id = v_menu_id;
            
            -- old_qty가 NULL이면 0으로 설정
            IF v_old_qty IS NULL THEN
                v_old_qty := 0;
            END IF;
            
            -- UPSERT: qty가 0보다 크면 upsert, 0이면 soft_delete 처리
            IF v_new_qty > 0 THEN
                -- INSERT or UPDATE
                INSERT INTO daily_sales_items (store_id, date, menu_id, qty)
                VALUES (p_store_id, p_date, v_menu_id, v_new_qty)
                ON CONFLICT (store_id, date, menu_id) DO UPDATE SET
                    qty = EXCLUDED.qty,
                    updated_at = NOW();
                
                -- Audit 기록
                IF v_old_qty = 0 THEN
                    -- INSERT
                    PERFORM log_daily_sales_item_change(
                        p_store_id, p_date, v_menu_id, 'insert',
                        NULL, v_new_qty, 'close', '점장 마감 저장', p_changed_by
                    );
                ELSIF v_old_qty != v_new_qty THEN
                    -- UPDATE
                    PERFORM log_daily_sales_item_change(
                        p_store_id, p_date, v_menu_id, 'update',
                        v_old_qty, v_new_qty, 'close', '점장 마감 저장', p_changed_by
                    );
                END IF;
            ELSE
                -- qty가 0이면 soft_delete (실제 삭제는 하지 않고 audit만 기록)
                IF v_old_qty > 0 THEN
                    PERFORM log_daily_sales_item_change(
                        p_store_id, p_date, v_menu_id, 'soft_delete',
                        v_old_qty, 0, 'close', '점장 마감 저장 (qty=0)', p_changed_by
                    );
                    -- 실제 row는 유지 (qty=0으로 업데이트)
                    INSERT INTO daily_sales_items (store_id, date, menu_id, qty)
                    VALUES (p_store_id, p_date, v_menu_id, 0)
                    ON CONFLICT (store_id, date, menu_id) DO UPDATE SET
                        qty = 0,
                        updated_at = NOW();
                END IF;
            END IF;
        END LOOP;
    END IF;
    
    -- 모든 작업이 성공하면 커밋 (자동)
    -- 실패 시 자동 롤백
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 함수 권한 설정
-- ============================================
GRANT EXECUTE ON FUNCTION save_daily_close_transaction TO authenticated;
GRANT EXECUTE ON FUNCTION log_daily_sales_item_change TO authenticated;

-- ============================================
-- VIEW 권한 설정
-- ============================================
GRANT SELECT ON v_daily_sales_official TO authenticated;
GRANT SELECT ON v_daily_sales_best_available TO authenticated;
