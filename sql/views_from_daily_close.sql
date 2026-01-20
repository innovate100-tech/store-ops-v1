-- ============================================
-- Daily Close 기반 뷰 생성
-- daily_close 테이블이 단일 소스이므로, 
-- 기존 테이블들(sales, naver_visitors, daily_sales_items)을
-- daily_close에서 추출하는 뷰로 대체
-- ============================================

-- ============================================
-- 1. Sales View (매출 데이터 뷰)
-- ============================================
CREATE OR REPLACE VIEW sales_from_daily_close AS
SELECT 
    store_id,
    date,
    card_sales,
    cash_sales,
    total_sales,
    created_at,
    updated_at
FROM daily_close
WHERE total_sales > 0;

-- ============================================
-- 2. Naver Visitors View (방문자 데이터 뷰)
-- ============================================
CREATE OR REPLACE VIEW naver_visitors_from_daily_close AS
SELECT 
    store_id,
    date,
    visitors AS visitors,
    created_at,
    updated_at
FROM daily_close
WHERE visitors > 0;

-- ============================================
-- 3. Daily Sales Items View (일일 판매 내역 뷰)
-- ============================================
-- 주의: sales_items가 JSONB이므로 파싱이 필요합니다.
-- 이 뷰는 PostgreSQL의 JSONB 함수를 사용합니다.
CREATE OR REPLACE VIEW daily_sales_items_from_daily_close AS
SELECT 
    dc.store_id,
    dc.date,
    mm.id AS menu_id,
    mm.name AS menu_name,
    (item->>'quantity')::INTEGER AS qty,
    dc.created_at,
    dc.updated_at
FROM daily_close dc
CROSS JOIN LATERAL jsonb_array_elements(dc.sales_items) AS item
LEFT JOIN menu_master mm ON mm.store_id = dc.store_id 
    AND mm.name = item->>'menu_name'
WHERE dc.sales_items IS NOT NULL 
    AND jsonb_array_length(dc.sales_items) > 0;

-- ============================================
-- RLS 정책 적용 (뷰는 기본 테이블의 RLS를 상속)
-- ============================================
-- 뷰는 기본 테이블(daily_close)의 RLS 정책을 자동으로 상속받습니다.
-- 별도의 RLS 정책 설정이 필요 없습니다.

-- ============================================
-- 사용 방법
-- ============================================
-- 기존 코드에서:
--   SELECT * FROM sales WHERE ...
-- 대신:
--   SELECT * FROM sales_from_daily_close WHERE ...
--
-- 하지만 호환성을 위해 기존 테이블도 유지합니다.
-- 점진적으로 뷰로 마이그레이션하는 것을 권장합니다.
