-- ============================================
-- Phase C/F: 실제정산 관련 테이블 생성
-- Supabase SQL Editor에서 실행
-- ============================================

-- ============================================
-- 1. Cost Item Templates Table (비용 항목 템플릿)
-- ============================================
CREATE TABLE IF NOT EXISTS cost_item_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('임차료', '재료비', '인건비', '공과금', '부가세&카드수수료')),
    item_name TEXT NOT NULL,
    item_type TEXT DEFAULT 'normal' CHECK (item_type IN ('normal', 'fixed', 'percent')),
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_value NUMERIC(10, 2) DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, category, item_name)
);

-- Index for Performance
CREATE INDEX IF NOT EXISTS idx_cost_item_templates_store_category ON cost_item_templates(store_id, category);
CREATE INDEX IF NOT EXISTS idx_cost_item_templates_active ON cost_item_templates(store_id, is_active);

-- ============================================
-- 2. Actual Settlement Items Table (실제정산 월별 항목 값)
-- ============================================
CREATE TABLE IF NOT EXISTS actual_settlement_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    template_id UUID NOT NULL REFERENCES cost_item_templates(id) ON DELETE CASCADE,
    amount NUMERIC(12, 0),  -- 금액 (고정비/normal 항목용, NULL 허용)
    percent NUMERIC(5, 2),  -- 비율 (매출연동 항목용, NULL 허용)
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'final')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, year, month, template_id)
);

-- Index for Performance
CREATE INDEX IF NOT EXISTS idx_actual_settlement_items_store_year_month ON actual_settlement_items(store_id, year, month);
CREATE INDEX IF NOT EXISTS idx_actual_settlement_items_template ON actual_settlement_items(template_id);
CREATE INDEX IF NOT EXISTS idx_actual_settlement_items_status ON actual_settlement_items(store_id, year, month, status);

-- ============================================
-- Enable RLS
-- ============================================
ALTER TABLE cost_item_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE actual_settlement_items ENABLE ROW LEVEL SECURITY;

-- ============================================
-- RLS Policy: Cost Item Templates
-- ============================================
CREATE POLICY "Users can view cost_item_templates from their store"
    ON cost_item_templates FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert cost_item_templates to their store"
    ON cost_item_templates FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update cost_item_templates in their store"
    ON cost_item_templates FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete cost_item_templates from their store"
    ON cost_item_templates FOR DELETE
    USING (store_id = get_user_store_id());

-- ============================================
-- RLS Policy: Actual Settlement Items
-- ============================================
CREATE POLICY "Users can view actual_settlement_items from their store"
    ON actual_settlement_items FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert actual_settlement_items to their store"
    ON actual_settlement_items FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update actual_settlement_items in their store"
    ON actual_settlement_items FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete actual_settlement_items from their store"
    ON actual_settlement_items FOR DELETE
    USING (store_id = get_user_store_id());
