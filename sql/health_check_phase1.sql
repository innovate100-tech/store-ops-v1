-- ============================================
-- Health Check System - Phase 1 Tables
-- 건강검진 시스템 테이블 생성 (QSCPPPMHF)
-- ============================================

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. health_check_sessions (건강검진 세션)
-- ============================================
CREATE TABLE IF NOT EXISTS health_check_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    check_type TEXT DEFAULT 'ad-hoc',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL,
    overall_score NUMERIC NULL,
    overall_grade TEXT NULL,
    main_bottleneck TEXT NULL,  -- 'Q','S','C','P1','P2','P3','M','H','F'
    coach_summary TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_check_type CHECK (check_type IN ('ad-hoc', 'regular', 'periodic')),
    CONSTRAINT valid_grade CHECK (overall_grade IS NULL OR overall_grade IN ('A', 'B', 'C', 'D', 'E')),
    CONSTRAINT valid_bottleneck CHECK (main_bottleneck IS NULL OR main_bottleneck IN ('Q', 'S', 'C', 'P1', 'P2', 'P3', 'M', 'H', 'F'))
);

-- ============================================
-- 2. health_check_answers (건강검진 답변)
-- ============================================
CREATE TABLE IF NOT EXISTS health_check_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES health_check_sessions(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    category TEXT NOT NULL,  -- 'Q','S','C','P1','P2','P3','M','H','F'
    question_code TEXT NOT NULL,  -- 'Q1'..'F10'
    raw_value TEXT NOT NULL,  -- 'yes'|'maybe'|'no'
    score INT NOT NULL,  -- 3|1|0
    memo TEXT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_category CHECK (category IN ('Q', 'S', 'C', 'P1', 'P2', 'P3', 'M', 'H', 'F')),
    CONSTRAINT valid_raw_value CHECK (raw_value IN ('yes', 'maybe', 'no')),
    CONSTRAINT valid_score CHECK (score IN (0, 1, 3)),
    UNIQUE(store_id, session_id, category, question_code)
);

-- ============================================
-- 3. health_check_results (건강검진 결과 집계)
-- ============================================
CREATE TABLE IF NOT EXISTS health_check_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES health_check_sessions(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    category TEXT NOT NULL,  -- 'Q','S','C','P1','P2','P3','M','H','F'
    score_avg NUMERIC NOT NULL,  -- 0~100
    risk_level TEXT NOT NULL,  -- 'green'|'yellow'|'red'
    strength_flags JSONB DEFAULT '[]',
    risk_flags JSONB DEFAULT '[]',
    structure_summary TEXT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_category_result CHECK (category IN ('Q', 'S', 'C', 'P1', 'P2', 'P3', 'M', 'H', 'F')),
    CONSTRAINT valid_risk_level CHECK (risk_level IN ('green', 'yellow', 'red')),
    CONSTRAINT valid_score_range CHECK (score_avg >= 0 AND score_avg <= 100),
    UNIQUE(store_id, session_id, category)
);

-- ============================================
-- Indexes for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_health_check_sessions_store_id ON health_check_sessions(store_id);
CREATE INDEX IF NOT EXISTS idx_health_check_sessions_completed_at ON health_check_sessions(completed_at);
CREATE INDEX IF NOT EXISTS idx_health_check_answers_session_id ON health_check_answers(session_id);
CREATE INDEX IF NOT EXISTS idx_health_check_answers_store_id ON health_check_answers(store_id);
CREATE INDEX IF NOT EXISTS idx_health_check_results_session_id ON health_check_results(session_id);
CREATE INDEX IF NOT EXISTS idx_health_check_results_store_id ON health_check_results(store_id);

-- ============================================
-- RLS Policies (Row Level Security)
-- ============================================

-- Enable RLS
ALTER TABLE health_check_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_check_answers ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_check_results ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access their own store's health check data
-- (Using auth.uid() to get user_id, then checking store_members)

-- health_check_sessions policies
CREATE POLICY "Users can view their store's health check sessions"
    ON health_check_sessions FOR SELECT
    USING (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their store's health check sessions"
    ON health_check_sessions FOR INSERT
    WITH CHECK (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their store's health check sessions"
    ON health_check_sessions FOR UPDATE
    USING (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );

-- health_check_answers policies
CREATE POLICY "Users can view their store's health check answers"
    ON health_check_answers FOR SELECT
    USING (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their store's health check answers"
    ON health_check_answers FOR INSERT
    WITH CHECK (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their store's health check answers"
    ON health_check_answers FOR UPDATE
    USING (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );

-- health_check_results policies
CREATE POLICY "Users can view their store's health check results"
    ON health_check_results FOR SELECT
    USING (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert their store's health check results"
    ON health_check_results FOR INSERT
    WITH CHECK (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update their store's health check results"
    ON health_check_results FOR UPDATE
    USING (
        store_id IN (
            SELECT store_id FROM store_members
            WHERE user_id = auth.uid()
        )
    );
