-- ============================================
-- 판매량 우선순위 뷰: v_daily_sales_items_effective
-- ============================================
-- daily_sales_items (base)와 overrides를 조인하여
-- overrides가 있으면 overrides.qty를 우선 사용, 없으면 base.qty 사용
-- ============================================

CREATE OR REPLACE VIEW v_daily_sales_items_effective AS
SELECT 
    COALESCE(ovr.store_id, base.store_id) AS store_id,
    COALESCE(ovr.sale_date, base.date) AS date,
    COALESCE(ovr.menu_id, base.menu_id) AS menu_id,
    -- 우선순위: overrides가 있으면 overrides.qty, 없으면 base.qty
    COALESCE(ovr.qty, base.qty, 0) AS qty,
    -- 메타 정보 (선택적, 호환성 유지)
    CASE 
        WHEN ovr.menu_id IS NOT NULL THEN 'override'
        WHEN base.menu_id IS NOT NULL THEN 'base'
        ELSE 'none'
    END AS source_type,
    ovr.updated_at AS override_updated_at,
    base.created_at AS base_created_at,
    base.updated_at AS base_updated_at
FROM daily_sales_items base
FULL OUTER JOIN daily_sales_items_overrides ovr
    ON base.store_id = ovr.store_id
    AND base.date = ovr.sale_date
    AND base.menu_id = ovr.menu_id
WHERE COALESCE(ovr.qty, base.qty, 0) > 0;  -- 0인 항목은 제외

-- ============================================
-- RLS 정책 (뷰는 기본 테이블의 RLS를 상속)
-- ============================================
-- 뷰는 기본 테이블(daily_sales_items, daily_sales_items_overrides)의 
-- RLS 정책을 자동으로 상속받습니다.

-- ============================================
-- 사용 예시
-- ============================================
-- SELECT * FROM v_daily_sales_items_effective 
-- WHERE store_id = 'xxx' AND date = '2024-01-20';
--
-- 결과:
-- - overrides가 있으면: overrides.qty 사용 (source_type = 'override')
-- - overrides가 없으면: base.qty 사용 (source_type = 'base')
