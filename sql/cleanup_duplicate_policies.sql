-- ============================================
-- 중복 RLS 정책 정리 스크립트
-- 기존 정책을 모두 삭제하고 새로 생성
-- ============================================

-- 주의: 이 스크립트는 모든 기존 정책을 삭제합니다.
-- 실행 전에 백업을 권장합니다.

-- ============================================
-- 1단계: 모든 기존 정책 삭제
-- ============================================

-- sales 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view sales from their store" ON sales;
DROP POLICY IF EXISTS "Users can insert sales to their store" ON sales;
DROP POLICY IF EXISTS "Users can update sales in their store" ON sales;
DROP POLICY IF EXISTS "Users can delete sales from their store" ON sales;

-- naver_visitors 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view naver_visitors from their store" ON naver_visitors;
DROP POLICY IF EXISTS "Users can insert naver_visitors to their store" ON naver_visitors;
DROP POLICY IF EXISTS "Users can update naver_visitors in their store" ON naver_visitors;
DROP POLICY IF EXISTS "Users can delete naver_visitors from their store" ON naver_visitors;

-- menu_master 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view menu_master from their store" ON menu_master;
DROP POLICY IF EXISTS "Users can insert menu_master to their store" ON menu_master;
DROP POLICY IF EXISTS "Users can update menu_master in their store" ON menu_master;
DROP POLICY IF EXISTS "Users can delete menu_master from their store" ON menu_master;

-- ingredients 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view ingredients from their store" ON ingredients;
DROP POLICY IF EXISTS "Users can insert ingredients to their store" ON ingredients;
DROP POLICY IF EXISTS "Users can update ingredients in their store" ON ingredients;
DROP POLICY IF EXISTS "Users can delete ingredients from their store" ON ingredients;

-- recipes 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view recipes from their store" ON recipes;
DROP POLICY IF EXISTS "Users can insert recipes to their store" ON recipes;
DROP POLICY IF EXISTS "Users can update recipes in their store" ON recipes;
DROP POLICY IF EXISTS "Users can delete recipes from their store" ON recipes;

-- daily_sales_items 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view daily_sales_items from their store" ON daily_sales_items;
DROP POLICY IF EXISTS "Users can insert daily_sales_items to their store" ON daily_sales_items;
DROP POLICY IF EXISTS "Users can update daily_sales_items in their store" ON daily_sales_items;
DROP POLICY IF EXISTS "Users can delete daily_sales_items from their store" ON daily_sales_items;

-- inventory 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view inventory from their store" ON inventory;
DROP POLICY IF EXISTS "Users can insert inventory to their store" ON inventory;
DROP POLICY IF EXISTS "Users can update inventory in their store" ON inventory;
DROP POLICY IF EXISTS "Users can delete inventory from their store" ON inventory;

-- daily_close 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view daily_close from their store" ON daily_close;
DROP POLICY IF EXISTS "Users can insert daily_close to their store" ON daily_close;
DROP POLICY IF EXISTS "Users can update daily_close in their store" ON daily_close;
DROP POLICY IF EXISTS "Users can delete daily_close from their store" ON daily_close;

-- targets 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view targets from their store" ON targets;
DROP POLICY IF EXISTS "Users can insert targets to their store" ON targets;
DROP POLICY IF EXISTS "Users can update targets in their store" ON targets;
DROP POLICY IF EXISTS "Users can delete targets from their store" ON targets;

-- abc_history 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view abc_history from their store" ON abc_history;
DROP POLICY IF EXISTS "Users can insert abc_history to their store" ON abc_history;
DROP POLICY IF EXISTS "Users can update abc_history in their store" ON abc_history;
DROP POLICY IF EXISTS "Users can delete abc_history from their store" ON abc_history;

-- expense_structure 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view expense_structure from their store" ON expense_structure;
DROP POLICY IF EXISTS "Users can insert expense_structure to their store" ON expense_structure;
DROP POLICY IF EXISTS "Users can update expense_structure in their store" ON expense_structure;
DROP POLICY IF EXISTS "Users can delete expense_structure from their store" ON expense_structure;

-- suppliers 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view suppliers from their store" ON suppliers;
DROP POLICY IF EXISTS "Users can insert suppliers to their store" ON suppliers;
DROP POLICY IF EXISTS "Users can update suppliers in their store" ON suppliers;
DROP POLICY IF EXISTS "Users can delete suppliers from their store" ON suppliers;

-- ingredient_suppliers 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view ingredient_suppliers from their store" ON ingredient_suppliers;
DROP POLICY IF EXISTS "Users can insert ingredient_suppliers to their store" ON ingredient_suppliers;
DROP POLICY IF EXISTS "Users can update ingredient_suppliers in their store" ON ingredient_suppliers;
DROP POLICY IF EXISTS "Users can delete ingredient_suppliers from their store" ON ingredient_suppliers;

-- orders 테이블 정책 삭제
DROP POLICY IF EXISTS "Users can view orders from their store" ON orders;
DROP POLICY IF EXISTS "Users can insert orders to their store" ON orders;
DROP POLICY IF EXISTS "Users can update orders in their store" ON orders;
DROP POLICY IF EXISTS "Users can delete orders from their store" ON orders;

-- ============================================
-- 2단계: 정책 재생성 (함수 사용)
-- ============================================
-- 위 정책 삭제 후, 아래 명령어 실행:
-- SELECT create_all_rls_policies();
