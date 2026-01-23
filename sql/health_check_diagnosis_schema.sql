-- ============================================
-- Health Check Diagnosis Schema Extension
-- 판독 결과 저장을 위한 컬럼 추가
-- ============================================

-- health_check_sessions 테이블에 판독 결과 JSON 컬럼 추가
ALTER TABLE health_check_sessions
    ADD COLUMN IF NOT EXISTS diagnosis_json JSONB DEFAULT NULL;

-- 인덱스 추가 (판독 결과 조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_health_check_sessions_diagnosis_json 
    ON health_check_sessions USING GIN (diagnosis_json);

-- 주석 추가
COMMENT ON COLUMN health_check_sessions.diagnosis_json IS 
    '건강검진 판독 결과 JSON (risk_axes, primary_pattern, insight_summary, strategy_bias)';
