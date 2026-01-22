-- ============================================
-- 매출 저장 + daily_close 동기화 함수
-- ============================================
-- 매출등록 시 sales를 SSOT로 저장하고,
-- 동일 날짜에 daily_close가 존재하면 daily_close의 매출 필드도 동기화
-- ============================================

CREATE OR REPLACE FUNCTION save_sales_with_daily_close_sync(
    p_date DATE,
    p_store_id UUID,
    p_card_sales NUMERIC,
    p_cash_sales NUMERIC,
    p_total_sales NUMERIC
)
RETURNS void AS $$
BEGIN
    -- 1. sales 저장 (SSOT)
    INSERT INTO sales (store_id, date, card_sales, cash_sales, total_sales)
    VALUES (p_store_id, p_date, p_card_sales, p_cash_sales, p_total_sales)
    ON CONFLICT (store_id, date) DO UPDATE SET
        card_sales = EXCLUDED.card_sales,
        cash_sales = EXCLUDED.cash_sales,
        total_sales = EXCLUDED.total_sales,
        updated_at = NOW();
    
    -- 2. daily_close가 존재하면 매출 필드 동기화
    UPDATE daily_close
    SET 
        card_sales = p_card_sales,
        cash_sales = p_cash_sales,
        total_sales = p_total_sales,
        updated_at = NOW()
    WHERE store_id = p_store_id 
        AND date = p_date;
    
    -- daily_close가 없으면 아무것도 안 함 (생성하지 않음)
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 함수 권한 설정
-- ============================================
GRANT EXECUTE ON FUNCTION save_sales_with_daily_close_sync TO authenticated;
