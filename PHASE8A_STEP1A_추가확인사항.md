# Phase 8-A Step 1-A: 추가 확인사항 검토

## ✅ 1. store_members 테이블 FK/UNIQUE 제약 확인

### 현재 SQL 확인:
```sql
CREATE TABLE IF NOT EXISTS store_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'manager', 'staff')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(store_id, user_id)
);
```

### ✅ 확인 결과:
- ✅ `(store_id, user_id) UNIQUE` 제약 포함됨
- ✅ `store_id` FK → `stores(id)` 정상
- ✅ `user_id` FK → `auth.users(id)` 정상
- ✅ `ON DELETE CASCADE` 설정 (매장/사용자 삭제 시 자동 정리)

**결론: 제약 조건이 올바르게 설정되어 있습니다. ✅**

---

## ✅ 2. user_profiles.onboarding_mode CHECK 제약과 기본값 확인

### 현재 SQL 확인:
```sql
ALTER TABLE user_profiles 
ADD COLUMN onboarding_mode TEXT NOT NULL DEFAULT 'coach' 
CHECK (onboarding_mode IN ('coach', 'fast'));
```

### ✅ 확인 결과:
- ✅ 기본값: `DEFAULT 'coach'` 설정됨
- ✅ CHECK 제약: `CHECK (onboarding_mode IN ('coach', 'fast'))` 설정됨
- ✅ NOT NULL 제약 포함

**주의사항:**
- 기존 row에 대해 `NOT NULL DEFAULT 'coach'`가 자동 적용됨
- 기존 데이터는 모두 'coach'로 설정됨 (안전)

**결론: 제약 조건과 기본값이 올바르게 설정되어 있습니다. ✅**

---

## ✅ 3. 마이그레이션 SQL 중복 실행 안전성 확인

### 3-1. user_profiles.store_id → store_members 마이그레이션

#### 현재 SQL:
```sql
INSERT INTO store_members (store_id, user_id, role, created_at)
SELECT 
    up.store_id,
    up.id AS user_id,
    COALESCE(up.role, 'manager') AS role,
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
```

#### ✅ 안전성 확인:
- ✅ `NOT EXISTS` 조건으로 중복 체크
- ✅ `ON CONFLICT (store_id, user_id) DO NOTHING` 추가 보호
- ✅ 중복 실행 시 기존 데이터 유지 (안전)

**결론: 중복 실행에 안전합니다. ✅**

### 3-2. default_store_id 설정 마이그레이션

#### 현재 SQL:
```sql
UPDATE user_profiles up
SET default_store_id = up.store_id
WHERE up.store_id IS NOT NULL
AND up.default_store_id IS NULL;
```

#### ✅ 안전성 확인:
- ✅ `WHERE up.default_store_id IS NULL` 조건으로 이미 값이 있으면 업데이트 안 함
- ✅ 중복 실행 시 기존 값 보존 (안전)

**결론: 중복 실행에 안전합니다. ✅**

---

## ✅ 4. Helper 함수 SECURITY DEFINER 및 RLS 관련 확인

### 4-1. get_user_store_id() 함수

#### 현재 SQL:
```sql
CREATE OR REPLACE FUNCTION get_user_store_id()
RETURNS UUID AS $$
DECLARE
    result_store_id UUID;
BEGIN
    -- store_members 조회
    SELECT sm.store_id INTO result_store_id
    FROM store_members sm
    WHERE sm.user_id = auth.uid()
    ...
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### ✅ 확인 결과:
- ✅ `SECURITY DEFINER` 사용됨
- ✅ `auth.uid()` 사용으로 현재 로그인 사용자 확인
- ⚠️ **RLS 우회 가능성**: `SECURITY DEFINER`는 함수 소유자 권한으로 실행

#### 🔍 RLS 동작 분석:
1. **함수 내부 쿼리:**
   - `FROM store_members sm WHERE sm.user_id = auth.uid()`
   - `FROM user_profiles WHERE id = auth.uid()`
   - 모두 `auth.uid()` 기반 필터링

2. **RLS 정책과의 관계:**
   - `store_members` 테이블에 RLS가 활성화되어 있으면
   - 함수 내부에서도 RLS가 적용됨
   - 하지만 `SECURITY DEFINER`는 함수 소유자 권한으로 실행되므로
   - **RLS 정책이 올바르게 설정되어야 함**

#### ✅ 해결 방안:
- `store_members` 테이블에 RLS 정책 추가 필요 (Step 2에서 수행)
- RLS 정책 예시:
  ```sql
  CREATE POLICY "Users can view their own memberships"
      ON store_members FOR SELECT
      USING (user_id = auth.uid());
  ```

**결론: 함수는 올바르게 작성되었으나, RLS 정책이 필요합니다. Step 2에서 RLS 정책을 추가해야 합니다. ⚠️**

### 4-2. get_user_store_ids() 함수

#### 현재 SQL:
```sql
CREATE OR REPLACE FUNCTION get_user_store_ids()
RETURNS TABLE(store_id UUID) AS $$
BEGIN
    RETURN QUERY
    SELECT sm.store_id
    FROM store_members sm
    WHERE sm.user_id = auth.uid();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

#### ✅ 확인 결과:
- ✅ `SECURITY DEFINER` 사용됨
- ✅ `auth.uid()` 기반 필터링
- ⚠️ RLS 정책 필요 (위와 동일)

**결론: 함수는 올바르게 작성되었으나, RLS 정책이 필요합니다. ⚠️**

### 4-3. is_user_store_member() 함수

#### 현재 SQL:
```sql
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
```

#### ✅ 확인 결과:
- ✅ `SECURITY DEFINER` 사용됨
- ✅ `auth.uid()` 기반 필터링
- ⚠️ RLS 정책 필요 (위와 동일)

**결론: 함수는 올바르게 작성되었으나, RLS 정책이 필요합니다. ⚠️**

---

## 📋 요약

| 항목 | 상태 | 설명 |
|------|------|------|
| **1. store_members FK/UNIQUE** | ✅ 완료 | 제약 조건 올바름 |
| **2. onboarding_mode 제약** | ✅ 완료 | CHECK 및 기본값 올바름 |
| **3. 마이그레이션 중복 실행** | ✅ 안전 | NOT EXISTS + ON CONFLICT 사용 |
| **4. Helper 함수 SECURITY** | ⚠️ 주의 | SECURITY DEFINER 사용, RLS 정책 필요 |

### ⚠️ Step 2에서 반드시 수행할 사항:
- `store_members` 테이블에 RLS 정책 추가
- Helper 함수들이 RLS를 우회하지 않도록 정책 설정

---

## 🔄 수정 권장사항 (선택)

현재 SQL은 안전하지만, 더 명확하게 하기 위해:

1. **마이그레이션 로직 개선 (선택):**
   - 현재도 안전하지만, 더 명확한 로깅 추가 가능

2. **RLS 정책 미리 준비 (Step 2용):**
   - `store_members` 테이블 RLS 정책 SQL 준비

**현재 SQL은 그대로 사용 가능하며, Step 2에서 RLS 정책을 추가하면 완벽합니다. ✅**
