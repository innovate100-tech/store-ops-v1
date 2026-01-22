-- ============================================
-- daily_sales_items_overrides + v_daily_sales_items_effective
-- ============================================
-- 사용법: Supabase Dashboard → SQL Editor → 이 파일 전체 복사 → 붙여넣기 → Run
-- (\i 등 psql 전용 명령 사용 안 함. Editor에서 그대로 실행 가능)
-- ============================================

-- ------------------------------------------------------------------------------
-- STEP 0: 현재 DB 상태 확인 (결과만 보시면 됩니다)
-- ------------------------------------------------------------------------------
-- 0-1) daily_sales_items.menu_id 타입 확인 → menu_id는 이 타입으로 overrides에 맞춥니다.
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'daily_sales_items'
  AND column_name = 'menu_id';

-- 0-2) overrides 테이블 / effective 뷰 존재 여부 (false면 아직 없음)
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'daily_sales_items_overrides'
) AS overrides_table_exists;

SELECT EXISTS (
    SELECT 1 FROM information_schema.views
    WHERE table_schema = 'public' AND table_name = 'v_daily_sales_items_effective'
) AS effective_view_exists;


-- ------------------------------------------------------------------------------
-- STEP 1: DDL — daily_sales_items_overrides 테이블 생성
-- menu_id는 daily_sales_items와 동일하게 UUID (REFERENCES menu_master(id))
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.daily_sales_items_overrides (
    store_id UUID NOT NULL REFERENCES public.stores(id) ON DELETE CASCADE,
    sale_date DATE NOT NULL,
    menu_id UUID NOT NULL REFERENCES public.menu_master(id) ON DELETE CASCADE,
    qty NUMERIC NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID NULL,
    note TEXT NULL,
    PRIMARY KEY (store_id, sale_date, menu_id)
);

CREATE INDEX IF NOT EXISTS idx_overrides_store_date
    ON public.daily_sales_items_overrides(store_id, sale_date);
CREATE INDEX IF NOT EXISTS idx_overrides_menu
    ON public.daily_sales_items_overrides(menu_id);


-- ------------------------------------------------------------------------------
-- STEP 2: DDL — v_daily_sales_items_effective 뷰 생성
-- base = daily_sales_items (date), override = overrides (sale_date)
-- FULL OUTER JOIN: 마감에 메뉴 수량 없이 판매량등록만 한 경우(override만 존재)도 포함
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.v_daily_sales_items_effective AS
SELECT
    COALESCE(b.store_id, o.store_id)   AS store_id,
    COALESCE(b.date, o.sale_date)      AS date,
    COALESCE(b.menu_id, o.menu_id)     AS menu_id,
    COALESCE(o.qty, b.qty, 0)          AS qty
FROM public.daily_sales_items b
FULL OUTER JOIN public.daily_sales_items_overrides o
    ON b.store_id = o.store_id
   AND b.date = o.sale_date
   AND b.menu_id = o.menu_id
WHERE COALESCE(o.qty, b.qty, 0) > 0;


-- ------------------------------------------------------------------------------
-- STEP 3: RLS — overrides 테이블 (기존 daily_sales_items와 동일 패턴, get_user_store_id 사용)
-- ------------------------------------------------------------------------------
ALTER TABLE public.daily_sales_items_overrides ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view daily_sales_items_overrides from their store" ON public.daily_sales_items_overrides;
DROP POLICY IF EXISTS "Users can insert daily_sales_items_overrides to their store" ON public.daily_sales_items_overrides;
DROP POLICY IF EXISTS "Users can update daily_sales_items_overrides in their store" ON public.daily_sales_items_overrides;
DROP POLICY IF EXISTS "Users can delete daily_sales_items_overrides from their store" ON public.daily_sales_items_overrides;

CREATE POLICY "Users can view daily_sales_items_overrides from their store"
    ON public.daily_sales_items_overrides FOR SELECT
    USING (store_id = get_user_store_id());

CREATE POLICY "Users can insert daily_sales_items_overrides to their store"
    ON public.daily_sales_items_overrides FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can update daily_sales_items_overrides in their store"
    ON public.daily_sales_items_overrides FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

CREATE POLICY "Users can delete daily_sales_items_overrides from their store"
    ON public.daily_sales_items_overrides FOR DELETE
    USING (store_id = get_user_store_id());


-- ------------------------------------------------------------------------------
-- STEP 4: 검증 — 테이블/뷰 조회 (0건이어도 에러 없으면 성공)
-- ------------------------------------------------------------------------------
SELECT * FROM public.daily_sales_items_overrides LIMIT 1;

SELECT * FROM public.v_daily_sales_items_effective LIMIT 5;
