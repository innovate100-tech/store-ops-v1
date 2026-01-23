# Phase 8-A Step 2: RLS 정책 적용 계획

## 📋 작업 원칙

### 원칙 1: 읽기(SELECT) 정책부터 최소로 적용
- ❌ 한 번에 모든 테이블 RLS 완성 금지
- ✅ **1단계**: `store_members`, `stores`, `user_profiles` 3개 테이블만
- ✅ **2단계**: `daily_close` 같은 핵심 테이블 1~2개만 추가
- ✅ 단계별로 테스트 후 다음 단계 진행

### 원칙 2: SECURITY DEFINER 함수의 RLS 우회 방지
- ✅ 함수가 반환하는 데이터 범위를 `auth.uid()`로 강하게 제한
- ✅ Helper 함수는 "ID 목록 반환" 수준으로 최소화
- ✅ 함수 내부 쿼리에서 `WHERE user_id = auth.uid()` 필터 필수

#### RLS 우회가 불가능한 이유:
1. **PostgreSQL RLS 동작 방식:**
   - `SECURITY DEFINER` 함수는 함수 소유자 권한으로 실행되지만
   - 함수 내부에서 테이블을 조회할 때는 **여전히 RLS 정책이 적용됨**
   - RLS는 테이블 레벨에서 동작하므로 함수 내부 쿼리에도 적용됨

2. **현재 Helper 함수의 안전성:**
   - `get_user_store_id()`: `WHERE sm.user_id = auth.uid()` 필터 사용
   - `get_user_store_ids()`: `WHERE sm.user_id = auth.uid()` 필터 사용
   - `is_user_store_member()`: `WHERE user_id = auth.uid()` 필터 사용
   - 모든 함수가 `auth.uid()` 기반 필터링으로 사용자 격리 보장

3. **추가 보안:**
   - RLS 정책이 `user_id = auth.uid()` 조건을 포함하면
   - 함수 내부 쿼리도 RLS 정책에 의해 추가로 필터링됨
   - 이중 보안 레이어 제공

### 원칙 3: 정책 적용 순서
1. ✅ **정책 작성** (아직 ENABLE 안 함)
2. ✅ **테스트 쿼리 준비**
3. ✅ **정책 적용** (ENABLE)
4. ✅ **기존 앱 동작 확인**
5. ✅ **문제 없으면 다음 단계**

---

## 🎯 Step 2 대상 테이블

### 1단계: 기본 테이블 (우선순위 1)

#### 1-1. store_members 테이블
- **목적**: 사용자-매장 멤버십 관리
- **RLS 정책**: 자신이 멤버인 매장 정보만 조회 가능
- **정책 이름**: `store_members_select_own_memberships`

#### 1-2. stores 테이블
- **목적**: 매장 정보 관리
- **RLS 정책**: 자신이 멤버인 매장만 조회 가능
- **정책 이름**: `stores_select_own_stores`

#### 1-3. user_profiles 테이블
- **목적**: 사용자 프로필 관리
- **RLS 정책**: 본인 프로필만 조회/수정 가능
- **정책 이름**: `user_profiles_select_own_profile`, `user_profiles_update_own_profile`

### 2단계: 핵심 운영 테이블 (우선순위 2)

#### 2-1. daily_close 테이블
- **목적**: 일일 마감 데이터 (가장 중요한 운영 데이터)
- **RLS 정책**: 자신이 멤버인 매장의 마감 데이터만 조회 가능
- **정책 이름**: `daily_close_select_own_store`

#### 2-2. (선택) daily_sales_items 테이블
- **목적**: 일일 판매량 데이터
- **RLS 정책**: 자신이 멤버인 매장의 판매량만 조회 가능
- **정책 이름**: `daily_sales_items_select_own_store`

---

## 📝 RLS 정책 초안

### 1단계 정책 초안

#### 1-1. store_members 테이블

```sql
-- 읽기 정책: 자신이 멤버인 매장 정보만 조회
CREATE POLICY "store_members_select_own_memberships"
    ON store_members FOR SELECT
    USING (user_id = auth.uid());

-- 쓰기 정책: 자신의 멤버십만 생성 (매장 생성 시 owner 자동 등록용)
CREATE POLICY "store_members_insert_own_membership"
    ON store_members FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- 수정 정책: 자신의 멤버십만 수정 (role 변경 등)
CREATE POLICY "store_members_update_own_membership"
    ON store_members FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());
```

**설명:**
- SELECT: 자신이 멤버인 매장 정보만 조회
- INSERT: 자신의 멤버십만 생성 (매장 생성 시 owner 자동 등록)
- UPDATE: 자신의 멤버십만 수정 (role 변경 등)
- DELETE: 제외 (매장 삭제 시 CASCADE로 자동 삭제)

#### 1-2. stores 테이블

**⚠️ 기존 정책 업데이트 필요:**
- 기존 정책: "Users can view their own store" (레거시 `get_user_store_id()` 사용)
- 새 정책으로 교체 필요

```sql
-- 기존 정책 삭제
DROP POLICY IF EXISTS "Users can view their own store" ON stores;

-- 읽기 정책: 자신이 멤버인 매장만 조회 (store_members 기반)
CREATE POLICY "stores_select_own_stores"
    ON stores FOR SELECT
    USING (
        id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
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
        id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid() 
            AND role = 'owner'
        )
    )
    WITH CHECK (
        id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid() 
            AND role = 'owner'
        )
    );
```

**설명:**
- SELECT: 자신이 멤버인 매장만 조회 (store_members 기반)
- INSERT: 매장 생성 가능 (created_by 자동 설정)
- UPDATE: owner만 매장 정보 수정 가능
- DELETE: 제외 (매장 삭제는 별도 프로세스 필요)

#### 1-3. user_profiles 테이블

**⚠️ 기존 정책 확인:**
- 기존 정책: "Users can view their own profile" (이미 존재)
- INSERT/UPDATE 정책 추가 필요

```sql
-- 읽기 정책: 본인 프로필만 조회 (기존 정책 유지 또는 업데이트)
-- 기존 정책이 있으면 그대로 사용 가능
-- DROP POLICY IF EXISTS "Users can view their own profile" ON user_profiles;  -- 필요시만

CREATE POLICY IF NOT EXISTS "user_profiles_select_own_profile"
    ON user_profiles FOR SELECT
    USING (id = auth.uid());

-- 쓰기 정책: 본인 프로필 생성 가능 (회원가입 시)
CREATE POLICY "user_profiles_insert_own_profile"
    ON user_profiles FOR INSERT
    WITH CHECK (id = auth.uid());

-- 수정 정책: 본인 프로필만 수정 가능
CREATE POLICY "user_profiles_update_own_profile"
    ON user_profiles FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());
```

**설명:**
- SELECT: 본인 프로필만 조회
- INSERT: 본인 프로필 생성 가능 (회원가입 시)
- UPDATE: 본인 프로필만 수정 가능 (default_store_id, onboarding_mode 등)
- DELETE: 제외 (auth.users 삭제 시 CASCADE로 자동 삭제)

### 2단계 정책 초안

#### 2-1. daily_close 테이블

```sql
-- 읽기 정책: 자신이 멤버인 매장의 마감 데이터만 조회
CREATE POLICY "daily_close_select_own_store"
    ON daily_close FOR SELECT
    USING (
        store_id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
    );

-- 쓰기 정책: 자신이 멤버인 매장의 마감 데이터만 생성
CREATE POLICY "daily_close_insert_own_store"
    ON daily_close FOR INSERT
    WITH CHECK (
        store_id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
    );

-- 수정 정책: 자신이 멤버인 매장의 마감 데이터만 수정
CREATE POLICY "daily_close_update_own_store"
    ON daily_close FOR UPDATE
    USING (
        store_id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        store_id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
    );
```

**설명:**
- SELECT/INSERT/UPDATE: 모두 store_members 기반으로 자신이 멤버인 매장만 접근
- DELETE: 제외 (마감 데이터는 삭제하지 않음)

#### 2-2. daily_sales_items 테이블 (선택)

```sql
-- 읽기 정책: 자신이 멤버인 매장의 판매량만 조회
CREATE POLICY "daily_sales_items_select_own_store"
    ON daily_sales_items FOR SELECT
    USING (
        store_id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
    );

-- 쓰기 정책: 자신이 멤버인 매장의 판매량만 생성
CREATE POLICY "daily_sales_items_insert_own_store"
    ON daily_sales_items FOR INSERT
    WITH CHECK (
        store_id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
    );

-- 수정 정책: 자신이 멤버인 매장의 판매량만 수정
CREATE POLICY "daily_sales_items_update_own_store"
    ON daily_sales_items FOR UPDATE
    USING (
        store_id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        store_id IN (
            SELECT store_id 
            FROM store_members 
            WHERE user_id = auth.uid()
        )
    );
```

---

## 🔍 정책 적용 전 테스트 쿼리

### 1단계 테스트 쿼리

#### store_members 테이블
```sql
-- 테스트 1: 자신의 멤버십 조회 (성공해야 함)
SELECT * FROM store_members WHERE user_id = auth.uid();

-- 테스트 2: 다른 사용자의 멤버십 조회 시도 (실패해야 함)
-- (다른 사용자 ID로 테스트 필요)
```

#### stores 테이블
```sql
-- 테스트 1: 자신이 멤버인 매장 조회 (성공해야 함)
SELECT s.* 
FROM stores s
WHERE s.id IN (
    SELECT store_id 
    FROM store_members 
    WHERE user_id = auth.uid()
);

-- 테스트 2: 다른 사용자의 매장 조회 시도 (실패해야 함)
```

#### user_profiles 테이블
```sql
-- 테스트 1: 본인 프로필 조회 (성공해야 함)
SELECT * FROM user_profiles WHERE id = auth.uid();

-- 테스트 2: 다른 사용자의 프로필 조회 시도 (실패해야 함)
```

### 2단계 테스트 쿼리

#### daily_close 테이블
```sql
-- 테스트 1: 자신이 멤버인 매장의 마감 데이터 조회 (성공해야 함)
SELECT * 
FROM daily_close 
WHERE store_id IN (
    SELECT store_id 
    FROM store_members 
    WHERE user_id = auth.uid()
);

-- 테스트 2: 다른 사용자의 매장 마감 데이터 조회 시도 (실패해야 함)
```

---

## 📊 적용 순서

### Step 2-A: 1단계 정책 작성 및 테스트
1. ✅ `store_members` 정책 작성 (아직 ENABLE 안 함)
2. ✅ `stores` 정책 작성 (아직 ENABLE 안 함)
3. ✅ `user_profiles` 정책 작성 (아직 ENABLE 안 함)
4. ✅ 테스트 쿼리 준비
5. ✅ 정책 적용 (ENABLE RLS)
6. ✅ 테스트 쿼리 실행 및 검증
7. ✅ 기존 앱 동작 확인

### Step 2-B: 2단계 정책 작성 및 테스트 (1단계 완료 후)
1. ✅ `daily_close` 정책 작성 (아직 ENABLE 안 함)
2. ✅ (선택) `daily_sales_items` 정책 작성
3. ✅ 테스트 쿼리 준비
4. ✅ 정책 적용 (ENABLE RLS)
5. ✅ 테스트 쿼리 실행 및 검증
6. ✅ 기존 앱 동작 확인

---

## ⚠️ 주의사항

### 기존 RLS 정책과의 충돌
- 현재 `schema.sql`에 이미 일부 RLS 정책이 존재함:
  - `stores`: "Users can view their own store" (레거시 `get_user_store_id()` 사용)
  - `user_profiles`: "Users can view their own profile" (이미 존재)
  - 다른 테이블들도 이미 RLS 활성화 및 정책 존재
- **기존 정책 업데이트 필요:**
  - `stores` 정책: `get_user_store_id()` → `store_members` 기반으로 변경
  - `user_profiles` 정책: INSERT/UPDATE 정책 추가 필요
  - `store_members`: 신규 테이블이므로 정책 생성 필요

### Helper 함수와의 호환성
- `get_user_store_id()` 함수는 `store_members` 기반으로 동작
- RLS 정책이 적용되어도 함수 내부의 `auth.uid()` 필터로 안전
- 함수 테스트 필요

### 성능 고려사항
- `store_members` 서브쿼리는 인덱스 활용으로 최적화됨
- 대량 데이터 환경에서 성능 테스트 필요

---

## 📋 다음 단계

1. ✅ Step 2-A SQL 작성 (1단계 정책)
2. ✅ Step 2-A 테스트 쿼리 작성
3. ✅ Step 2-A 적용 및 검증
4. ✅ Step 2-B 진행 (1단계 완료 후)

---

## 🔄 롤백 계획

정책 적용 후 문제 발생 시:
```sql
-- RLS 비활성화 (임시)
ALTER TABLE store_members DISABLE ROW LEVEL SECURITY;
ALTER TABLE stores DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;

-- 정책 삭제
DROP POLICY IF EXISTS "store_members_select_own_memberships" ON store_members;
DROP POLICY IF EXISTS "stores_select_own_stores" ON stores;
DROP POLICY IF EXISTS "user_profiles_select_own_profile" ON user_profiles;
```

---

## 📌 요약

| 단계 | 테이블 | 정책 수 | 우선순위 |
|------|--------|---------|----------|
| **1단계** | store_members, stores, user_profiles | 7개 | 높음 |
| **2단계** | daily_close, daily_sales_items | 6개 | 중간 |

**총 정책 수**: 13개 (1단계 7개 + 2단계 6개)

**적용 방식**: 단계별로 정책 작성 → 테스트 → 적용 → 검증
