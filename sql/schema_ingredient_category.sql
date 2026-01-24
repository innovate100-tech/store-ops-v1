-- ============================================
-- 재료 분류 및 상태 컬럼 추가
-- ============================================
-- ingredients 테이블에 category, status, notes 컬럼 추가
-- 사용법: Supabase Dashboard → SQL Editor → 이 파일 전체 복사 → 붙여넣기 → Run
-- ============================================

-- 재료 분류 컬럼 추가
ALTER TABLE ingredients 
ADD COLUMN IF NOT EXISTS category TEXT;

-- 재료 상태 컬럼 추가
ALTER TABLE ingredients 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT '사용중' 
CHECK (status IN ('사용중', '사용중지'));

-- 재료 메모 컬럼 추가
ALTER TABLE ingredients 
ADD COLUMN IF NOT EXISTS notes TEXT;

-- 인덱스 추가 (선택사항, 성능 향상)
CREATE INDEX IF NOT EXISTS idx_ingredients_category ON ingredients(category);
CREATE INDEX IF NOT EXISTS idx_ingredients_status ON ingredients(status);

-- ============================================
-- 기존 데이터 확인 (실행 후 확인용)
-- ============================================
-- SELECT 
--     name,
--     category,
--     status,
--     notes
-- FROM ingredients
-- WHERE store_id = 'your-store-id'
-- ORDER BY name;
