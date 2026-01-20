-- ============================================
-- 발주 단위 변환 기능 추가
-- 재료 마스터에 발주 단위와 변환 비율 필드 추가
-- ============================================

-- 발주 단위 필드 추가 (발주 시 사용할 단위, 예: "개", "박스")
ALTER TABLE ingredients 
ADD COLUMN IF NOT EXISTS order_unit TEXT;

-- 단위 변환 비율 필드 추가 (1 발주단위 = 몇 기본단위인지, 예: 1개 = 500g이면 500)
ALTER TABLE ingredients 
ADD COLUMN IF NOT EXISTS conversion_rate NUMERIC(10, 2) DEFAULT 1.0;

-- ============================================
-- 발주 이력 테이블 안정성 보강용 컬럼
-- - inventory_applied: 입고 완료 시 재고 반영이 이미 수행되었는지 여부
--   (상태를 여러 번 바꾸더라도 재고가 중복 반영되지 않도록 하기 위함)
-- ============================================

ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS inventory_applied BOOLEAN DEFAULT FALSE;

-- 기존 데이터에 대한 기본값 설정 (변환 비율이 없으면 1로 설정)
UPDATE ingredients 
SET conversion_rate = 1.0 
WHERE conversion_rate IS NULL;

-- 발주 단위가 없으면 기본 단위와 동일하게 설정
UPDATE ingredients 
SET order_unit = unit 
WHERE order_unit IS NULL;
