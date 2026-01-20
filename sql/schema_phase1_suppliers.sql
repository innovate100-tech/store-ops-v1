-- ============================================
-- Phase 1: 공급업체 및 발주 이력 관리 테이블
-- ============================================
-- 이 스크립트는 발주 관리 Phase 1 기능을 위한 테이블을 생성합니다.

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
-- Indexes for Performance
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
-- Enable Row Level Security (RLS)
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
