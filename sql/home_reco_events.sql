-- ============================================
-- 홈 추천 이벤트 로그 테이블
-- ============================================
-- 추천 표시(shown) 및 클릭(clicked) 이벤트 저장
-- ============================================

CREATE TABLE IF NOT EXISTS home_reco_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    event_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_day DATE NOT NULL GENERATED ALWAYS AS (event_at::date) STORED,  -- 중복 방지용
    event_type TEXT NOT NULL CHECK (event_type IN ('shown', 'clicked')),
    reco_type TEXT NOT NULL,  -- 'TYPE_0', 'TYPE_1-A', 'TYPE_1-B', 'TYPE_2', 'TYPE_3', 'TYPE_4'
    action_page TEXT,  -- 예: '일일 입력(통합)', '레시피 등록', '목표 매출구조'
    message TEXT,  -- 추천 문장(짧게)
    snapshot JSONB,  -- 그 순간 상태 (yesterday_closed, last7_close_days, recipe_cover_rate, goals...)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_home_reco_events_store_event_at 
    ON home_reco_events(store_id, event_at DESC);

CREATE INDEX IF NOT EXISTS idx_home_reco_events_user_event_at 
    ON home_reco_events(user_id, event_at DESC);

-- 중복 방지: 같은 store_id + 같은 날짜 + 같은 reco_type + event_type='shown'에 대해 하루 1회만
CREATE UNIQUE INDEX IF NOT EXISTS idx_home_reco_events_unique_shown 
    ON home_reco_events(store_id, event_day, reco_type) 
    WHERE event_type = 'shown';

-- RLS 활성화
ALTER TABLE home_reco_events ENABLE ROW LEVEL SECURITY;

-- RLS 정책: 자신의 store_id에 대한 로그만 insert/select 가능
CREATE POLICY "Users can insert their own store reco events"
    ON home_reco_events FOR INSERT
    WITH CHECK (
        store_id IN (
            SELECT store_id FROM user_profiles 
            WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can view their own store reco events"
    ON home_reco_events FOR SELECT
    USING (
        store_id IN (
            SELECT store_id FROM user_profiles 
            WHERE id = auth.uid()
        )
    );
