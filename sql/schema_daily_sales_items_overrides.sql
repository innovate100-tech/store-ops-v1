-- ============================================
-- 판매량 우선순위 레이어: daily_sales_items_overrides
-- ============================================
-- 매출등록/판매량등록이 마감보다 우선 적용되도록 하는 오버라이드 테이블
-- ============================================

CREATE TABLE IF NOT EXISTS daily_sales_items_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    sale_date DATE NOT NULL,
    menu_id UUID NOT NULL REFERENCES menu_master(id) ON DELETE CASCADE,
    qty INTEGER NOT NULL DEFAULT 0 CHECK (qty >= 0),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES auth.users(id),
    note TEXT,
    
    -- 고유 제약: 같은 날짜, 같은 메뉴는 하나만
    UNIQUE(store_id, sale_date, menu_id)
);

-- ============================================
-- 인덱스 생성
-- ============================================
CREATE INDEX IF NOT EXISTS idx_daily_sales_items_overrides_store_date 
    ON daily_sales_items_overrides(store_id, sale_date);
CREATE INDEX IF NOT EXISTS idx_daily_sales_items_overrides_menu 
    ON daily_sales_items_overrides(menu_id);

-- ============================================
-- RLS 정책
-- ============================================
ALTER TABLE daily_sales_items_overrides ENABLE ROW LEVEL SECURITY;

-- 자신의 매장 데이터만 조회/수정 가능
CREATE POLICY "Users can view their own store overrides"
    ON daily_sales_items_overrides FOR SELECT
    USING (
        store_id IN (
            SELECT store_id FROM user_profiles 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their own store overrides"
    ON daily_sales_items_overrides FOR INSERT
    WITH CHECK (
        store_id IN (
            SELECT store_id FROM user_profiles 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their own store overrides"
    ON daily_sales_items_overrides FOR UPDATE
    USING (
        store_id IN (
            SELECT store_id FROM user_profiles 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete their own store overrides"
    ON daily_sales_items_overrides FOR DELETE
    USING (
        store_id IN (
            SELECT store_id FROM user_profiles 
            WHERE user_id = auth.uid()
        )
    );

-- ============================================
-- updated_at 자동 업데이트 트리거
-- ============================================
CREATE OR REPLACE FUNCTION update_daily_sales_items_overrides_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_daily_sales_items_overrides_updated_at
    BEFORE UPDATE ON daily_sales_items_overrides
    FOR EACH ROW
    EXECUTE FUNCTION update_daily_sales_items_overrides_updated_at();
