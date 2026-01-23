-- ============================================
-- Phase 8-A Step 1: SaaS 기본 구조 - 테이블 생성/변경
-- 실행 전 반드시 영향 범위 확인 후 진행
-- ============================================

-- ============================================
-- 1. stores 테이블 업데이트 (created_by 추가)
-- ============================================
-- 기존 stores 테이블에 created_by 컬럼 추가 (NULL 허용)
-- 기존 데이터는 created_by가 NULL로 유지됨 (안전)

DO $$
BEGIN
    -- created_by 컬럼이 없을 때만 추가
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'stores' 
        AND column_name = 'created_by'
    ) THEN
        ALTER TABLE stores 
        ADD COLUMN created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL;
        
        -- 인덱스 추가 (성능 향상)
        CREATE INDEX IF NOT EXISTS idx_stores_created_by ON stores(created_by);
        
        RAISE NOTICE 'stores 테이블에 created_by 컬럼 추가 완료';
    ELSE
        RAISE NOTICE 'stores 테이블에 created_by 컬럼이 이미 존재합니다.';
    END IF;
END $$;

-- ============================================
-- 2. store_members 테이블 생성 (신규)
-- ============================================
-- 사용자-매장 멤버십 테이블 (다중 매장 지원)
-- 한 사용자가 여러 매장에 소속될 수 있음

CREATE TABLE IF NOT EXISTS store_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'manager', 'staff')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, user_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_store_members_store_id ON store_members(store_id);
CREATE INDEX IF NOT EXISTS idx_store_members_user_id ON store_members(user_id);
CREATE INDEX IF NOT EXISTS idx_store_members_role ON store_members(role);

-- ============================================
-- 3. user_profiles 테이블 업데이트
-- ============================================
-- 기존 store_id 컬럼은 유지 (호환성)
-- default_store_id 추가 (선호 매장)
-- onboarding_mode 추가 (온보딩 모드)

DO $$
BEGIN
    -- default_store_id 컬럼 추가 (없을 때만)
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'default_store_id'
    ) THEN
        ALTER TABLE user_profiles 
        ADD COLUMN default_store_id UUID REFERENCES stores(id) ON DELETE SET NULL;
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS idx_user_profiles_default_store_id 
        ON user_profiles(default_store_id);
        
        RAISE NOTICE 'user_profiles 테이블에 default_store_id 컬럼 추가 완료';
    ELSE
        RAISE NOTICE 'user_profiles 테이블에 default_store_id 컬럼이 이미 존재합니다.';
    END IF;
    
    -- onboarding_mode 컬럼 추가 (없을 때만)
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'onboarding_mode'
    ) THEN
        ALTER TABLE user_profiles 
        ADD COLUMN onboarding_mode TEXT NOT NULL DEFAULT 'coach' 
        CHECK (onboarding_mode IN ('coach', 'fast'));
        
        RAISE NOTICE 'user_profiles 테이블에 onboarding_mode 컬럼 추가 완료';
    ELSE
        RAISE NOTICE 'user_profiles 테이블에 onboarding_mode 컬럼이 이미 존재합니다.';
    END IF;
END $$;

-- ============================================
-- 4. Helper Function: 사용자의 매장 목록 조회
-- ============================================
-- store_members를 통해 사용자가 소속된 매장 목록 반환

CREATE OR REPLACE FUNCTION get_user_store_ids()
RETURNS TABLE(store_id UUID) AS $$
BEGIN
    RETURN QUERY
    SELECT sm.store_id
    FROM store_members sm
    WHERE sm.user_id = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 5. Helper Function: 사용자의 기본 매장 ID 조회 (업데이트)
-- ============================================
-- 기존 get_user_store_id() 함수는 user_profiles.store_id를 사용
-- 새로운 함수는 store_members를 우선 확인하고, 없으면 default_store_id 사용

CREATE OR REPLACE FUNCTION get_user_store_id()
RETURNS UUID AS $$
DECLARE
    result_store_id UUID;
BEGIN
    -- 1순위: store_members에서 첫 번째 매장 (owner 우선, 없으면 첫 번째)
    SELECT sm.store_id INTO result_store_id
    FROM store_members sm
    WHERE sm.user_id = auth.uid()
    ORDER BY 
        CASE sm.role 
            WHEN 'owner' THEN 1 
            WHEN 'manager' THEN 2 
            ELSE 3 
        END,
        sm.created_at ASC
    LIMIT 1;
    
    -- 2순위: user_profiles.default_store_id
    IF result_store_id IS NULL THEN
        SELECT default_store_id INTO result_store_id
        FROM user_profiles
        WHERE id = auth.uid();
    END IF;
    
    -- 3순위: user_profiles.store_id (레거시 호환)
    IF result_store_id IS NULL THEN
        SELECT store_id INTO result_store_id
        FROM user_profiles
        WHERE id = auth.uid();
    END IF;
    
    RETURN result_store_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 6. Helper Function: 사용자가 매장 멤버인지 확인
-- ============================================
-- 특정 매장에 대한 사용자의 멤버십 확인

CREATE OR REPLACE FUNCTION is_user_store_member(check_store_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM store_members
        WHERE user_id = auth.uid()
        AND store_id = check_store_id
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 7. 데이터 마이그레이션: 기존 user_profiles.store_id → store_members
-- ============================================
-- 기존 user_profiles에 store_id가 있는 경우, store_members에 자동 등록
-- 이 마이그레이션은 안전하게 실행 가능 (기존 데이터 보존)

DO $$
DECLARE
    migrated_count INTEGER := 0;
BEGIN
    -- user_profiles에 store_id가 있지만 store_members에 없는 경우만 마이그레이션
    INSERT INTO store_members (store_id, user_id, role, created_at)
    SELECT 
        up.store_id,
        up.id AS user_id,
        COALESCE(up.role, 'manager') AS role,  -- 기존 role 사용, 없으면 'manager'
        up.created_at
    FROM user_profiles up
    WHERE up.store_id IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 
        FROM store_members sm 
        WHERE sm.user_id = up.id 
        AND sm.store_id = up.store_id
    )
    ON CONFLICT (store_id, user_id) DO NOTHING;
    
    GET DIAGNOSTICS migrated_count = ROW_COUNT;
    
    RAISE NOTICE '기존 user_profiles.store_id → store_members 마이그레이션 완료: %건', migrated_count;
END $$;

-- ============================================
-- 8. 데이터 마이그레이션: default_store_id 설정
-- ============================================
-- user_profiles에 store_id가 있지만 default_store_id가 NULL인 경우 설정

DO $$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    UPDATE user_profiles up
    SET default_store_id = up.store_id
    WHERE up.store_id IS NOT NULL
    AND up.default_store_id IS NULL;
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    
    RAISE NOTICE 'default_store_id 자동 설정 완료: %건', updated_count;
END $$;

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Phase 8-A Step 1 SQL 실행 완료';
    RAISE NOTICE '========================================';
    RAISE NOTICE '생성/변경된 항목:';
    RAISE NOTICE '1. stores.created_by 컬럼 추가';
    RAISE NOTICE '2. store_members 테이블 생성';
    RAISE NOTICE '3. user_profiles.default_store_id 컬럼 추가';
    RAISE NOTICE '4. user_profiles.onboarding_mode 컬럼 추가';
    RAISE NOTICE '5. Helper 함수들 생성/업데이트';
    RAISE NOTICE '6. 기존 데이터 마이그레이션 완료';
    RAISE NOTICE '========================================';
END $$;
