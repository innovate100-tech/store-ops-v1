-- ============================================
-- 사용하지 않는 뷰 삭제
-- ============================================
-- 이 스크립트는 실제로 사용되지 않는 뷰들을 삭제합니다.
--
-- 분석 결과:
-- 1. sales_from_daily_close - 코드에서 사용되지 않음 (sales 테이블 직접 사용)
-- 2. naver_visitors_from_daily_close - 코드에서 사용되지 않음 (naver_visitors 테이블 직접 사용)
-- 3. daily_sales_items_from_daily_close - 코드에서 사용되지 않음 (daily_sales_items 테이블 직접 사용)
--
-- 이 뷰들은 daily_close를 단일 소스로 사용하려는 계획으로 만들어졌지만,
-- 실제 코드에서는 여전히 기존 테이블들을 직접 사용하고 있습니다.
-- ============================================

-- 사용하지 않는 뷰 삭제
DROP VIEW IF EXISTS sales_from_daily_close CASCADE;
DROP VIEW IF EXISTS naver_visitors_from_daily_close CASCADE;
DROP VIEW IF EXISTS daily_sales_items_from_daily_close CASCADE;

-- ============================================
-- 삭제 확인 쿼리 (선택사항)
-- ============================================
-- 실행 후 다음 쿼리로 뷰가 제거되었는지 확인할 수 있습니다:
--
-- SELECT table_name 
-- FROM information_schema.views 
-- WHERE table_schema = 'public' 
--   AND table_name IN ('sales_from_daily_close', 'naver_visitors_from_daily_close', 'daily_sales_items_from_daily_close');
--
-- 결과가 없으면 정상적으로 삭제된 것입니다.
