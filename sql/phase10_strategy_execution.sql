-- ============================================
-- PHASE 10 / STEP 10-7B: 전략 실행 미션 및 체크리스트
-- ============================================
-- 목적: "오늘의 전략 카드"를 실행 체크리스트로 쪼개고, 진행률을 저장하며, 7일 후 효과를 비교
-- ============================================

-- ============================================
-- STEP 1: strategy_missions 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS strategy_missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    mission_date DATE NOT NULL,  -- 미션 생성/배정된 날
    cause_type TEXT NOT NULL CHECK (cause_type IN (
        '유입 감소형', '객단가 하락형', '판매량 하락형', 
        '주력메뉴 붕괴형', '원가율 악화형', '구조 리스크형'
    )),
    title TEXT NOT NULL,
    reason_json JSONB NOT NULL,  -- 근거 숫자들 저장
    cta_page TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL,
    UNIQUE(store_id, mission_date)  -- 하루 1개만
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_strategy_missions_store_date 
    ON strategy_missions(store_id, mission_date DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_missions_status 
    ON strategy_missions(store_id, status) WHERE status = 'active';

-- ============================================
-- STEP 2: strategy_mission_tasks 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS strategy_mission_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES strategy_missions(id) ON DELETE CASCADE,
    task_order INT NOT NULL,
    task_title TEXT NOT NULL,
    is_done BOOLEAN NOT NULL DEFAULT FALSE,
    done_at TIMESTAMPTZ NULL,
    UNIQUE(mission_id, task_order)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_strategy_mission_tasks_mission 
    ON strategy_mission_tasks(mission_id, task_order);

-- ============================================
-- STEP 3: RLS 정책
-- ============================================
ALTER TABLE strategy_missions ENABLE ROW LEVEL SECURITY;
ALTER TABLE strategy_mission_tasks ENABLE ROW LEVEL SECURITY;

-- strategy_missions RLS
DROP POLICY IF EXISTS "Users can view strategy_missions from their store" ON strategy_missions;
CREATE POLICY "Users can view strategy_missions from their store"
    ON strategy_missions FOR SELECT
    USING (store_id = get_user_store_id());

DROP POLICY IF EXISTS "Users can insert strategy_missions to their store" ON strategy_missions;
CREATE POLICY "Users can insert strategy_missions to their store"
    ON strategy_missions FOR INSERT
    WITH CHECK (store_id = get_user_store_id());

DROP POLICY IF EXISTS "Users can update strategy_missions in their store" ON strategy_missions;
CREATE POLICY "Users can update strategy_missions in their store"
    ON strategy_missions FOR UPDATE
    USING (store_id = get_user_store_id())
    WITH CHECK (store_id = get_user_store_id());

DROP POLICY IF EXISTS "Users can delete strategy_missions from their store" ON strategy_missions;
CREATE POLICY "Users can delete strategy_missions from their store"
    ON strategy_missions FOR DELETE
    USING (store_id = get_user_store_id());

-- strategy_mission_tasks RLS (mission_id를 통해 간접 접근)
DROP POLICY IF EXISTS "Users can view strategy_mission_tasks from their store" ON strategy_mission_tasks;
CREATE POLICY "Users can view strategy_mission_tasks from their store"
    ON strategy_mission_tasks FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM strategy_missions sm
            WHERE sm.id = strategy_mission_tasks.mission_id
            AND sm.store_id = get_user_store_id()
        )
    );

DROP POLICY IF EXISTS "Users can insert strategy_mission_tasks to their store" ON strategy_mission_tasks;
CREATE POLICY "Users can insert strategy_mission_tasks to their store"
    ON strategy_mission_tasks FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM strategy_missions sm
            WHERE sm.id = strategy_mission_tasks.mission_id
            AND sm.store_id = get_user_store_id()
        )
    );

DROP POLICY IF EXISTS "Users can update strategy_mission_tasks in their store" ON strategy_mission_tasks;
CREATE POLICY "Users can update strategy_mission_tasks in their store"
    ON strategy_mission_tasks FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM strategy_missions sm
            WHERE sm.id = strategy_mission_tasks.mission_id
            AND sm.store_id = get_user_store_id()
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM strategy_missions sm
            WHERE sm.id = strategy_mission_tasks.mission_id
            AND sm.store_id = get_user_store_id()
        )
    );

DROP POLICY IF EXISTS "Users can delete strategy_mission_tasks from their store" ON strategy_mission_tasks;
CREATE POLICY "Users can delete strategy_mission_tasks from their store"
    ON strategy_mission_tasks FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM strategy_missions sm
            WHERE sm.id = strategy_mission_tasks.mission_id
            AND sm.store_id = get_user_store_id()
        )
    );

-- ============================================
-- STEP 4: 트리거 (updated_at 자동 갱신)
-- ============================================
-- strategy_missions는 completed_at만 수동 업데이트

-- strategy_mission_tasks의 is_done 변경 시 done_at 자동 설정
CREATE OR REPLACE FUNCTION update_task_done_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_done = TRUE AND OLD.is_done = FALSE THEN
        NEW.done_at = NOW();
    ELSIF NEW.is_done = FALSE THEN
        NEW.done_at = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_task_done_at ON strategy_mission_tasks;
CREATE TRIGGER trigger_update_task_done_at
    BEFORE UPDATE ON strategy_mission_tasks
    FOR EACH ROW
    WHEN (OLD.is_done IS DISTINCT FROM NEW.is_done)
    EXECUTE FUNCTION update_task_done_at();
