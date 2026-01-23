-- ============================================
-- Phase 8-A Step 2-A: RLS 정책 적용 (1단계)
-- 대상: store_members, stores, user_profiles 3개 테이블만
-- ============================================
-- 
-- 적용 순서:
-- 1. 기존 정책 확인 및 정리
-- 2. 신규 정책 생성
-- 3. RLS ENABLE (FORCE는 보류)
-- 4. 검증 쿼리 실행 (별도 파일)
-- ============================================

-- ============================================
-- 1. store_members 테이블 RLS 정책
-- ============================================
-- 신규 테이블이므로 기존 정책 없음

-- RLS 활성화 (FORCE는 보류)
ALTER TABLE store_members ENABLE ROW LEVEL SECURITY;

-- 읽기 정책: 자신이 멤버인 매장 정보만 조회
CREATE POLICY "store_members_select_own_memberships"
    ON store_members FOR SELECT
    USING (user_id = auth.uid());

-- 쓰기 정책: 자신의 멤버십만 생성
CREATE POLICY "store_members_insert_own_membership"
    ON store_members FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- 수정 정책: 자신의 멤버십만 수정
CREATE POLICY "store_members_update_own_membership"
    ON store_members FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ============================================
-- 2. stores 테이블 RLS 정책
-- ============================================
-- 기존 정책 확인 및 업데이트

-- RLS 활성화 (이미 활성화되어 있을 수 있음)
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;

-- 기존 정책 확인 및 삭제 (레거시 get_user_store_id() 사용)
DROP POLICY IF EXISTS "Users can view their own store" ON stores;

-- 읽기 정책: 자신이 멤버인 매장만 조회 (store_members 기반)
CREATE POLICY "stores_select_own_stores"
    ON stores FOR SELECT
    USING (
        EXISTS (
            SELECT 1 
            FROM store_members 
            WHERE user_id = auth.uid() 
            AND store_id = stores.id
        )
    );

-- 쓰기 정책: 매장 생성 가능 (created_by 자동 설정)
CREATE POLICY "stores_insert_own_store"
    ON stores FOR INSERT
    WITH CHECK (created_by = auth.uid());

-- 수정 정책: owner만 매장 정보 수정 가능
CREATE POLICY "stores_update_own_store"
    ON stores FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 
            FROM store_members 
            WHERE user_id = auth.uid() 
            AND store_id = stores.id
            AND role = 'owner'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 
            FROM store_members 
            WHERE user_id = auth.uid() 
            AND store_id = stores.id
            AND role = 'owner'
        )
    );

-- ============================================
-- 3. user_profiles 테이블 RLS 정책
-- ============================================
-- 기존 정책 확인 및 추가

-- RLS 활성화 (이미 활성화되어 있을 수 있음)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 기존 SELECT 정책 확인 (이미 존재할 수 있음)
-- 기존 정책 이름: "Users can view their own profile"
-- 새 정책과 동일하므로 유지하거나 업데이트
-- 이름 충돌 방지를 위해 기존 정책은 유지하고, 필요시 나중에 정리

-- 읽기 정책: 본인 프로필만 조회 (기존 정책과 동일하므로 IF NOT EXISTS 사용 불가)
-- 기존 정책이 있으면 그대로 사용, 없으면 생성
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_profiles' 
        AND policyname = 'user_profiles_select_own_profile'
    ) THEN
        -- 기존 정책 이름이 다를 수 있으므로 확인 후 생성
        IF NOT EXISTS (
            SELECT 1 
            FROM pg_policies 
            WHERE schemaname = 'public' 
            AND tablename = 'user_profiles' 
            AND policyname = 'Users can view their own profile'
        ) THEN
            CREATE POLICY "user_profiles_select_own_profile"
                ON user_profiles FOR SELECT
                USING (id = auth.uid());
        END IF;
    END IF;
END $$;

-- 쓰기 정책: 본인 프로필 생성 가능 (회원가입 시)
-- IF NOT EXISTS는 CREATE POLICY에서 지원하지 않으므로 DO 블록으로 처리
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_profiles' 
        AND policyname = 'user_profiles_insert_own_profile'
    ) THEN
        CREATE POLICY "user_profiles_insert_own_profile"
            ON user_profiles FOR INSERT
            WITH CHECK (id = auth.uid());
    END IF;
END $$;

-- 수정 정책: 본인 프로필만 수정 가능
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_policies 
        WHERE schemaname = 'public' 
        AND tablename = 'user_profiles' 
        AND policyname = 'user_profiles_update_own_profile'
    ) THEN
        CREATE POLICY "user_profiles_update_own_profile"
            ON user_profiles FOR UPDATE
            USING (id = auth.uid())
            WITH CHECK (id = auth.uid());
    END IF;
END $$;

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Phase 8-A Step 2-A RLS 정책 적용 완료';
    RAISE NOTICE '========================================';
    RAISE NOTICE '적용된 테이블:';
    RAISE NOTICE '1. store_members (3개 정책)';
    RAISE NOTICE '2. stores (3개 정책)';
    RAISE NOTICE '3. user_profiles (3개 정책)';
    RAISE NOTICE '========================================';
    RAISE NOTICE '다음 단계:';
    RAISE NOTICE '1. phase8a_step2a_검증.sql 실행하여 검증';
    RAISE NOTICE '2. 기존 앱 동작 확인';
    RAISE NOTICE '3. 문제 없으면 Step 2-B 진행';
    RAISE NOTICE '========================================';
END $$;
