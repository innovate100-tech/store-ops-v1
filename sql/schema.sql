-- ============================================
-- Store Operations v1 - Supabase Schema
-- RLS 기반 보안 정책 포함
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. Stores Table (매장 정보)
-- ============================================
CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 2. User Profiles Table (사용자 프로필 - auth.users와 연동)
-- ============================================
-- Note: auth.users의 id를 참조
-- email은 auth.users에 있으므로 여기에 저장하지 않음
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id) ON DELETE SET NULL,
    role TEXT DEFAULT 'manager',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_role CHECK (role IN ('manager', 'admin'))
);

-- ============================================
-- 3. Sales Table (매출 데이터)
-- ============================================
CREATE TABLE IF NOT EXISTS sales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    card_sales NUMERIC(12, 0) DEFAULT 0,
    cash_sales NUMERIC(12, 0) DEFAULT 0,
    total_sales NUMERIC(12, 0) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, date)
);

-- ============================================
-- 4. Naver Visitors Table (네이버 방문자수)
-- ============================================
CREATE TABLE IF NOT EXISTS naver_visitors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    visitors INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, date)
);

-- ============================================
-- 5. Menu Master Table (메뉴 마스터)
-- ============================================
CREATE TABLE IF NOT EXISTS menu_master (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    price NUMERIC(10, 0) NOT NULL,
    is_core BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, name)
);

-- ============================================
-- 6. Ingredients Table (재료 마스터)
-- ============================================
CREATE TABLE IF NOT EXISTS ingredients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    unit_cost NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, name)
);

-- ============================================
-- 7. Recipes Table (레시피 - 메뉴-재료 매핑)
-- ============================================
CREATE TABLE IF NOT EXISTS recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    menu_id UUID NOT NULL REFERENCES menu_master(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    qty NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, menu_id, ingredient_id)
);

-- ============================================
-- 8. Daily Sales Items Table (일일 판매 내역)
-- ============================================
CREATE TABLE IF NOT EXISTS daily_sales_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    menu_id UUID NOT NULL REFERENCES menu_master(id) ON DELETE CASCADE,
    qty INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, date, menu_id)
);

-- ============================================
-- 9. Inventory Table (재고 정보)
-- ============================================
CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    on_hand NUMERIC(10, 2) DEFAULT 0,
    safety_stock NUMERIC(10, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, ingredient_id)
);

-- ============================================
-- 10. Daily Close Table (일일 마감 통합 데이터)
-- ============================================
CREATE TABLE IF NOT EXISTS daily_close (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    card_sales NUMERIC(12, 0) DEFAULT 0,
    cash_sales NUMERIC(12, 0) DEFAULT 0,
    total_sales NUMERIC(12, 0) DEFAULT 0,
    visitors INTEGER DEFAULT 0,
    out_of_stock BOOLEAN DEFAULT FALSE,
    complaint BOOLEAN DEFAULT FALSE,
    group_customer BOOLEAN DEFAULT FALSE,
    staff_issue BOOLEAN DEFAULT FALSE,
    memo TEXT,
    sales_items JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, date)
);

-- ============================================
-- 11. Targets Table (목표 매출/비용 구조)
-- ============================================
CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    target_sales NUMERIC(12, 0) DEFAULT 0,
    target_cost_rate NUMERIC(5, 2) DEFAULT 0,
    target_labor_rate NUMERIC(5, 2) DEFAULT 0,
    target_rent_rate NUMERIC(5, 2) DEFAULT 0,
    target_other_rate NUMERIC(5, 2) DEFAULT 0,
    target_profit_rate NUMERIC(5, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, year, month)
);

-- ============================================
-- 12. ABC History Table (ABC 분석 히스토리)
-- ============================================
CREATE TABLE IF NOT EXISTS abc_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    menu_name TEXT NOT NULL,
    sales_qty INTEGER DEFAULT 0,
    sales_amount NUMERIC(12, 0) DEFAULT 0,
    contribution_margin NUMERIC(12, 0) DEFAULT 0,
    qty_ratio NUMERIC(5, 2) DEFAULT 0,
    sales_ratio NUMERIC(5, 2) DEFAULT 0,
    margin_ratio NUMERIC(5, 2) DEFAULT 0,
    abc_grade TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, year, month, menu_name)
);

-- ============================================
-- 13. Expense Structure Table (비용구조 - 월간 비용 입력)
-- ============================================
-- 5개 비용 카테고리: 임차료, 재료비, 인건비, 공과금, 부가세&카드수수료
-- 각 카테고리별로 세부 항목 입력 가능
CREATE TABLE IF NOT EXISTS expense_structure (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    category TEXT NOT NULL CHECK (category IN ('임차료', '재료비', '인건비', '공과금', '부가세&카드수수료')),
    item_name TEXT NOT NULL,  -- 세부 항목명 (예: "본점 임차료", "메인 요리사 급여" 등)
    amount NUMERIC(12, 2) NOT NULL DEFAULT 0,  -- 변동비는 비율(%)로 저장되므로 소수점 허용
    notes TEXT,  -- 메모 (선택사항)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Indexes for Performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_sales_store_date ON sales(store_id, date);
CREATE INDEX IF NOT EXISTS idx_visitors_store_date ON naver_visitors(store_id, date);
CREATE INDEX IF NOT EXISTS idx_menu_store ON menu_master(store_id);
CREATE INDEX IF NOT EXISTS idx_ingredients_store ON ingredients(store_id);
CREATE INDEX IF NOT EXISTS idx_recipes_store ON recipes(store_id);
CREATE INDEX IF NOT EXISTS idx_daily_sales_store_date ON daily_sales_items(store_id, date);
CREATE INDEX IF NOT EXISTS idx_inventory_store ON inventory(store_id);
CREATE INDEX IF NOT EXISTS idx_daily_close_store_date ON daily_close(store_id, date);
CREATE INDEX IF NOT EXISTS idx_targets_store_year_month ON targets(store_id, year, month);
CREATE INDEX IF NOT EXISTS idx_abc_history_store_year_month ON abc_history(store_id, year, month);
CREATE INDEX IF NOT EXISTS idx_user_profiles_store_id ON user_profiles(store_id);
CREATE INDEX IF NOT EXISTS idx_expense_structure_store_year_month ON expense_structure(store_id, year, month);
CREATE INDEX IF NOT EXISTS idx_expense_structure_category ON expense_structure(category);

-- ============================================
-- Helper Function: Get current user's store_id
-- ============================================
CREATE OR REPLACE FUNCTION get_user_store_id()
RETURNS UUID AS $$
BEGIN
    RETURN (
        SELECT store_id 
        FROM user_profiles 
        WHERE id = auth.uid()
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- Row Level Security (RLS) Policies
-- ============================================

-- Enable RLS on all tables (stores는 예외 - 관리자만 접근)
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE naver_visitors ENABLE ROW LEVEL SECURITY;
ALTER TABLE menu_master ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredients ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_sales_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_close ENABLE ROW LEVEL SECURITY;
ALTER TABLE targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE abc_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE expense_structure ENABLE ROW LEVEL SECURITY;

-- ============================================
-- RLS Policy: Stores
-- ============================================
-- 사용자는 자신의 매장만 조회 가능
CREATE POLICY "Users can view their own store"
    ON stores FOR SELECT
    USING (id = get_user_store_id());

-- ============================================
-- RLS Policy: User Profiles
-- ============================================
-- 사용자는 자신의 프로필만 조회 가능
CREATE POLICY "Users can view their own profile"
    ON user_profiles FOR SELECT
    USING (id = auth.uid());

-- ============================================
-- RLS Policy: Sales
-- ============================================
CREATE POLICY "Users can view sales from their store"
    ON sales FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert sales to their store"
    ON sales FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update sales in their store"
    ON sales FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete sales from their store"
    ON sales FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Naver Visitors
-- ============================================
CREATE POLICY "Users can view visitors from their store"
    ON naver_visitors FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert visitors to their store"
    ON naver_visitors FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update visitors in their store"
    ON naver_visitors FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete visitors from their store"
    ON naver_visitors FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Menu Master
-- ============================================
CREATE POLICY "Users can view menus from their store"
    ON menu_master FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert menus to their store"
    ON menu_master FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update menus in their store"
    ON menu_master FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete menus from their store"
    ON menu_master FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Ingredients
-- ============================================
CREATE POLICY "Users can view ingredients from their store"
    ON ingredients FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert ingredients to their store"
    ON ingredients FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update ingredients in their store"
    ON ingredients FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete ingredients from their store"
    ON ingredients FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Recipes
-- ============================================
CREATE POLICY "Users can view recipes from their store"
    ON recipes FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert recipes to their store"
    ON recipes FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update recipes in their store"
    ON recipes FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete recipes from their store"
    ON recipes FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Daily Sales Items
-- ============================================
CREATE POLICY "Users can view daily sales from their store"
    ON daily_sales_items FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert daily sales to their store"
    ON daily_sales_items FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update daily sales in their store"
    ON daily_sales_items FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete daily sales from their store"
    ON daily_sales_items FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Inventory
-- ============================================
CREATE POLICY "Users can view inventory from their store"
    ON inventory FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert inventory to their store"
    ON inventory FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update inventory in their store"
    ON inventory FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete inventory from their store"
    ON inventory FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Daily Close
-- ============================================
CREATE POLICY "Users can view daily close from their store"
    ON daily_close FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert daily close to their store"
    ON daily_close FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update daily close in their store"
    ON daily_close FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete daily close from their store"
    ON daily_close FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Targets
-- ============================================
CREATE POLICY "Users can view targets from their store"
    ON targets FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert targets to their store"
    ON targets FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update targets in their store"
    ON targets FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete targets from their store"
    ON targets FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: ABC History
-- ============================================
CREATE POLICY "Users can view abc history from their store"
    ON abc_history FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert abc history to their store"
    ON abc_history FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update abc history in their store"
    ON abc_history FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete abc history from their store"
    ON abc_history FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Expense Structure
-- ============================================
CREATE POLICY "Users can view expense_structure from their store"
    ON expense_structure FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert expense_structure to their store"
    ON expense_structure FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update expense_structure in their store"
    ON expense_structure FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete expense_structure from their store"
    ON expense_structure FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- 14. Suppliers Table (공급업체)
-- ============================================
CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    delivery_days TEXT,  -- 배송일 (예: "2" 또는 "월,수,금")
    min_order_amount NUMERIC(12, 0) DEFAULT 0,  -- 최소 주문금액
    delivery_fee NUMERIC(12, 0) DEFAULT 0,  -- 배송비
    notes TEXT,  -- 비고
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, name)
);

-- ============================================
-- 15. Ingredient Suppliers Table (재료-공급업체 매핑)
-- ============================================
CREATE TABLE IF NOT EXISTS ingredient_suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    unit_price NUMERIC(10, 2) NOT NULL,  -- 공급업체별 단가
    is_default BOOLEAN DEFAULT FALSE,  -- 기본 공급업체 여부
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, ingredient_id, supplier_id)
);

-- ============================================
-- 16. Orders Table (발주 이력)
-- ============================================
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    order_date DATE NOT NULL,  -- 발주일
    ingredient_id UUID NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    supplier_id UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    quantity NUMERIC(10, 2) NOT NULL,  -- 발주 수량
    unit_price NUMERIC(10, 2) NOT NULL,  -- 단가
    total_amount NUMERIC(12, 0) NOT NULL,  -- 총 금액
    status TEXT NOT NULL DEFAULT '예정',  -- 예정, 완료, 입고완료, 취소
    expected_delivery_date DATE,  -- 입고 예정일
    actual_delivery_date DATE,  -- 실제 입고일
    notes TEXT,  -- 비고
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_status CHECK (status IN ('예정', '완료', '입고완료', '취소'))
);

-- ============================================
-- Indexes for Suppliers, Ingredient Suppliers, Orders
-- ============================================
CREATE INDEX IF NOT EXISTS idx_suppliers_store ON suppliers(store_id);
CREATE INDEX IF NOT EXISTS idx_ingredient_suppliers_store ON ingredient_suppliers(store_id);
CREATE INDEX IF NOT EXISTS idx_ingredient_suppliers_ingredient ON ingredient_suppliers(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_ingredient_suppliers_supplier ON ingredient_suppliers(supplier_id);
CREATE INDEX IF NOT EXISTS idx_orders_store ON orders(store_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_ingredient ON orders(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_orders_supplier ON orders(supplier_id);

-- ============================================
-- Enable Row Level Security (RLS) for Phase 1 Tables
-- ============================================
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingredient_suppliers ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- ============================================
-- RLS Policy: Suppliers
-- ============================================
CREATE POLICY "Users can view suppliers from their store"
    ON suppliers FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert suppliers to their store"
    ON suppliers FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update suppliers in their store"
    ON suppliers FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete suppliers from their store"
    ON suppliers FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Ingredient Suppliers
-- ============================================
CREATE POLICY "Users can view ingredient_suppliers from their store"
    ON ingredient_suppliers FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert ingredient_suppliers to their store"
    ON ingredient_suppliers FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update ingredient_suppliers in their store"
    ON ingredient_suppliers FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete ingredient_suppliers from their store"
    ON ingredient_suppliers FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Orders
-- ============================================
CREATE POLICY "Users can view orders from their store"
    ON orders FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert orders to their store"
    ON orders FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update orders in their store"
    ON orders FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete orders from their store"
    ON orders FOR DELETE
    USING (store_id = get_user_store_id());
