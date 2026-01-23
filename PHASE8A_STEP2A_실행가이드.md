# Phase 8-A Step 2-A: RLS 정책 적용 실행 가이드

## 📋 실행 순서

### 1단계: SQL 파일 실행
1. Supabase 대시보드 > SQL Editor 열기
2. `sql/phase8a_step2a_rls_policies.sql` 파일 내용 복사
3. SQL Editor에 붙여넣기
4. **실행** (RLS 정책 생성 및 활성화)

### 2단계: 검증 쿼리 실행
1. Supabase 대시보드 > SQL Editor에서 새 쿼리 생성
2. `sql/phase8a_step2a_검증.sql` 파일 내용 복사
3. SQL Editor에 붙여넣기
4. **실행** (모든 검증 항목 확인)

### 3단계: 결과 확인
- 모든 검증 항목이 ✅인지 확인
- ❌ 또는 ⚠️가 있으면 문제 해결 후 재검증

### 4단계: 기존 앱 동작 확인
- 로컬에서 앱 실행
- 로그인 후 홈 화면 접근 확인
- 매장 정보 조회 확인
- 문제 없으면 Step 2-B 진행

---

## ⚠️ 주의사항

### RLS 활성화 상태
- **ENABLE RLS**: ✅ 적용됨
- **FORCE RLS**: ❌ 보류 (Step 2-B에서 검토)

### 적용 범위
- **1단계**: `store_members`, `stores`, `user_profiles` 3개 테이블만
- **daily_close**: Step 2-C에서 별도 진행 (앱 깨짐 방지)

### 기존 정책 처리
- 기존 정책이 있으면 이름 충돌 없이 신규 정책 추가
- 레거시 정책(`get_user_store_id()` 사용)은 삭제 후 신규 정책 생성

---

## 🔍 검증 항목

### 검증 1: store_members 테이블
- ✅ 자신의 멤버십 조회 가능
- ✅ 타 사용자의 멤버십 조회 불가
- ✅ 타 사용자 store_id로 INSERT 시도 시 실패

### 검증 2: stores 테이블
- ✅ 자신이 멤버인 매장 조회 가능
- ✅ 타 사용자의 매장 조회 불가
- ✅ 타 사용자 store로 UPDATE 시도 시 실패

### 검증 3: user_profiles 테이블
- ✅ 본인 프로필 조회 가능
- ✅ 타 사용자의 프로필 조회 불가

### 검증 4: Helper 함수
- ✅ `get_user_store_id()`가 자신의 store만 반환
- ✅ `get_user_store_ids()`가 자신의 stores만 반환
- ✅ `is_user_store_member()`가 올바르게 동작

### 검증 5: RLS 정책 존재
- ✅ 각 테이블에 정책이 존재하는지 확인

### 검증 6: RLS 활성화 상태
- ✅ 각 테이블에 RLS가 활성화되어 있는지 확인

---

## 🔄 롤백 방법

문제 발생 시:

```sql
-- RLS 비활성화 (임시)
ALTER TABLE store_members DISABLE ROW LEVEL SECURITY;
ALTER TABLE stores DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles DISABLE ROW LEVEL SECURITY;

-- 정책 삭제
DROP POLICY IF EXISTS "store_members_select_own_memberships" ON store_members;
DROP POLICY IF EXISTS "store_members_insert_own_membership" ON store_members;
DROP POLICY IF EXISTS "store_members_update_own_membership" ON store_members;

DROP POLICY IF EXISTS "stores_select_own_stores" ON stores;
DROP POLICY IF EXISTS "stores_insert_own_store" ON stores;
DROP POLICY IF EXISTS "stores_update_own_store" ON stores;

DROP POLICY IF EXISTS "user_profiles_select_own_profile" ON user_profiles;
DROP POLICY IF EXISTS "user_profiles_insert_own_profile" ON user_profiles;
DROP POLICY IF EXISTS "user_profiles_update_own_profile" ON user_profiles;
```

---

## 📌 다음 단계

Step 2-A 완료 후:
1. ✅ 검증 쿼리 모두 통과
2. ✅ 기존 앱 정상 동작 확인
3. ⏭️ Step 2-B 진행 (필요시)
