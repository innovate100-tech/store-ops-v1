-- ============================================
-- Health Check: check_type 제약조건 업데이트
-- 'monthly' 값 추가
-- ============================================

-- 기존 제약조건 삭제 후 재생성
ALTER TABLE health_check_sessions 
    DROP CONSTRAINT IF EXISTS valid_check_type;

ALTER TABLE health_check_sessions 
    ADD CONSTRAINT valid_check_type 
    CHECK (check_type IN ('ad-hoc', 'regular', 'periodic', 'monthly'));
