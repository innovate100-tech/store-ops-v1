-- ============================================
-- Daily Close 트랜잭션 저장 함수
-- ============================================
-- 여러 테이블에 원자적으로 저장하여 데이터 무결성 보장
-- 실패 시 자동 롤백
-- ============================================

CREATE OR REPLACE FUNCTION save_daily_close_transaction(
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
    p_sales_items JSONB DEFAULT NULL
)
RETURNS void AS $$
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
    
    -- 2. sales 저장 (호환성)
    IF p_total_sales > 0 THEN
        INSERT INTO sales (store_id, date, card_sales, cash_sales, total_sales)
        VALUES (p_store_id, p_date, p_card_sales, p_cash_sales, p_total_sales)
        ON CONFLICT (store_id, date) DO UPDATE SET
            card_sales = EXCLUDED.card_sales,
            cash_sales = EXCLUDED.cash_sales,
            total_sales = EXCLUDED.total_sales,
            updated_at = NOW();
    END IF;
    
    -- 3. naver_visitors 저장 (호환성)
    IF p_visitors > 0 THEN
        INSERT INTO naver_visitors (store_id, date, visitors)
        VALUES (p_store_id, p_date, p_visitors)
        ON CONFLICT (store_id, date) DO UPDATE SET
            visitors = EXCLUDED.visitors,
            updated_at = NOW();
    END IF;
    
    -- 4. daily_sales_items 저장 (호환성)
    -- sales_items가 JSONB 배열인 경우 파싱하여 저장
    -- 안전성: jsonb_typeof로 배열인지 확인 후 jsonb_array_length 호출 (스칼라 오류 방지)
    IF p_sales_items IS NOT NULL 
       AND jsonb_typeof(p_sales_items) = 'array' 
       AND jsonb_array_length(p_sales_items) > 0 THEN
        -- 기존 항목 삭제
        DELETE FROM daily_sales_items
        WHERE store_id = p_store_id AND date = p_date;
        
        -- 새 항목 삽입
        INSERT INTO daily_sales_items (store_id, date, menu_id, qty)
        SELECT 
            p_store_id,
            p_date,
            mm.id AS menu_id,
            (item->>'quantity')::INTEGER AS qty
        FROM jsonb_array_elements(p_sales_items) AS item
        LEFT JOIN menu_master mm ON mm.store_id = p_store_id 
            AND mm.name = item->>'menu_name'
        WHERE (item->>'quantity')::INTEGER > 0
            AND mm.id IS NOT NULL;
    END IF;
    
    -- 모든 작업이 성공하면 커밋 (자동)
    -- 실패 시 자동 롤백
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 함수 권한 설정
-- ============================================
-- 인증된 사용자만 실행 가능
GRANT EXECUTE ON FUNCTION save_daily_close_transaction TO authenticated;

-- ============================================
-- 사용 예시
-- ============================================
-- SELECT save_daily_close_transaction(
--     '2024-01-20'::DATE,
--     'store-uuid-here'::UUID,
--     100000,  -- card_sales
--     50000,   -- cash_sales
--     150000,  -- total_sales
--     50,      -- visitors
--     FALSE,   -- out_of_stock
--     FALSE,   -- complaint
--     FALSE,   -- group_customer
--     FALSE,   -- staff_issue
--     '메모',  -- memo
--     '[{"menu_name": "김밥", "quantity": 10}]'::JSONB  -- sales_items
-- );
