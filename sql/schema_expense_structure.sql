-- ============================================
-- Expense Structure Table (비용구조 - 월간 비용 입력)
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
    amount NUMERIC(12, 0) NOT NULL DEFAULT 0,
    notes TEXT,  -- 메모 (선택사항)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for Performance
CREATE INDEX IF NOT EXISTS idx_expense_structure_store_year_month ON expense_structure(store_id, year, month);
CREATE INDEX IF NOT EXISTS idx_expense_structure_category ON expense_structure(category);

-- Enable RLS
ALTER TABLE expense_structure ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Expense Structure
CREATE POLICY "Users can view expense_structure from their store"
    ON expense_structure FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert expense_structure to their store"
    ON expense_structure FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update expense_structure in their store"
    ON expense_structure FOR UPDATE
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can delete expense_structure from their store"
    ON expense_structure FOR DELETE
    USING (store_id = get_user_store_id());
