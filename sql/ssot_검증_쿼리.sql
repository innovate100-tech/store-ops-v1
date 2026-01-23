-- ============================================
-- SSOT 구현 검증 쿼리 세트
-- ============================================
-- 사용법: 아래 변수 값을 본인의 store_id와 날짜로 변경 후 실행
-- ============================================

-- 🔧 변수 설정 (여기 값을 변경하세요)
-- store_id는 실제 매장 UUID로 변경
-- 테스트 날짜는 실제 데이터가 있는 날짜로 변경
DO $$
DECLARE
    v_store_id UUID := 'your-store-id-here';  -- ⚠️ 여기를 실제 store_id로 변경
    v_test_date DATE := '2024-01-20';         -- ⚠️ 여기를 테스트할 날짜로 변경
    v_start_date DATE := CURRENT_DATE - INTERVAL '30 days';  -- 최근 30일
    v_end_date DATE := CURRENT_DATE;
BEGIN
    -- 변수는 아래 쿼리에서 사용됨
    RAISE NOTICE 'Store ID: %', v_store_id;
    RAISE NOTICE 'Test Date: %', v_test_date;
END $$;

-- ============================================
-- 1) 객체 존재 확인
-- ============================================

-- 1-1. VIEW 존재 확인
SELECT 
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('v_daily_sales_official', 'v_daily_sales_best_available')
ORDER BY table_name;
-- 기대 결과: 2개 행 (v_daily_sales_official, v_daily_sales_best_available)

-- 1-2. daily_sales_items_audit 테이블 존재 확인
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'daily_sales_items_audit'
ORDER BY ordinal_position;
-- 기대 결과: 11개 컬럼 (id, store_id, date, menu_id, action, old_qty, new_qty, source, reason, changed_at, changed_by)

-- 1-3. log_daily_sales_item_change 함수 존재 확인
SELECT 
    routine_name,
    routine_type,
    data_type as return_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'log_daily_sales_item_change';
-- 기대 결과: 1개 행 (함수 존재 확인)

-- 1-4. save_daily_close_transaction 함수 시그니처 확인
SELECT 
    routine_name,
    parameter_name,
    data_type,
    parameter_default
FROM information_schema.parameters
WHERE specific_schema = 'public'
  AND routine_name = 'save_daily_close_transaction'
ORDER BY ordinal_position;
-- 기대 결과: 13개 파라미터 (p_date부터 p_changed_by까지, p_changed_by가 마지막에 있어야 함)

-- ============================================
-- 2) 공식/보조 뷰 샘플 조회
-- ============================================
-- ⚠️ 아래 쿼리에서 'your-store-id-here'를 실제 store_id로 변경하세요

-- 2-1. v_daily_sales_official 샘플 조회 (최근 30일)
SELECT 
    date,
    total_sales,
    card_sales,
    cash_sales,
    visitors,
    is_official,
    source
FROM v_daily_sales_official
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC
LIMIT 10;
-- 기대 결과: daily_close가 있는 날짜만 조회, is_official=true, source='daily_close'

-- 2-2. v_daily_sales_best_available 샘플 조회 (최근 30일)
SELECT 
    date,
    total_sales,
    card_sales,
    cash_sales,
    visitors,
    is_official,
    source
FROM v_daily_sales_best_available
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC
LIMIT 10;
-- 기대 결과: daily_close 있으면 is_official=true, sales만 있으면 is_official=false

-- 2-3. 공식/보조 비교 조회 (같은 날짜 기준)
SELECT 
    COALESCE(o.date, b.date) AS date,
    o.is_official AS official_exists,
    o.source AS official_source,
    b.is_official AS best_is_official,
    b.source AS best_source,
    o.total_sales AS official_sales,
    b.total_sales AS best_sales
FROM v_daily_sales_best_available b
LEFT JOIN v_daily_sales_official o ON b.store_id = o.store_id AND b.date = o.date
WHERE b.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND b.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC
LIMIT 10;
-- 기대 결과: daily_close 있으면 official_exists=true, sales만 있으면 official_exists=NULL

-- ============================================
-- 3) audit 로깅 확인
-- ============================================
-- ⚠️ 아래 쿼리에서 'your-store-id-here'를 실제 store_id로 변경하세요

-- 3-1. audit 최신 20개 조회
SELECT 
    date,
    (SELECT name FROM menu_master WHERE id = a.menu_id) AS menu_name,
    action,
    old_qty,
    new_qty,
    source,
    reason,
    changed_at,
    changed_by
FROM daily_sales_items_audit a
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
ORDER BY changed_at DESC
LIMIT 20;
-- 기대 결과: 최근 변경 이력 20개, action은 'insert'/'update'/'soft_delete', source는 'close'/'override'/'import'

-- 3-2. 특정 날짜의 audit 조회
SELECT 
    date,
    (SELECT name FROM menu_master WHERE id = a.menu_id) AS menu_name,
    action,
    old_qty,
    new_qty,
    source,
    reason,
    changed_at
FROM daily_sales_items_audit a
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND date = '2024-01-20'::DATE  -- ⚠️ 여기를 테스트할 날짜로 변경
ORDER BY changed_at DESC;
-- 기대 결과: 해당 날짜의 모든 변경 이력

-- 3-3. audit 통계 (source별, action별)
SELECT 
    source,
    action,
    COUNT(*) AS count,
    MIN(changed_at) AS first_change,
    MAX(changed_at) AS last_change
FROM daily_sales_items_audit
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
GROUP BY source, action
ORDER BY source, action;
-- 기대 결과: source별, action별 통계 (close/override/import, insert/update/soft_delete)

-- ============================================
-- 4) SSOT 분리 확인 시나리오 쿼리
-- ============================================
-- ⚠️ 아래 쿼리에서 'your-store-id-here'를 실제 store_id로 변경하세요

-- 4-1. 시나리오 A: daily_close만 있는 날짜 확인
SELECT 
    dc.date,
    'daily_close만 존재' AS scenario,
    (SELECT COUNT(*) FROM v_daily_sales_official WHERE store_id = dc.store_id AND date = dc.date) AS official_count,
    (SELECT COUNT(*) FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date) AS best_count,
    (SELECT is_official FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date LIMIT 1) AS best_is_official,
    (SELECT source FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date LIMIT 1) AS best_source
FROM daily_close dc
WHERE dc.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND NOT EXISTS (
      SELECT 1 FROM sales s 
      WHERE s.store_id = dc.store_id 
        AND s.date = dc.date
        AND NOT EXISTS (
            SELECT 1 FROM daily_close dc2 
            WHERE dc2.store_id = s.store_id 
              AND dc2.date = s.date
        )
  )
ORDER BY dc.date DESC
LIMIT 5;
-- 기대 결과: official_count=1, best_count=1, best_is_official=true, best_source='daily_close'

-- 4-2. 시나리오 B: sales만 있는 날짜 확인
SELECT 
    s.date,
    'sales만 존재' AS scenario,
    (SELECT COUNT(*) FROM v_daily_sales_official WHERE store_id = s.store_id AND date = s.date) AS official_count,
    (SELECT COUNT(*) FROM v_daily_sales_best_available WHERE store_id = s.store_id AND date = s.date) AS best_count,
    (SELECT is_official FROM v_daily_sales_best_available WHERE store_id = s.store_id AND date = s.date LIMIT 1) AS best_is_official,
    (SELECT source FROM v_daily_sales_best_available WHERE store_id = s.store_id AND date = s.date LIMIT 1) AS best_source
FROM sales s
WHERE s.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND NOT EXISTS (
      SELECT 1 FROM daily_close dc 
      WHERE dc.store_id = s.store_id 
        AND dc.date = s.date
  )
ORDER BY s.date DESC
LIMIT 5;
-- 기대 결과: official_count=0, best_count=1, best_is_official=false, best_source='sales'

-- 4-3. 시나리오 C: 둘 다 있는 날짜 확인
SELECT 
    dc.date,
    'daily_close와 sales 둘 다 존재' AS scenario,
    (SELECT COUNT(*) FROM v_daily_sales_official WHERE store_id = dc.store_id AND date = dc.date) AS official_count,
    (SELECT COUNT(*) FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date) AS best_count,
    (SELECT is_official FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date LIMIT 1) AS best_is_official,
    (SELECT source FROM v_daily_sales_best_available WHERE store_id = dc.store_id AND date = dc.date LIMIT 1) AS best_source
FROM daily_close dc
WHERE dc.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND EXISTS (
      SELECT 1 FROM sales s 
      WHERE s.store_id = dc.store_id 
        AND s.date = dc.date
  )
ORDER BY dc.date DESC
LIMIT 5;
-- 기대 결과: official_count=1, best_count=1, best_is_official=true, best_source='daily_close' (daily_close 우선)

-- 4-4. 종합 시나리오 확인 (한 번에 보기)
WITH date_scenarios AS (
    SELECT DISTINCT
        COALESCE(dc.date, s.date) AS date,
        CASE 
            WHEN dc.date IS NOT NULL AND s.date IS NOT NULL THEN '둘 다 존재'
            WHEN dc.date IS NOT NULL THEN 'daily_close만'
            WHEN s.date IS NOT NULL THEN 'sales만'
        END AS scenario
    FROM (
        SELECT DISTINCT store_id, date FROM daily_close
        UNION
        SELECT DISTINCT store_id, date FROM sales
    ) AS all_dates
    LEFT JOIN daily_close dc ON all_dates.store_id = dc.store_id AND all_dates.date = dc.date
    LEFT JOIN sales s ON all_dates.store_id = s.store_id AND all_dates.date = s.date
    WHERE all_dates.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
      AND COALESCE(dc.date, s.date) >= CURRENT_DATE - INTERVAL '30 days'
)
SELECT 
    ds.date,
    ds.scenario,
    (SELECT COUNT(*) FROM v_daily_sales_official WHERE store_id = 'your-store-id-here'::UUID AND date = ds.date) AS official_count,
    (SELECT COUNT(*) FROM v_daily_sales_best_available WHERE store_id = 'your-store-id-here'::UUID AND date = ds.date) AS best_count,
    (SELECT is_official FROM v_daily_sales_best_available WHERE store_id = 'your-store-id-here'::UUID AND date = ds.date LIMIT 1) AS best_is_official,
    (SELECT source FROM v_daily_sales_best_available WHERE store_id = 'your-store-id-here'::UUID AND date = ds.date LIMIT 1) AS best_source
FROM date_scenarios ds
ORDER BY ds.date DESC
LIMIT 20;
-- 기대 결과: 각 날짜별 시나리오와 official/best count, is_official, source 확인

-- ============================================
-- 5) daily_sales_items DELETE 금지 확인
-- ============================================
-- ⚠️ 아래 쿼리에서 'your-store-id-here'를 실제 store_id로 변경하세요

-- 5-1. daily_sales_items에 qty=0인 행 확인 (soft_delete된 행)
SELECT 
    date,
    (SELECT name FROM menu_master WHERE id = dsi.menu_id) AS menu_name,
    qty,
    updated_at
FROM daily_sales_items dsi
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND qty = 0
ORDER BY date DESC, updated_at DESC
LIMIT 10;
-- 기대 결과: qty=0인 행이 있다면 soft_delete된 행 (실제 삭제되지 않음)

-- 5-2. audit에서 soft_delete 확인
SELECT 
    date,
    (SELECT name FROM menu_master WHERE id = a.menu_id) AS menu_name,
    action,
    old_qty,
    new_qty,
    source,
    changed_at
FROM daily_sales_items_audit a
WHERE store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND action = 'soft_delete'
ORDER BY changed_at DESC
LIMIT 10;
-- 기대 결과: soft_delete action이 있는 audit 기록 (실제 DELETE는 없고 qty=0으로 업데이트)

-- ============================================
-- 6) 점장 마감 저장 후 확인 (실제 테스트용)
-- ============================================
-- ⚠️ 점장 마감 저장 후 아래 쿼리로 확인하세요

-- 6-1. 특정 날짜의 daily_sales_items 확인
SELECT 
    dsi.date,
    mm.name AS menu_name,
    dsi.qty,
    dsi.updated_at
FROM daily_sales_items dsi
JOIN menu_master mm ON dsi.menu_id = mm.id
WHERE dsi.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND dsi.date = '2024-01-20'::DATE  -- ⚠️ 여기를 테스트한 날짜로 변경
ORDER BY mm.name;
-- 기대 결과: 해당 날짜의 모든 메뉴별 판매량 (DELETE 없이 UPSERT만 됨)

-- 6-2. 특정 날짜의 audit 기록 확인
SELECT 
    a.date,
    mm.name AS menu_name,
    a.action,
    a.old_qty,
    a.new_qty,
    a.source,
    a.reason,
    a.changed_at
FROM daily_sales_items_audit a
JOIN menu_master mm ON a.menu_id = mm.id
WHERE a.store_id = 'your-store-id-here'::UUID  -- ⚠️ 여기를 실제 store_id로 변경
  AND a.date = '2024-01-20'::DATE  -- ⚠️ 여기를 테스트한 날짜로 변경
ORDER BY a.changed_at DESC;
-- 기대 결과: 해당 날짜의 모든 변경 이력 (source='close', action은 'insert' 또는 'update')

-- ============================================
-- 사용 팁
-- ============================================
-- 1. 먼저 1) 객체 존재 확인부터 실행하여 모든 객체가 생성되었는지 확인
-- 2. 2) 공식/보조 뷰 샘플 조회로 VIEW가 정상 동작하는지 확인
-- 3. 4) SSOT 분리 확인으로 시나리오별 동작 확인
-- 4. 점장 마감 저장 후 6) 점장 마감 저장 후 확인으로 실제 동작 검증
