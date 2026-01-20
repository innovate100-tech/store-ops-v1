-- ============================================
-- 발주 관리 챕터 관련 테이블 완전 삭제 (구조까지 제거)
-- ============================================
-- 이 스크립트는 발주 추천, 진행 현황, 공급업체, 발주 분석 챕터가 비워짐에 따라
-- 관련 테이블을 완전히 삭제합니다 (데이터 + 테이블 구조 모두).
--
-- ⚠️ 매우 주의: 이 작업은 되돌릴 수 없습니다!
-- 테이블 구조까지 완전히 제거되므로, 나중에 재기획할 때
-- sql/schema_phase1_suppliers.sql 파일을 다시 실행해야 테이블을 복구할 수 있습니다.
-- ============================================

-- 외래키 제약조건 때문에 삭제 순서가 중요합니다.
-- 1. Orders 테이블 삭제 (가장 많은 외래키 참조)
DROP TABLE IF EXISTS orders CASCADE;

-- 2. Ingredient Suppliers 테이블 삭제 (suppliers와 ingredients를 참조)
DROP TABLE IF EXISTS ingredient_suppliers CASCADE;

-- 3. Suppliers 테이블 삭제 (가장 기본 테이블)
DROP TABLE IF EXISTS suppliers CASCADE;

-- ============================================
-- 삭제 확인 쿼리 (선택사항)
-- ============================================
-- 실행 후 다음 쿼리로 테이블이 완전히 제거되었는지 확인할 수 있습니다:
--
-- SELECT table_name 
-- FROM information_schema.tables 
-- WHERE table_schema = 'public' 
--   AND table_name IN ('orders', 'ingredient_suppliers', 'suppliers');
--
-- 결과가 없으면 정상적으로 삭제된 것입니다.
