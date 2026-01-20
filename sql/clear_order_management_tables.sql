-- ============================================
-- 발주 관리 챕터 관련 테이블 데이터 삭제
-- ============================================
-- 이 스크립트는 발주 추천, 진행 현황, 공급업체, 발주 분석 챕터가 비워짐에 따라
-- 관련 테이블의 데이터를 모두 삭제합니다.
--
-- 주의: 이 작업은 되돌릴 수 없습니다. 실행 전에 백업을 권장합니다.
-- ============================================

-- 1. Orders 테이블 데이터 삭제 (발주 이력)
--    외래키 제약조건 때문에 먼저 삭제해야 합니다.
DELETE FROM orders
WHERE store_id = get_user_store_id();

-- 2. Ingredient Suppliers 테이블 데이터 삭제 (재료-공급업체 매핑)
DELETE FROM ingredient_suppliers
WHERE store_id = get_user_store_id();

-- 3. Suppliers 테이블 데이터 삭제 (공급업체)
DELETE FROM suppliers
WHERE store_id = get_user_store_id();

-- ============================================
-- 삭제 확인 쿼리 (선택사항)
-- ============================================
-- 실행 후 다음 쿼리로 데이터가 비워졌는지 확인할 수 있습니다:
--
-- SELECT COUNT(*) FROM orders WHERE store_id = get_user_store_id();
-- SELECT COUNT(*) FROM ingredient_suppliers WHERE store_id = get_user_store_id();
-- SELECT COUNT(*) FROM suppliers WHERE store_id = get_user_store_id();
--
-- 모든 결과가 0이면 정상적으로 삭제된 것입니다.
